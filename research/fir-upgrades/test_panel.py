"""Contract and arithmetic checks for the frozen Task 4 panel."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import panel

EXPECTED_FILTERS = {
    'native_lp1800': ('4cc95f66dcae4fa848d8b5870ecca26a5be6101c91fc7e28bd52e404419c4118', 50001, None),
    'wide_lp2800': ('6293e26668672b816f2a5f22d4f0ce09ef7af8bc5d01cb0d433cff432615f573', 100002, (4, 5)),
    'wide_lp4600': ('900cf584be9d2b3597a63e5acd42e14594bd768607ac05e5c705a71f405b310b', 110003, (3, 4)),
}


def test_frozen_recipe_hash_l1_and_legal_cut_policy():
    data = panel.make_design()
    assert list(data['filters']) == list(EXPECTED_FILTERS)
    for name, (digest, l1, cuts) in EXPECTED_FILTERS.items():
        row = data['filters'][name]
        h = row['coefficients']
        assert hashlib.sha256(panel.coefficient_bytes(h)).hexdigest() == digest
        assert row['coefficient_l1'] == l1
        assert len(h) == 48 and h != h[::-1] and all(-32768 <= c <= 32767 for c in h)
        assert row['cuts'] == ([] if cuts is None else list(cuts))
        if cuts:
            assert row['cut_groups']['first'] == [[0, cuts[0]], [cuts[0], 48]]
            assert row['cut_groups']['balanced'] == [[0, cuts[1]], [cuts[1], 48]]
            assert row['group_abs_bounds'] == {str(cuts[0]): row['group_abs_bounds'][str(cuts[0])], str(cuts[1]): row['group_abs_bounds'][str(cuts[1])]}
            for cut, bounds in zip(cuts, row['group_abs_bounds'].values()):
                assert bounds == [32768*sum(abs(c) for c in h[:cut]), 32768*sum(abs(c) for c in h[cut:])]
            assert len(row['group_reduction_prefix_intervals']['first']) == 2
        assert len(row['full_prefix_intervals']) == 48


def test_exact_full_sum_intervals_and_extremal_witnesses():
    design = panel.make_design()
    expected = {
        'native_lp1800': [-1638421124, 1638394411],
        'wide_lp2800': [-3276839180, 3276791890],
        'wide_lp4600': [-3604545833, 3604500772],
    }
    for name, interval in expected.items():
        row = design['filters'][name]
        assert row['full_sum_interval'] == interval
        assert row['upper_witness_sum'] == interval[1]
        assert row['lower_witness_sum'] == interval[0]
        assert sum(c*x for c,x in zip(row['coefficients'], row['upper_witness_taps'][::-1])) == interval[1]
        assert sum(c*x for c,x in zip(row['coefficients'], row['lower_witness_taps'][::-1])) == interval[0]
        if name != 'native_lp1800':
            assert interval[1] > 2**31 - 1 and interval[0] < -(2**31)


def test_input_stream_identity_and_case_accounting():
    data = panel.make_inputs()
    assert data['full'][:16] == [-32768,32767,0,-1,1,-32767,32766,0,-3675,-21672,280,-30481,-17793,-19545,13532,-30280]
    assert hashlib.sha256(panel.coefficient_bytes(data['full'])).hexdigest() == '45f756624d8bb824a19352860fff89648c26971c961433f5ee1bcc8dab6fefc8'
    assert hashlib.sha256(panel.coefficient_bytes(data['adc'])).hexdigest() == '4ee975455373f3b8c4af42282b82d542e8e2810b4f46cf253a0f13ce4a78095e'
    rows = panel.case_rows()
    assert len(rows) == 288
    keys = [(r['filter'], r['variant'], r['compiler'], r['block'], r['stimulus'], r['regime']) for r in rows]
    assert len(set(keys)) == 288
    assert {(r['warmup_samples'], r['measured_samples'], r['total_samples']) for r in rows} == {(0,257,257),(64,1025,1089)}


def test_direct_generator_order_widening_and_argument_validation():
    h = panel.make_design()['filters']['wide_lp2800']['coefficients']
    header, source = panel.generate_kernel(h, 'cert_direct_first', 64, [(0,4),(4,48)])
    assert 'int32_t partial0=0' in source
    assert 'int64_t sum=(int64_t)partial0+(int64_t)partial1' in source
    assert source.index('history[j+47]') < source.index('history[j+46]')
    assert source.count('quant(sum)') == 1
    assert 'if(b>' not in source
    with pytest.raises(ValueError):
        panel.generate_kernel(h, 'cert_direct_first', 64, [(0,4),(5,48)])
    with pytest.raises(ValueError):
        panel.generate_kernel(h, 'cert_direct_first', 64, [(0,48)])
    # A wide control may use one whole group even when it exceeds int32.
    panel.generate_kernel(h, 'wide_direct64', 64, [(0,48)])


def test_prepare_emits_reusable_literal_sources_and_pending_admission(tmp_path):
    result = panel.prepare_panel(tmp_path)
    again = panel.prepare_panel(tmp_path)
    assert result == again
    assert result['performance_runs'] == 0
    assert result['fast_cmsis_block64_admission'] == 'pending unresolved pointer-object aliasing'
    assert len([p for p in (tmp_path / 'vendor').glob('*.txt') if not p.name.endswith('.stderr.txt')]) == 3
    assert (tmp_path / 'panel-protocol.sha256').is_file()
    manifest = json.loads((tmp_path / 'sources-manifest.json').read_text())
    assert len(manifest['sources']) == 3 * 6 * 2


def test_prepare_rejects_changed_saved_graph_stderr(tmp_path):
    panel.prepare_panel(tmp_path)
    err = tmp_path / 'vendor' / 'wide_lp2800.stderr.txt'
    err.write_bytes(b'tampered notice\n')
    with pytest.raises(ValueError):
        panel.prepare_panel(tmp_path)


def test_single_quantizer_boundaries_are_exact():
    cases = {-1073741825:-32768, -1073741824:-32768, -1073741823:-32768,
             -32769:-2, -32768:-1, -32767:-1, -1:-1, 0:0, 1:0,
             32767:0, 32768:1, 1073741823:32767,
             1073741824:32767, 1073741825:32767}
    for total, expected in cases.items():
        assert panel._quantize(total) == expected


def test_aligned_state_guard_allocation_stays_inside_backing_buffer():
    raw, address = panel._aligned_state_buffer(257)
    base = panel.ctypes.addressof(raw)
    assert address % 16 == 0
    assert base <= address - 8
    assert address + 257 + 8 <= base + panel.ctypes.sizeof(raw)


def test_generator_rejects_noninteger_coefficients_and_group_cuts():
    h = panel.make_design()['filters']['wide_lp2800']['coefficients']
    bad = list(h)
    bad[0] = 1.5
    with pytest.raises(ValueError):
        panel.generate_kernel(bad, 'cert_direct_first', 64, [(0, 4), (4, 48)])
    with pytest.raises(ValueError):
        panel.generate_kernel(h, 'cert_direct_first', 64, [(0, 4.5), (4.5, 48)])

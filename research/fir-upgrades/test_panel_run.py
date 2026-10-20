"""TDD checks for frozen Task 5 runner preparation and gate inventory."""
import json
from decimal import Decimal
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import panel_run
import panel_verify
import panel


def test_gate_stream_is_exact_fixed_194_sample_input():
    design = json.loads((HERE / 'panel-design.json').read_text())
    row = design['filters']['wide_lp2800']
    stream = panel_run.gate_stream(row)
    h = row['coefficients']
    upper = [32767 if c > 0 else -32768 if c < 0 else 0 for c in h][::-1]
    lower = [-32768 if c > 0 else 32767 if c < 0 else 0 for c in h][::-1]
    assert len(stream) == 194
    assert stream == [0] * 48 + upper + lower + [-32768, 32767, -1, 0, 1] * 10


def test_performance_fixture_renderer_matches_independent_body_template():
    protocol = panel_verify.load_frozen_protocol(HERE)
    case = next(c for c in protocol['cases'] if c['regime'] == 'post_startup' and
                c['block'] == 64 and c['stimulus'] == 'full')
    inputs = json.loads((HERE / 'panel-inputs.json').read_text())
    source = panel_run.fixture_source(case['block'], inputs['full'],
                                      case['warmup_samples'], case['total_samples'])
    assert panel_verify.audit_fixture_source(source, case, inputs['full'])['measured_offsets'] == [64, 1089]


def test_correctness_inventory_preserves_all_identities_and_pending_fast_exclusions():
    protocol = panel_verify.load_frozen_protocol(HERE)
    design = json.loads((HERE / 'panel-design.json').read_text())
    cases = panel_run.gate_cases(protocol, design)
    assert len(cases) == 72
    skipped = [c for c in cases if c['status'] == 'skipped']
    runnable = [c for c in cases if c['status'] == 'pending']
    assert len(skipped) == 2 and len(runnable) == 70
    assert all(c['filter'] == 'native_lp1800' and c['variant'] == 'cmsis32_unroll'
               and c['block'] == 64 for c in skipped)


def test_state_size_is_derived_from_frozen_probe_abi_not_row_value():
    cmsis = (HERE / 'sources/native_lp1800/cmsis64_unroll/b64/probe.h').read_text()
    direct = (HERE / 'sources/wide_lp2800/trans_const/b64/probe.h').read_text()
    short = (HERE / 'sources/native_lp1800/wide_direct64/b1/probe.h').read_text()
    assert panel_run.state_allocation_from_header(cmsis) == 236
    assert panel_run.state_allocation_from_header(direct) == 200
    assert panel_run.state_allocation_from_header(short) == 98


def test_protocol_change_stops_before_any_target_build(tmp_path):
    for name in ('panel-protocol.json', 'panel-design.json', 'panel-inputs.json'):
        (tmp_path / name).write_bytes((HERE / name).read_bytes())
    protocol = json.loads((tmp_path / 'panel-protocol.json').read_text())
    protocol['cases'].pop()
    (tmp_path / 'panel-protocol.json').write_text(json.dumps(protocol))
    with pytest.raises(ValueError, match='protocol digest'):
        panel_run.frozen(tmp_path)


def test_gate_identity_selector_only_resolves_declared_executable_identity():
    protocol = panel_verify.load_frozen_protocol(HERE)
    design = json.loads((HERE / 'panel-design.json').read_text())
    selected = panel_run.select_gate_identity(protocol, design,
        ('native_lp1800', 'cmsis32_unroll', 'gcc15', 1))
    assert selected['filter'] == 'native_lp1800'
    assert selected['variant'] == 'cmsis32_unroll'
    with pytest.raises(ValueError, match='pending'):
        panel_run.select_gate_identity(protocol, design,
            ('native_lp1800', 'cmsis32_unroll', 'gcc15', 64))
    with pytest.raises(ValueError, match='not in'):
        panel_run.select_gate_identity(protocol, design,
            ('wide_lp2800', 'cmsis32_unroll', 'gcc15', 1))


def test_performance_selector_accepts_first_two_and_rejects_unknown_identity():
    protocol = panel_verify.load_frozen_protocol(HERE)
    first_two = protocol['cases'][:2]
    for case in first_two:
        identity = tuple(case[k] for k in panel_run.CASE_KEYS)
        assert panel_run.select_performance_case(protocol, identity) == case
    bad = tuple(first_two[0][k] for k in panel_run.CASE_KEYS[:-1]) + ('no_such_regime',)
    with pytest.raises(ValueError, match='absent'):
        panel_run.select_performance_case(protocol, bad)


def test_performance_selector_accepts_all_declared_executable_cases_and_rejects_pending_fast():
    protocol = panel_verify.load_frozen_protocol(HERE)
    for case in protocol['cases']:
        identity = tuple(case[k] for k in panel_run.CASE_KEYS)
        pending = (case['filter'] == 'native_lp1800' and
                   case['variant'] == 'cmsis32_unroll' and case['block'] == 64)
        if pending:
            with pytest.raises(ValueError, match='pending'):
                panel_run.select_performance_case(protocol, identity)
        else:
            assert panel_run.select_performance_case(protocol, identity) == case


def test_performance_cost_serialization_is_exact_and_independent_audit_accepts_it(tmp_path):
    labels = ('Executed insns: 12\nRAM data reads: 3\nRAM writes: 4\n'
              'Flash data reads: 5\nFlash writes: 0\nTaken branches: 2\n'
              'Flash insn reads: 19\nBL insns: 1\n')
    rows = '\n'.join(f"{i}: {2 if i == 16 else 10 if i == 0 else 0}, [" +
                     ', '.join(str(2 if i == 16 and j == 13 else 0)
                               for j in range(16)) + ']' for i in range(64))
    markers = '\nGPIOC[0] raised at cycle 20\nGPIOC[0] cleared at cycle 70\n'
    stderr_text = labels + rows + markers
    raw = panel_verify.rederive_raw_events(stderr_text)
    fields = panel_run.serialize_cost_fields(raw, 1025)
    saved = tmp_path / 'firmware.stderr'
    saved.write_text(stderr_text)
    admitted = panel_verify.audit_serialized_cost({
        'artifact_paths': {'stderr': saved.name}, 'artifact_sha256': {
            'stderr': panel_verify.sha256_bytes(saved.read_bytes())},
        'measured_samples': 1025, 'events': raw, **fields}, tmp_path)
    assert admitted['cycles_per_output'] == panel_verify.derive_cost(raw, 1025)['cycles_per_output']
    assert fields['energy_weighted_integer'].isdigit()
    assert fields['energy_nj'] == str(panel_verify.derive_cost(raw, 1025)['energy_nj'])


def test_checkpoint_json_preserves_decimal_estimands_as_exact_strings():
    assert json.loads(panel_run.dump({'energy': Decimal('123.000001')})) == {
        'energy': '123.000001'}


def test_panel_cli_measure_subcommand_routes_to_task5_runner(monkeypatch):
    calls = []
    monkeypatch.setattr(panel_run, 'main', lambda argv: calls.append(argv))
    panel.main(['measure', 'correctness'])
    assert calls == [['correctness']]


def test_toolchain_identity_pins_compiler_and_cortex_m0_libgcc():
    identity = panel_run.compiler_identity('gcc10')
    assert identity['sha256'] == '702dfc4dd0b34ee43ecd164a6db6ada4b5583d8945b17bbea3ebe223db765480'
    assert identity['libgcc']['path'].endswith('/thumb/v6-m/nofp/libgcc.a')
    assert identity['libgcc']['sha256'] == '7d25476df0fb0cb0133911547da014e94bf610d7a1e975c4c64e76c23fdbe517'


def test_stack_admission_includes_tail_branch_and_helper_frames(tmp_path):
    su = tmp_path / 'firmware.su'
    su.write_text('fixture.c:1:1:main\t8\tstatic\n')
    disassembly = '''
00000000 <main>:
   0: b500 push {lr}
   2: b081 sub sp, #4
   4: f000 f802 bl 0000000c <helper>
   8: bd00 pop {pc}
0000000c <helper>:
   c: b510 push {r4, lr}
   e: b081 sub sp, #4
  10: e000 b 00000014 <tail>
00000014 <tail>:
  14: b500 push {lr}
  16: bd00 pop {pc}
00000018 <measured>:
  18: b570 push {r4, r5, r6, lr}
  1a: bd70 pop {r4, r5, r6, pc}
'''
    evidence = panel_run.stack_admission([su], disassembly, {'main': {'address': 0, 'size': 8}})
    assert evidence['maximum_live_stack_bytes'] == 20
    assert evidence['maximizing_chain'] == ['main', 'helper']


def test_stack_admission_ignores_internal_loop_branch_at_function_label(tmp_path):
    su = tmp_path / 'loop.su'
    su.write_text('fixture.c:1:1:main\t8\tstatic\n')
    disassembly = '''
00000000 <main>:
   0: b500 push {lr}
   2: e7fd b 00000000 <main>
   4: bd00 pop {pc}
00000008 <measured>:
   8: b570 push {r4, r5, r6, lr}
   a: bd70 pop {r4, r5, r6, pc}
'''
    evidence = panel_run.stack_admission([su], disassembly, {'main': {'address': 0, 'size': 8}})
    assert evidence['maximum_live_stack_bytes'] == 8


def test_stack_admission_ignores_compiler_outlined_same_symbol_body_call(tmp_path):
    su = tmp_path / 'outlined.su'
    su.write_text('fixture.c:1:1:main\t8\tstatic\n')
    disassembly = '''
00000000 <main>:
   0: b500 push {lr}
   2: f000 f800 bl 00000006 <main+0x6>
   6: 4770 bx lr
00000008 <measured>:
   8: b570 push {r4, r5, r6, lr}
   a: bd70 pop {r4, r5, r6, pc}
'''
    evidence = panel_run.stack_admission([su], disassembly, {'main': {'address': 0, 'size': 8}})
    assert evidence['maximum_live_stack_bytes'] == 8
    assert evidence['intra_function_edges'] == [
        {'from': 'main', 'to': 'main+0x6', 'kind': 'outlined-intra-function-call'}]


def test_stack_admission_does_not_ignore_same_symbol_entry_call(tmp_path):
    su = tmp_path / 'recursive.su'
    su.write_text('fixture.c:1:1:main\t8\tstatic\n')
    disassembly = '''
00000000 <main>:
   0: b500 push {lr}
   2: f7ff fffe bl 00000000 <main>
00000008 <measured>:
   8: b570 push {r4, r5, r6, lr}
   a: bd70 pop {r4, r5, r6, pc}
'''
    with pytest.raises(ValueError, match='recursive stack'):
        panel_run.stack_admission([su], disassembly, {'main': {'address': 0, 'size': 8}})


def test_allocated_section_ranges_reject_orphans_and_flash_overflow():
    sections = [
        {'name': '.vectors', 'address': 0x08000000, 'size': 8, 'end': 0x08000008},
        {'name': '.text', 'address': 0x08000008, 'size': 64, 'end': 0x08000048},
        {'name': '.bss', 'address': 0x20000000, 'size': 100, 'end': 0x20000064},
    ]
    assert panel_run.validate_memory_ranges(sections)['ram_end'] == 0x20000064
    orphan = sections + [{'name': '.orphan', 'address': 0x20003000, 'size': 4, 'end': 0x20003004}]
    with pytest.raises(ValueError, match='allocated section'):
        panel_run.validate_memory_ranges(orphan)
    overflow = sections + [{'name': '.orphan', 'address': 0x0800fff0,
                            'size': 32, 'end': 0x08010010}]
    with pytest.raises(ValueError, match='allocated section'):
        panel_run.validate_memory_ranges(overflow)

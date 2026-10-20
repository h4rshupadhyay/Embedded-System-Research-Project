"""RED/GREEN checks for independent Task 5 evidence admission."""
import json
import hashlib
from decimal import Decimal
from pathlib import Path
import re
import shutil
import sys

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import panel_verify


def simulator_stderr(instructions=10, mul=2, marker_pair=True):
    labels = {
        'Executed insns': instructions, 'RAM data reads': 3, 'RAM writes': 4,
        'Flash data reads': 5, 'Flash writes': 0, 'Taken branches': 2,
        'Flash insn reads': instructions + 7, 'BL insns': 1,
    }
    rows = []
    for i in range(64):
        bins = [0] * 16
        total = 0
        if i == 16:
            bins[13] = mul
            total = mul
        elif i == 0:
            total = instructions - mul
        rows.append(f"{i}: {total}, [" + ', '.join(map(str, bins)) + ']')
    result = '\n'.join(f'{k}: {v}' for k, v in labels.items()) + '\n' + '\n'.join(rows)
    if marker_pair:
        result += '\nGPIOC[0] raised at cycle 20\nGPIOC[0] cleared at cycle 70\n'
    return result


def test_raw_events_are_strict_and_correction_is_applied_once():
    events = panel_verify.rederive_raw_events(simulator_stderr())
    assert events['instructions'] == 9
    assert events['flash_fetches'] == 16
    assert events['raw_tick_delta'] == 48
    assert events['mul'] == 2
    with pytest.raises(ValueError, match='duplicate'):
        panel_verify.rederive_raw_events(simulator_stderr() + '\nExecuted insns: 10\n')
    with pytest.raises(ValueError, match='markers'):
        panel_verify.rederive_raw_events(simulator_stderr(marker_pair=False))


def test_exact_decimal_energy_and_costs_are_rederived_from_raw_counts():
    events = panel_verify.rederive_raw_events(simulator_stderr())
    derived = panel_verify.derive_cost(events, 257)
    assert derived['arm_zero_ws_cycles'] == 9 + 3 + 4 + 5 + 4 + 1
    assert derived['energy_weighted_integer'] == panel_verify.weighted_integer(events)
    assert derived['energy_nj_per_output'] == derived['energy_nj'] / 257
    with pytest.raises(ValueError, match='positive'):
        panel_verify.derive_cost(events, 0)


def test_quantizer_clamp_paths_use_exact_sums_and_measured_absolute_range():
    h = [40000]
    x = [32767, -32768, 0]
    assert panel_verify.quantizer_clamp_paths(h, x, 1, 3) == {
        'positive': 0, 'negative': 1, 'total': 1,
        'predicates': {'positive': 'S>=1073741824', 'negative': 'S<=-1073741824'},
        'range': [1, 3]}


def test_frozen_identity_inventory_rejects_duplicate_and_missing_rows(tmp_path):
    protocol = json.loads((HERE / 'panel-protocol.json').read_text())
    rows = protocol['cases']
    assert len(panel_verify.validate_identity_inventory(rows, protocol)) == 288
    with pytest.raises(ValueError, match='duplicate'):
        panel_verify.validate_identity_inventory(rows + [dict(rows[0])], protocol)
    with pytest.raises(ValueError, match='inventory'):
        panel_verify.validate_identity_inventory(rows[:-1], protocol)


def test_frozen_identity_inventory_accepts_nested_campaign_rows_and_exact_unavailable_status():
    protocol = json.loads((HERE / 'panel-protocol.json').read_text())
    rows = [{'identity': {k: case[k] for k in panel_verify.CASE_FIELDS},
             'status': 'admitted'} for case in protocol['cases']]
    assert len(panel_verify.validate_identity_inventory(rows, protocol)) == 288


def test_exact_summary_ties_reversal_witness_and_incomplete_denominator():
    protocol = {'variants_by_filter': {
        'wide_lp2800': ['wide_direct64', 'cert_direct_first', 'trans_const',
                        'trans_hcub_demand', 'cmsis64_unroll', 'cert_direct_balanced'],
    }, 'compilers': ['gcc10', 'gcc15'], 'cases': []}
    costs = {'wide_direct64': '100', 'cert_direct_first': '80', 'trans_const': '100',
             'trans_hcub_demand': '85', 'cmsis64_unroll': '90', 'cert_direct_balanced': '80'}
    rows = []
    for variant, value in costs.items():
        identity = ['wide_lp2800', variant, 'gcc10', 1, 'adc', 'startup']
        protocol['cases'].append(dict(zip(panel_verify.CASE_FIELDS, identity)))
        rows.append({'identity': identity, 'cost': {'energy_nj_per_output': Decimal(value)},
                     'execution': {'quantizer_clamp_paths': {'positive': 0, 'negative': 0,
                         'total': 0, 'range': [0, 257]},
                         'memory': {'ram_end': 0x20000100, 'flash_end': 0x08000100},
                         'stack': {'maximum_live_stack_bytes': 100}}, 'mnemonics': []})
    audit = {'audited': rows, 'identity_count': 288, 'admitted_count': 280,
             'unavailable_count': 8, 'failed_count': 0,
             'unavailable': []}
    summary = panel_verify.summarize_campaign(audit, protocol)
    cell = summary['fixed_compiler_cells'][0]
    assert cell['D_old']['energy_nj_per_output'] == '90'
    assert cell['D_new']['energy_nj_per_output'] == '80'
    assert cell['D_new']['minimizers'] == ['cert_direct_first', 'cert_direct_balanced']
    assert cell['primary_reversal_witness'] is True
    assert summary['assessment'] == 'incomplete'
    assert summary['primary_extension']['wide_required_fixed_compiler_witnesses'][0]['E_Hcub'] == '85'
    selectable = summary['compiler_selectable_cells'][0]
    assert selectable['D_old']['status'] == 'unknown'
    assert selectable['per_form']['wide_direct64']['missing_compilers'] == ['gcc15']


def test_mutually_consistent_serialized_cost_rewrite_does_not_override_raw(tmp_path):
    stderr = tmp_path / 'stderr.txt'
    stderr.write_text(simulator_stderr())
    record = {'artifact_paths': {'stderr': 'stderr.txt'}, 'measured_samples': 257,
              'instructions': 100, 'arm_zero_ws_cycles': 999,
              'energy_weighted_integer': '999', 'energy_nj': '999'}
    with pytest.raises(ValueError, match='raw'):
        panel_verify.audit_serialized_cost(record, tmp_path)


def test_independent_fixture_grammar_rejects_changed_input_or_roi_reset():
    case = {'block': 1, 'warmup_samples': 0, 'total_samples': 1}
    source = panel_verify._fixture_template(1, [0], 0, 1)
    panel_verify.audit_fixture_source(source, case, [0])
    with pytest.raises(ValueError, match='audited'):
        panel_verify.audit_fixture_source(source.replace('input_data[TOTAL]={0}',
            'input_data[TOTAL]={1}'), case, [0])

    warmed = {'block': 64, 'warmup_samples': 64, 'total_samples': 1089}
    values = list(range(1089))
    warm_source = panel_verify._fixture_template(64, values, 64, 1089)
    panel_verify.audit_fixture_source(warm_source, warmed, values)
    reset = warm_source.replace('process_range(WARMUP,TOTAL)', 'process_range(0,TOTAL)')
    with pytest.raises(ValueError, match='audited'):
        panel_verify.audit_fixture_source(reset, warmed, values)


def test_raw_histogram_and_marker_mutations_are_rejected():
    raw = simulator_stderr()
    broken_hist = raw.replace('16: 2, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0]',
                              '16: 2, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]')
    with pytest.raises(ValueError, match='bins|totals'):
        panel_verify.rederive_raw_events(broken_hist)
    with pytest.raises(ValueError, match='markers'):
        panel_verify.rederive_raw_events(raw.replace('GPIOC[0] cleared', 'GPIOC[0] raised'))


def _encoded(prefix, values, bits):
    return prefix + ':' + ''.join(f'{value % (1 << bits):0{bits // 4}x}' for value in values)


@pytest.mark.parametrize('damage', ['output', 'state', 'guard', 'duplicate_output'])
def test_saved_output_state_and_guard_traces_are_independently_checked(tmp_path, damage):
    h = [1] * 48
    x = [0] * 257
    outs = [0] * len(x)
    state = [0] * 47
    if damage == 'output':
        outs[0] = 1
    elif damage == 'state':
        state[0] = 1
    guard = '5a5a5a5a' * 4 + '5a5a' * 4
    if damage == 'guard':
        guard = '0' * len(guard)
    stdout = '\n'.join([_encoded('O', outs, 16), _encoded('H', state, 64),
                        'G:' + guard, 'M:00000062']) + '\n'
    if damage == 'duplicate_output':
        stdout += _encoded('O', outs, 16) + '\n'
    (tmp_path / 'stdout.txt').write_text(stdout)
    import hashlib
    row = {'filter': 'native_lp1800', 'stimulus': 'full', 'total_samples': 257,
           'measured_samples': 257, 'variant': 'wide_direct64', 'artifacts': {'stdout': 'stdout.txt'},
           'artifact_sha256': {'stdout': hashlib.sha256(stdout.encode()).hexdigest()},
           'state_allocation_bytes': 98, 'outputs_verified': 257,
           'guards_verified': True, 'state_verified': True}
    design = {'filters': {'native_lp1800': {'coefficients': h}}}
    inputs = {'full': x}
    with pytest.raises(ValueError, match='trace|guard|terminal'):
        panel_verify.audit_trace(row, tmp_path, design, inputs)


def test_real_correctness_gate_attempt_is_independently_admitted():
    attempt = (HERE / 'build/panel/correctness/native_lp1800__wide_direct64__gcc15__1'
               / 'attempt-005/attempt.json')
    assert attempt.is_file(), 'the declared target gate fixture must be preserved before this audit'
    row = json.loads(attempt.read_text())
    audit = panel_verify.audit_gate_attempt(row, HERE)
    assert audit['status'] == 'admitted'
    assert audit['outputs_verified'] == 194
    assert audit['state_allocation_bytes'] == 98
    assert audit['raw_events']['instructions'] > 0
    assert audit['memory']['initial_sp'] == 0x20001FF0
    assert audit['stack']['maximum_live_stack_bytes'] <= 2048


def test_real_performance_case_audit_rejects_rewritten_exact_clamp_metrics():
    checkpoint = json.loads((HERE / 'build/panel/performance/checkpoint-results.json').read_text())
    row = next(r for r in checkpoint['rows'] if r['identity']['regime'] == 'post_startup')
    protocol = panel_verify.load_frozen_protocol(HERE)
    design = json.loads((HERE / 'panel-design.json').read_text())
    inputs = json.loads((HERE / 'panel-inputs.json').read_text())
    panel_verify.audit_case(row, HERE, protocol, design, inputs)
    mutated = json.loads(json.dumps(row))
    mutated['quantizer_clamp_paths']['positive'] += 1
    with pytest.raises(ValueError, match='clamp paths'):
        panel_verify.audit_case(mutated, HERE, protocol, design, inputs)


def test_runner_pass_with_incomplete_tool_provenance_is_not_independently_admitted():
    attempt = (HERE / 'build/panel/correctness/native_lp1800__wide_direct64__gcc15__1'
               / 'attempt-002/attempt.json')
    assert attempt.is_file(), 'rejected historical attempt must remain available for audit'
    row = json.loads(attempt.read_text())
    with pytest.raises(ValueError, match='raw artifacts'):
        panel_verify.audit_gate_attempt(row, HERE)


def _restore_gate_attempt(tmp_path, number='005', relative=None):
    original = (HERE / (relative or
                f'build/panel/correctness/native_lp1800__wide_direct64__gcc15__1/attempt-{number}'))
    row = json.loads((original / 'attempt.json').read_text())
    root = tmp_path / 'restored-campaign'
    root.mkdir()
    for name in ('panel-protocol.json', 'panel-design.json', 'sources-manifest.json'):
        shutil.copyfile(HERE / name, root / name)
    target = root / row['directory']
    target.parent.mkdir(parents=True)
    shutil.copytree(original, target)
    row_path = target / 'attempt.json'
    row = json.loads(row_path.read_text())
    return root, target, row


def _restore_direct_or_cmsis(tmp_path, cmsis):
    relative = ('build/panel/correctness/wide_lp4600__cmsis64_unroll__gcc10__1/attempt-003'
                if cmsis else
                'build/panel/correctness/native_lp1800__wide_direct64__gcc15__64/attempt-003')
    root, target, row = _restore_gate_attempt(tmp_path, relative=relative)
    assert panel_verify.audit_gate_attempt(row, root)['status'] == 'admitted'
    return root, target, row


def _rewrite_artifact(target, row, artifact_name, data):
    relative = row['artifact_paths'][artifact_name]
    (target / relative).write_bytes(data)
    row['artifact_sha256'][artifact_name] = hashlib.sha256(data).hexdigest()


def test_saved_gate_audit_succeeds_from_relocated_tree_without_target_tools(tmp_path):
    root, _, row = _restore_gate_attempt(tmp_path)
    audit = panel_verify.audit_gate_attempt(row, root)
    assert audit['status'] == 'admitted'
    assert audit['source_identity']['dependency_count'] >= 3
    assert audit['binary_binding']['input_bytes'] == 388
    assert audit['binary_binding']['disassembly_bytes_bound'] > 0


def test_real_attempt_source_mutation_rejected_even_with_rewritten_artifact_hash(tmp_path):
    root, target, row = _restore_gate_attempt(tmp_path)
    data = (target / row['artifact_paths']['kernel_source']).read_bytes() + b'/* tampered */\n'
    _rewrite_artifact(target, row, 'kernel_source', data)
    with pytest.raises(ValueError, match='frozen source bytes'):
        panel_verify.audit_gate_attempt(row, root)


@pytest.mark.parametrize('cmsis', [False, True], ids=['direct', 'cmsis'])
def test_real_attempt_empty_effective_provenance_rejected_after_rehash(tmp_path, cmsis):
    root, target, row = _restore_direct_or_cmsis(tmp_path, cmsis)
    for key in ('dependencies', 'dependency_hashes', 'macros'):
        _rewrite_artifact(target, row, key, b'{}\n')
    with pytest.raises(ValueError, match='translation-unit inventory'):
        panel_verify.audit_gate_attempt(row, root)


@pytest.mark.parametrize('cmsis', [False, True], ids=['direct', 'cmsis'])
def test_real_attempt_jointly_removed_translation_unit_rejected(tmp_path, cmsis):
    root, target, row = _restore_direct_or_cmsis(tmp_path, cmsis)
    for key, tu in (('dependencies', 'probe.c'), ('macros', 'probe.c')):
        obj = json.loads((target / row['artifact_paths'][key]).read_text())
        del obj[tu]
        _rewrite_artifact(target, row, key, (json.dumps(obj, indent=2, sort_keys=True) + '\n').encode())
    hashes = json.loads((target / row['artifact_paths']['dependency_hashes']).read_text())
    hashes = {path: digest for path, digest in hashes.items()
              if not path.endswith('/probe.c') and
              not (cmsis is False and path.endswith('/kernels.h'))}
    _rewrite_artifact(target, row, 'dependency_hashes',
                      (json.dumps(hashes, indent=2, sort_keys=True) + '\n').encode())
    with pytest.raises(ValueError, match='translation-unit inventory'):
        panel_verify.audit_gate_attempt(row, root)


@pytest.mark.parametrize('cmsis', [False, True], ids=['direct', 'cmsis'])
def test_real_attempt_missing_required_header_dependency_rejected_after_joint_removal(tmp_path, cmsis):
    root, target, row = _restore_direct_or_cmsis(tmp_path, cmsis)
    deps = json.loads((target / row['artifact_paths']['dependencies']).read_text())
    probe_deps = deps['probe.c']
    header_path = next(path for path in re.findall(r'(?m)(?<!\\)(/[^\s\\]+)', probe_deps)
                       if path.endswith('/probe.h'))
    deps['probe.c'] = probe_deps.replace(' ' + header_path, '')
    _rewrite_artifact(target, row, 'dependencies',
                      (json.dumps(deps, indent=2, sort_keys=True) + '\n').encode())
    with pytest.raises(ValueError, match='required copied probe.h'):
        panel_verify.audit_gate_attempt(row, root)


@pytest.mark.parametrize('cmsis', [False, True], ids=['direct', 'cmsis'])
def test_real_attempt_copied_header_rewrite_rejected_even_with_artifact_rehash(tmp_path, cmsis):
    root, target, row = _restore_direct_or_cmsis(tmp_path, cmsis)
    header = (target / row['artifact_paths']['kernel_header']).read_bytes() + b'/* changed */\n'
    _rewrite_artifact(target, row, 'kernel_header', header)
    with pytest.raises(ValueError, match='frozen source bytes'):
        panel_verify.audit_gate_attempt(row, root)


def test_real_cmsis_attempt_missing_pinned_header_from_every_tu_is_rejected(tmp_path):
    root, target, row = _restore_direct_or_cmsis(tmp_path, True)
    deps = json.loads((target / row['artifact_paths']['dependencies']).read_text())
    header_path = next(path for text in deps.values()
                       for path in re.findall(r'(?m)(?<!\\)(/[^\s\\]+)', text)
                       if path.endswith('/cmsis_gcc.h'))
    for tu in ('firmware.c', 'probe.c', 'library.c'):
        deps[tu] = deps[tu].replace(header_path, '')
    _rewrite_artifact(target, row, 'dependencies',
                      (json.dumps(deps, indent=2, sort_keys=True) + '\n').encode())
    hashes = json.loads((target / row['artifact_paths']['dependency_hashes']).read_text())
    del hashes[header_path]
    _rewrite_artifact(target, row, 'dependency_hashes',
                      (json.dumps(hashes, indent=2, sort_keys=True) + '\n').encode())
    with pytest.raises(ValueError, match='missing pinned CMSIS/core header cmsis-core/cmsis_gcc.h'):
        panel_verify.audit_gate_attempt(row, root)


def test_real_attempt_rewritten_local_dependency_hash_is_rejected(tmp_path):
    root, target, row = _restore_direct_or_cmsis(tmp_path, False)
    hashes = json.loads((target / row['artifact_paths']['dependency_hashes']).read_text())
    header = next(path for path in hashes if path.endswith('/probe.h'))
    hashes[header] = '0' * 64
    _rewrite_artifact(target, row, 'dependency_hashes',
                      (json.dumps(hashes, indent=2, sort_keys=True) + '\n').encode())
    with pytest.raises(ValueError, match='copied dependency hash differs'):
        panel_verify.audit_gate_attempt(row, root)


def test_real_attempt_exact_command_contract_rejects_mutually_rewritten_log(tmp_path):
    root, target, row = _restore_gate_attempt(tmp_path)
    commands = row['commands']
    commands[0]['argv'].append('-fno-strict-aliasing')
    row['commands'] = commands
    data = (json.dumps(commands, indent=2, sort_keys=True) + '\n').encode()
    _rewrite_artifact(target, row, 'commands', data)
    with pytest.raises(ValueError, match='exact frozen command grammar'):
        panel_verify.audit_gate_attempt(row, root)


def test_real_attempt_macro_mutation_rejected_with_rewritten_file_hash(tmp_path):
    root, target, row = _restore_gate_attempt(tmp_path)
    macro_data = json.loads((target / row['artifact_paths']['macros']).read_text())
    macro_data['probe.c'] = macro_data['probe.c'].replace('#define __ARM_ARCH 6', '#define __ARM_ARCH 7')
    data = (json.dumps(macro_data, indent=2, sort_keys=True) + '\n').encode()
    _rewrite_artifact(target, row, 'macros', data)
    with pytest.raises(ValueError, match='ARM architecture/endianness'):
        panel_verify.audit_gate_attempt(row, root)


def test_real_elf_and_binary_input_mutation_rejected_as_wrong_frozen_stream(tmp_path):
    root, target, row = _restore_gate_attempt(tmp_path)
    elf_path = target / row['artifact_paths']['elf']
    layout = panel_verify._elf_layout(elf_path)
    symbol = layout['symbols']['input_data']
    segment = next(s for s in layout['segments'] if s['vaddr'] <= symbol['address'] < s['vaddr'] + s['file_size'])
    elf = bytearray(layout['elf_bytes'])
    offset = segment['file_offset'] + symbol['address'] - segment['vaddr']
    elf[offset] ^= 1
    binary_path = target / row['artifact_paths']['binary']
    binary = bytearray(binary_path.read_bytes())
    first_flash = min(s['paddr'] for s in layout['segments'] if 0x08000000 <= s['paddr'] < 0x08010000)
    binary[symbol['address'] - first_flash] ^= 1
    _rewrite_artifact(target, row, 'elf', bytes(elf))
    _rewrite_artifact(target, row, 'binary', bytes(binary))
    with pytest.raises(ValueError, match='input_data bytes differ'):
        panel_verify.audit_gate_attempt(row, root)


def test_real_elf_allocated_orphan_section_range_mutation_is_rejected(tmp_path):
    root, target, row = _restore_gate_attempt(tmp_path)
    elf_path = target / row['artifact_paths']['elf']
    data = bytearray(elf_path.read_bytes())
    header = __import__('struct').unpack_from('<16sHHIIIIIHHHHHH', data)
    shoff, shentsize, shnum, shstrndx = header[6], header[11], header[12], header[13]
    sections = [__import__('struct').unpack_from('<IIIIIIIIII', data, shoff + i * shentsize)
                for i in range(shnum)]
    strings = sections[shstrndx]
    name_table = data[strings[4]:strings[4] + strings[5]]
    bss_index = next(i for i, section in enumerate(sections)
                     if name_table[section[0]:].split(b'\0', 1)[0] == b'.bss')
    __import__('struct').pack_into('<I', data, shoff + bss_index * shentsize + 12, 0x20002010)
    _rewrite_artifact(target, row, 'elf', bytes(data))
    with pytest.raises(ValueError, match='allocated section outside'):
        panel_verify.audit_gate_attempt(row, root)


def test_real_stack_frame_mutation_cannot_be_hidden_by_runner_stack_summary(tmp_path):
    root, target, row = _restore_gate_attempt(tmp_path)
    stack_key = next(name for name in row['artifact_paths'] if name.startswith('stack_probe'))
    path = target / row['artifact_paths'][stack_key]
    data = path.read_text().replace('\t616\tstatic', '\t4096\tstatic')
    assert data != path.read_text(), 'real probe_process frame row changed in test fixture'
    _rewrite_artifact(target, row, stack_key, data.encode())
    with pytest.raises(ValueError, match='exceeds 2048'):
        panel_verify.audit_gate_attempt(row, root)


def test_saved_correctness_campaign_has_exact_admitted_and_pending_inventory():
    result = panel_verify.audit_correctness_campaign(HERE)
    assert (result['identity_count'], result['admitted_count'], result['skipped_count'],
            result['failed_count']) == (72, 70, 2, 0)
    assert all(row['outputs_verified'] == 194 for row in result['audited'])


def test_correctness_campaign_rejects_duplicate_or_missing_gate_identity(tmp_path):
    source = json.loads((HERE / 'build/panel/correctness/correctness-gates.json').read_text())
    target = tmp_path / 'build/panel/correctness/correctness-gates.json'
    target.parent.mkdir(parents=True)
    for name in ('panel-protocol.json', 'panel-design.json'):
        (tmp_path / name).write_bytes((HERE / name).read_bytes())
    duplicate = dict(source)
    duplicate['rows'] = source['rows'] + [dict(source['rows'][0])]
    target.write_text(json.dumps(duplicate))
    with pytest.raises(ValueError, match='duplicate correctness gate identity'):
        panel_verify.audit_correctness_campaign(tmp_path)
    missing = dict(source)
    missing['rows'] = source['rows'][:-1]
    target.write_text(json.dumps(missing))
    with pytest.raises(ValueError, match='missing or contains extras'):
        panel_verify.audit_correctness_campaign(tmp_path)

"""Held-out FIR validation; see ../fir-validation-protocol.md before running."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import statistics

import numpy as np
import scipy
from scipy import signal

from simulator import (ROOT, BUILD, FLAGS, PIN, ENERGY_WEIGHTS, sha, command, run,
                       arm_zero_ws_cycles, estimated_energy_nj)
from experiment import decode_output, check_instruction_subset
from cmsis_baseline import DSP_PIN

OUT = ROOT / 'selection-results.json'
DESIGN = ROOT / 'selection-design.json'
PROTOCOL = ROOT.parent / 'fir-validation-protocol.md'
WORK = BUILD / 'selection-validation'

KERNELS = ('direct64', 'direct32', 'fold64', 'fold32', 'fold64_wide',
           'cmsis64', 'cmsis32', 'cmsis64_unroll', 'cmsis32_unroll')


def is_admitted(kernel, coefficients, maximum):
    if kernel not in KERNELS:
        raise ValueError(kernel)
    h = [int(c) for c in coefficients]
    if not h or any(not -32768 <= c <= 32767 for c in h) or not 1 <= maximum <= 32768:
        raise ValueError('Invalid int16 coefficients or magnitude contract')
    if kernel.startswith('cmsis') and (len(h) < 4 or len(h) % 2):
        return False
    if kernel.startswith('fold') and h != h[::-1]:
        return False
    if kernel in ('direct32', 'fold32', 'cmsis32', 'cmsis32_unroll'):
        if maximum * sum(abs(c) for c in h) > 2**31 - 1:
            return False
    if kernel in ('fold32', 'fold64'):
        if any(2 * maximum * abs(c) > 2**31 - 1 for c in h[:len(h)//2]):
            return False
    return True

def select_kernel(coefficients, maximum):
    for kernel in ('fold32', 'fold64', 'direct32', 'direct64'):
        if is_admitted(kernel, coefficients, maximum):
            return kernel
    raise AssertionError('The direct64 reference must be admissible')

def case_header(coefficients, inputs, block):
    h = [int(c) for c in coefficients]
    return (f'#define TAPS {len(h)}\n#define BLOCK {block}\n#define SAMPLES {len(inputs)}\n'
            + 'static const int16_t coefficients[TAPS]={' + ','.join(map(str, h)) + '};\n'
            + 'static const int16_t cmsis_coefficients[TAPS]={' + ','.join(map(str, h[::-1])) + '};\n'
            + 'static const int16_t input_data[SAMPLES]={' + ','.join(map(str, inputs)) + '};\n')

def make_inputs():
    raw = np.random.default_rng(20261020).integers(-1024, 1024, 513).tolist()
    raw[:7] = [-1024, 1023, 0, -1, 1, -1023, 1022]
    return raw, [32*x for x in raw]

def reference_outputs(coefficients, inputs):
    # Independent Python arbitrary-precision integer reference, not target C.
    return [max(-32768, min(32767, sum(int(coefficients[i]) * int(inputs[n-i])
                for i in range(min(len(coefficients), n+1))) // 32768))
            for n in range(len(inputs))]

def evaluate_selection(coefficients, maximum, rows):
    chosen = select_kernel(coefficients, maximum)
    by_name = {r['kernel']: r for r in rows}
    if chosen not in by_name:
        raise ValueError('Missing chosen candidate; invalid or incomplete evaluation')
    energy = min(rows, key=lambda r: r['estimated_cpu_energy_nj'])
    cycles = min(rows, key=lambda r: r['arm_zero_ws_cycles'])
    return {'chosen': chosen, 'energy_best': energy['kernel'], 'cycle_best': cycles['kernel'],
            'energy_regret': by_name[chosen]['estimated_cpu_energy_nj']/energy['estimated_cpu_energy_nj']-1,
            'cycle_regret': by_name[chosen]['arm_zero_ws_cycles']/cycles['arm_zero_ws_cycles']-1}


def prepare():
    """Freeze new literal coefficients, input values and policy/protocol hashes."""
    specifications = [
        ('speech_lp48', dict(numtaps=48, cutoff=3400, fs=16000, window='hamming')),
        ('sensor_lp80', dict(numtaps=80, cutoff=100, fs=1000, window='blackman')),
        ('vibration_bp192', dict(numtaps=192, cutoff=[100, 1000], fs=4000,
                                window=('kaiser', 5), pass_zero=False)),
        ('biosignal_bp96', dict(numtaps=96, cutoff=[.5, 40], fs=360,
                               window='hamming', pass_zero=False)),
        ('mains_bs65', dict(numtaps=65, cutoff=[48, 52], fs=360,
                          window='hamming', pass_zero=True)),
        ('speech_minphase48', dict(numtaps=95, cutoff=3400, fs=16000, window='hamming')),
    ]
    filters = {}
    for name, spec in specifications:
        floating = signal.firwin(**spec, scale=True)
        if name == 'speech_minphase48':
            floating = signal.minimum_phase(floating, method='homomorphic', half=True, n_fft=32768)
        h = np.rint(floating*32768).astype(np.int64).tolist()
        assert all(-32768 <= c <= 32767 for c in h)
        symmetric = h == h[::-1]
        assert symmetric == (name != 'speech_minphase48'), name
        filters[name] = {'design': spec, 'coefficients': h, 'symmetric': symmetric,
                         'coefficient_l1': sum(abs(c) for c in h),
                         'full_int16_bound': 32768*sum(abs(c) for c in h),
                         'adc11_bound': 1024*sum(abs(c) for c in h)}
    raw, shifted = make_inputs()
    data = {'protocol_sha256': sha(PROTOCOL), 'implementation_sha256': sha(__file__),
            'policy': 'fold32 if admitted; fold64 if admitted; direct32 if admitted; direct64',
            'scipy': scipy.__version__, 'numpy': np.__version__, 'filters': filters,
            'inputs': {'adc_raw': raw, 'adc_shifted_q15': shifted},
            'blocks': [1, 16, 64], 'optimization': '-O2', 'kernels': KERNELS,
            'seed': 20261020, 'samples': 513, 'held_out_from': 'original six-filter pilot only'}
    DESIGN.write_text(json.dumps(data, indent=2)+'\n')
    print('Frozen design', sha(DESIGN), flush=True)
    return data


def toolchains():
    return {'gcc10': Path(shutil.which('arm-none-eabi-gcc')).resolve(),
            'gcc15': BUILD/'toolchains/arm-gnu-toolchain-15.2.rel1-x86_64-arm-none-eabi/bin/arm-none-eabi-gcc'}


def compile_case(directory, compiler, kernel):
    """Independent compiler/source/flag caches: never reuse pilot objects."""
    directory.mkdir(parents=True, exist_ok=True)
    cmsis = kernel.startswith('cmsis')
    macros = ['-DARM_MATH_LOOPUNROLL'] if kernel.endswith('_unroll') else []
    base = 'cmsis32' if kernel.startswith('cmsis32') else 'cmsis64'
    symbol = 'arm_fir_fast_q15' if base == 'cmsis32' else 'arm_fir_q15'
    source = (BUILD/'cmsis-dsp/Source/FilteringFunctions'/f'{symbol}.c') if cmsis else ROOT/'kernels.c'
    includes = ['-I', ROOT, '-I', BUILD/'cmsis-dsp/Include', '-I', BUILD/'cmsis-core']
    common = [compiler, *FLAGS, '-O2', '-Wall', '-Wextra', '-Werror', *includes, *macros]
    identity = hashlib.sha256(json.dumps([str(compiler), sha(compiler), sha(source),
                                         FLAGS, macros]).encode()).hexdigest()[:20]
    cache = WORK/'objects'/identity
    cache.mkdir(parents=True, exist_ok=True)
    obj = cache/'kernel.o'
    if not obj.exists():
        command([*common, '-c', source, '-o', obj])
    startup = cache/'startup.o'
    if not startup.exists():
        command([compiler, *FLAGS, '-c', ROOT/'startup.s', '-o', startup])
    selection = f'-DCMSIS_KERNEL={symbol}' if cmsis else f'-DKERNEL={kernel}'
    command([*common, '-I', directory, selection, '-c', ROOT/'validation_firmware.c',
             '-o', directory/'firmware.o'])
    command([compiler, *FLAGS, '-nostdlib', '-T', ROOT/'link.ld', '-Wl,--gc-sections',
             f'-Wl,-Map={directory/"firmware.map"}', startup, directory/'firmware.o', obj,
             '-lgcc', '-o', directory/'firmware.elf'])
    command([compiler.with_name('arm-none-eabi-objcopy'), '-O', 'binary',
             directory/'firmware.elf', directory/'firmware.bin'])
    (directory/'firmware.disasm').write_text(command([
        compiler.with_name('arm-none-eabi-objdump'), '-d', directory/'firmware.elf']).stdout)
    return directory/'firmware.bin'


def checked_case(sim, directory, compiler, kernel, h, x, block):
    directory.mkdir(parents=True, exist_ok=True)
    (directory/'case_data.h').write_text(case_header(h, x, block))
    binary = compile_case(directory, compiler, kernel)
    mnemonics = check_instruction_subset((directory/'firmware.disasm').read_text())
    events, stdout = run(sim, binary)
    output = decode_output(stdout, 'O').tolist()
    history = decode_output(stdout, 'H').tolist()
    guards = decode_output(stdout, 'G').tolist()
    assert output == reference_outputs(h, x), (directory.name, 'output mismatch')
    assert history == ([0]*(len(h)-1)+x)[-(len(h)-1):], (directory.name, 'history mismatch')
    assert guards == [23130]*8, (directory.name, 'canary mismatch')
    artifacts = {p.name: sha(p) for p in directory.iterdir()
                 if p.suffix in ('.elf', '.bin', '.h', '.disasm', '.stdout', '.stderr', '.map')}
    return ({**events, 'arm_zero_ws_cycles': arm_zero_ws_cycles(events),
             'estimated_cpu_energy_nj': estimated_energy_nj(events)},
            {'directory': str(directory.relative_to(ROOT)), 'artifacts': artifacts,
             'outputs_verified': len(output), 'history_verified': True,
             'guards_verified': True, 'mnemonics': mnemonics, 'bin_sha256': sha(binary)})


def summarize(groups):
    return {'groups': len(groups),
            'energy_winner_agreement': sum(g['energy_regret'] < 1e-12 for g in groups),
            'cycle_winner_agreement': sum(g['cycle_regret'] < 1e-12 for g in groups),
            'energy_regret_mean': statistics.mean(g['energy_regret'] for g in groups),
            'energy_regret_max': max(g['energy_regret'] for g in groups),
            'cycle_regret_mean': statistics.mean(g['cycle_regret'] for g in groups),
            'cycle_regret_max': max(g['cycle_regret'] for g in groups)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    if args.verify:
        verify()
    if not (args.run or args.smoke):
        return
    design = json.loads(DESIGN.read_text())
    assert design['protocol_sha256'] == sha(PROTOCOL), 'Protocol changed since prepare'
    assert design['implementation_sha256'] == sha(__file__), 'Implementation changed since prepare'
    sim = BUILD/'thumbulator/sim_main'
    pilot = json.loads((ROOT/'results.json').read_text())
    assert sha(sim) == pilot['simulator_binary_sha256']
    dsp = BUILD/'cmsis-dsp'
    assert command(['git', 'rev-parse', 'HEAD'], dsp).stdout.strip() == DSP_PIN
    assert not command(['git', 'status', '--porcelain'], dsp).stdout.strip()
    compilers = toolchains()
    compiler_info = {name: {'path': str(path), 'sha256': sha(path),
                            'version': command([path, '--version']).stdout.splitlines()[0]}
                     for name, path in compilers.items()}
    if args.smoke:
        # Test reversed CMSIS ordering, pair folding, odd centers and tail blocks
        # with literal hand-understandable fixtures before the held-out matrix.
        cases = [([1234, -8000, 7000, 300], 'nonsymmetric'),
                 ([10, 20, 30000, 20, 10], 'odd'),
                 ([1234, -8000, -8000, 1234], 'symmetric')]
        count = 0
        for tool, compiler in compilers.items():
            for h, label in cases:
                for kernel in KERNELS:
                    if is_admitted(kernel, h, 32768):
                        checked_case(sim, WORK/'smoke'/f'{tool}-{label}-{kernel}', compiler,
                                     kernel, h, [-32768, 32767, -1, 0, 1, -29999, 30000]*3, 4)
                        count += 1
        print(f'Smoke: {count} target binaries, all outputs/history/canaries matched', flush=True)
    if not args.run:
        return
    rows, excluded, binaries, groups = [], [], [], []
    for name, item in design['filters'].items():
        h = item['coefficients']
        for tool, compiler in compilers.items():
            print(f'Validating {name} {tool}', flush=True)
            for input_name, x in design['inputs'].items():
                contracts = {'full_int16': 32768}
                if input_name == 'adc_raw':
                    contracts['adc11'] = 1024
                for block in design['blocks']:
                    for kernel in KERNELS:
                        base_row = dict(filter=name, compiler=tool, input=input_name,
                                        block=block, kernel=kernel)
                        allowed = [c for c, m in contracts.items() if is_admitted(kernel, h, m)]
                        for contract in contracts:
                            if contract not in allowed:
                                excluded.append({**base_row, 'contract': contract,
                                                 'reason': 'symmetry, library tap contract, or width proof'})
                        if not allowed:
                            continue
                        identity = f'{name}-{tool}-{input_name}-b{block}-{kernel}'
                        costs, artifact = checked_case(sim, WORK/'cases'/identity, compiler,
                                                       kernel, h, x, block)
                        binaries.append({'id': identity, **base_row, **artifact})
                        for contract in allowed:
                            rows.append({**base_row, 'contract': contract, 'binary_id': identity,
                                         'samples': len(x), 'taps': len(h), **costs})
                    for contract, maximum in contracts.items():
                        group_rows = [r for r in rows if r['filter'] == name and r['compiler'] == tool
                                      and r['input'] == input_name and r['block'] == block
                                      and r['contract'] == contract]
                        groups.append(dict(filter=name, compiler=tool, input=input_name,
                                           block=block, contract=contract,
                                           **evaluate_selection(h, maximum, group_rows)))
    source_files = [Path(__file__), ROOT/'validation_firmware.c', ROOT/'kernels.c', ROOT/'kernels.h',
                    ROOT/'startup.s', ROOT/'link.ld', ROOT/'simulator.py', ROOT/'experiment.py',
                    ROOT/'cmsis_baseline.py', ROOT/'test_selection_validation.py', PROTOCOL]
    output = {'status': 'held-out policy evaluation; simulated events and model estimates only',
              'design_sha256': sha(DESIGN), 'sources': {str(p.relative_to(ROOT.parent)): sha(p) for p in source_files},
              'compilers': compiler_info, 'common_flags': FLAGS, 'optimization': '-O2', 'lto': False,
              'simulator_commit': PIN, 'simulator_binary_sha256': sha(sim),
              'cmsis_commit': DSP_PIN, 'cmsis_source_hashes': pilot['cmsis_dsp']['source_hashes'],
              'cmsis_core_hashes': pilot['cmsis_dsp']['core_header_hashes'],
              'energy_weights_nj': ENERGY_WEIGHTS, 'rows': rows, 'excluded': excluded,
              'binaries': binaries, 'groups': groups, 'summary': summarize(groups),
              'by_compiler': {t: summarize([g for g in groups if g['compiler'] == t]) for t in compilers}}
    OUT.write_text(json.dumps(output, indent=2)+'\n')
    with (ROOT/'selection-results.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({'binaries': len(binaries), 'rows': len(rows), 'excluded': len(excluded),
                      'target_output_comparisons': sum(b['outputs_verified'] for b in binaries),
                      **output['summary']}), flush=True)


def verify():
    """Reconstruct numerical outputs, costs, candidate accounting and summaries."""
    result = json.loads(OUT.read_text())
    design = json.loads(DESIGN.read_text())
    assert sha(DESIGN) == result['design_sha256']
    for relative, expected in result['sources'].items():
        assert sha(ROOT.parent/relative) == expected, relative
    records = {b['id']: b for b in result['binaries']}
    for binary in records.values():
        directory = ROOT/binary['directory']
        for name, expected in binary['artifacts'].items():
            assert sha(directory/name) == expected, (binary['id'], name)
        h = design['filters'][binary['filter']]['coefficients']
        x = design['inputs'][binary['input']]
        stdout = (directory/'firmware.stdout').read_text()
        assert decode_output(stdout, 'O').tolist() == reference_outputs(h, x)
        assert decode_output(stdout, 'H').tolist() == ([0]*(len(h)-1)+x)[-(len(h)-1):]
        assert decode_output(stdout, 'G').tolist() == [23130]*8
    for row in result['rows']:
        assert row['binary_id'] in records
        maximum = 1024 if row['contract'] == 'adc11' else 32768
        assert is_admitted(row['kernel'], design['filters'][row['filter']]['coefficients'], maximum)
        assert row['arm_zero_ws_cycles'] == arm_zero_ws_cycles(row)
        assert abs(row['estimated_cpu_energy_nj']-estimated_energy_nj(row)) < 1e-6
    for group in result['groups']:
        matching = [r for r in result['rows'] if all(r[k] == group[k]
                    for k in ('filter', 'compiler', 'input', 'block', 'contract'))]
        h = design['filters'][group['filter']]['coefficients']
        maximum = 1024 if group['contract'] == 'adc11' else 32768
        expected_kernels = {k for k in KERNELS if is_admitted(k, h, maximum)}
        assert {r['kernel'] for r in matching} == expected_kernels
        assert len(matching) == len(expected_kernels)
        for key, value in evaluate_selection(h, maximum, matching).items():
            assert group[key] == value
    assert summarize(result['groups']) == result['summary']
    with (ROOT/'selection-results.csv').open() as file:
        csv_rows = list(csv.DictReader(file))
    assert csv_rows == [{k: str(v) for k, v in r.items()} for r in result['rows']]
    print(f'Verified {len(records)} binaries, {len(result["rows"])} rows, '
          f'{sum(b["outputs_verified"] for b in records.values())} outputs; summary reconstructed')


if __name__ == '__main__':
    main()

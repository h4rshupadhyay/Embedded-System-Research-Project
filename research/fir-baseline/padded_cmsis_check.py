"""Post-evaluation baseline correction: exact zero extension for odd FIRs.

Does not alter the original protocol, policy, design or result file.
"""
import argparse
import json

from selection_validation import (ROOT, BUILD, WORK, OUT, DESIGN, PROTOCOL,
    toolchains, is_admitted, checked_case, reference_outputs, evaluate_selection, summarize)
from simulator import sha, arm_zero_ws_cycles, estimated_energy_nj
from experiment import decode_output

OUTPUT = ROOT/'selection-padded-cmsis.json'
LIBRARIES = ('cmsis64', 'cmsis32', 'cmsis64_unroll', 'cmsis32_unroll')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    original = json.loads(OUT.read_text())
    design = json.loads(DESIGN.read_text())
    name = 'mains_bs65'
    h = design['filters'][name]['coefficients']
    padded = h + [0]  # lag order; case_header reverses the COMPLETE array for CMSIS.
    assert len(h) % 2 and len(padded) % 2 == 0
    if args.verify:
        result = json.loads(OUTPUT.read_text())
        assert result['original_results_sha256'] == sha(OUT)
        assert result['source_sha256'] == sha(__file__)
        for record in result['binaries']:
            directory = ROOT/record['directory']
            for filename, expected in record['artifacts'].items():
                assert sha(directory/filename) == expected
            x = design['inputs'][record['input']]
            stdout = (directory/'firmware.stdout').read_text()
            assert decode_output(stdout, 'O').tolist() == reference_outputs(h, x)
            assert decode_output(stdout, 'H').tolist()[-(len(h)-1):] == x[-(len(h)-1):]
            assert decode_output(stdout, 'G').tolist() == [23130]*8
        for row in result['rows']:
            assert is_admitted(row['kernel'].removesuffix('_padded'), padded,
                               1024 if row['contract'] == 'adc11' else 32768)
            assert arm_zero_ws_cycles(row) == row['arm_zero_ws_cycles']
            assert abs(estimated_energy_nj(row)-row['estimated_cpu_energy_nj']) < 1e-6
        merged = original['rows'] + result['rows']
        for group in result['expanded_groups']:
            matching = [r for r in merged if all(r[k] == group[k]
                        for k in ('filter', 'compiler', 'input', 'block', 'contract'))]
            coeffs = design['filters'][group['filter']]['coefficients']
            expected = evaluate_selection(coeffs, 1024 if group['contract'] == 'adc11' else 32768, matching)
            assert all(group[k] == value for k, value in expected.items())
        assert summarize(result['expanded_groups']) == result['expanded_summary']
        print(f'Verified padded supplement: {len(result["binaries"])} binaries, '
              f'{len(result["rows"])} rows; expanded policy summary reconstructed')
        return
    assert sha(BUILD/'thumbulator/sim_main') == original['simulator_binary_sha256']
    for tool, info in original['compilers'].items():
        assert sha(toolchains()[tool]) == info['sha256']
    rows, binaries = [], []
    for tool, compiler in toolchains().items():
        for kind, x in design['inputs'].items():
            # Prove numeric equivalence independently of every target candidate.
            assert reference_outputs(padded, x) == reference_outputs(h, x)
            contracts = {'full_int16': 32768}
            if kind == 'adc_raw':
                contracts['adc11'] = 1024
            for block in design['blocks']:
                for kernel in LIBRARIES:
                    assert all(is_admitted(kernel, padded, m) for m in contracts.values())
                    identity = f'{name}-{tool}-{kind}-b{block}-{kernel}-padded'
                    costs, record = checked_case(BUILD/'thumbulator/sim_main', WORK/'padded-cases'/identity,
                                                compiler, kernel, padded, x, block)
                    binaries.append({'id': identity, 'input': kind, **record})
                    for contract in contracts:
                        rows.append(dict(filter=name, compiler=tool, input=kind, block=block,
                            contract=contract, kernel=kernel+'_padded', binary_id=identity,
                            samples=len(x), logical_taps=len(h), taps=len(padded), **costs))
    merged = original['rows'] + rows
    groups = []
    for group in original['groups']:
        matching = [r for r in merged if all(r[k] == group[k]
                    for k in ('filter', 'compiler', 'input', 'block', 'contract'))]
        coeffs = design['filters'][group['filter']]['coefficients']
        groups.append({**group, **evaluate_selection(coeffs,
            1024 if group['contract'] == 'adc11' else 32768, matching)})
    result = {'stage': 'post-evaluation strengthening of odd-FIR library baseline; policy unchanged',
              'source': 'https://arm-software.github.io/CMSIS-DSP/v1.14.4/group__FIR.html',
              'source_sha256': sha(__file__), 'fixture_sha256': sha(ROOT/'validation_firmware.c'),
              'original_results_sha256': sha(OUT), 'design_sha256': sha(DESIGN),
              'padding': 'append zero in lag order, then reverse entire array for CMSIS',
              'original_taps': len(h), 'physical_taps': len(padded),
              'rows': rows, 'binaries': binaries, 'expanded_groups': groups,
              'expanded_summary': summarize(groups)}
    OUTPUT.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'supplement_binaries': len(binaries), 'supplement_rows': len(rows),
                      'output_comparisons': sum(b['outputs_verified'] for b in binaries),
                      **result['expanded_summary']}), flush=True)


if __name__ == '__main__':
    main()

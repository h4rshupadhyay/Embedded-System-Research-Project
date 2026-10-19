"""Post-evaluation descriptive analysis. Does not modify the frozen policy."""
from collections import Counter
import json

from simulator import ROOT, sha


def main():
    path = ROOT/'selection-results.json'
    result = json.loads(path.read_text())
    groups, rows = result['groups'], result['rows']
    dimensions = ('filter', 'compiler', 'input', 'block', 'contract')
    indexed = {}
    for row in rows:
        indexed.setdefault(tuple(row[k] for k in dimensions), {})[row['kernel']] = row
    per_filter = {}
    for name in sorted({g['filter'] for g in groups}):
        subset = [g for g in groups if g['filter'] == name]
        per_filter[name] = {
            'groups': len(subset),
            'energy_policy_wins': sum(g['energy_regret'] < 1e-12 for g in subset),
            'maximum_energy_regret': max(g['energy_regret'] for g in subset),
            'energy_winners': dict(Counter(g['energy_best'] for g in subset)),
        }
    reversals = []
    for group in groups:
        candidates = indexed[tuple(group[k] for k in dimensions)]
        if group['energy_best'] != group['cycle_best']:
            energy = candidates[group['energy_best']]
            cycle = candidates[group['cycle_best']]
            reversals.append({**group,
                'energy_penalty_of_cycle_winner': cycle['estimated_cpu_energy_nj']/energy['estimated_cpu_energy_nj']-1,
                'cycle_penalty_of_energy_winner': energy['arm_zero_ws_cycles']/cycle['arm_zero_ws_cycles']-1})
    paired = {}
    for group in groups:
        key = tuple(group[k] for k in dimensions if k != 'compiler')
        paired.setdefault(key, {})[group['compiler']] = group
    changed = [dict(zip(('filter', 'input', 'block', 'contract'), key),
                    old=pair['gcc10']['energy_best'], new=pair['gcc15']['energy_best'])
               for key, pair in paired.items()
               if pair['gcc10']['energy_best'] != pair['gcc15']['energy_best']]
    case_ids = [
        ('speech_lp48', 'gcc10', 'adc_raw', 1, 'full_int16'),
        ('speech_lp48', 'gcc15', 'adc_raw', 64, 'full_int16'),
        ('speech_minphase48', 'gcc15', 'adc_raw', 64, 'adc11'),
        ('vibration_bp192', 'gcc15', 'adc_raw', 64, 'full_int16'),
    ]
    causal_cases = []
    for identity in case_ids:
        alternatives = []
        for row in indexed[identity].values():
            features = {**row, 'nonmul': row['instructions']-row['mul']}
            terms = {k: features[k]*w for k, w in result['energy_weights_nj'].items()}
            assert abs(sum(terms.values())-row['estimated_cpu_energy_nj']) < 1e-6
            alternatives.append({**row, 'energy_terms_nj': terms,
                                 'energy_uj_per_output': row['estimated_cpu_energy_nj']/row['samples']/1000})
        causal_cases.append({'group': dict(zip(dimensions, identity)), 'alternatives': alternatives})
    analysis = {
        'result_sha256': sha(path), 'analysis_source_sha256': sha(__file__),
        'summary': result['summary'], 'by_compiler': result['by_compiler'], 'by_filter': per_filter,
        'executions': len(result['binaries']), 'valid_rows': len(rows),
        'exclusions': len(result['excluded']),
        'target_output_comparisons': sum(b['outputs_verified'] for b in result['binaries']),
        'unique_reference_positions': sum(len(x) for x in json.loads((ROOT/'selection-design.json').read_text())['inputs'].values())*len(per_filter),
        'energy_cycle_reversals': reversals, 'compiler_changed_energy_winners': changed,
        'compiler_matched_groups': len(paired), 'causal_cases': causal_cases,
        'interpretation': 'Descriptive evidence, not a new selector or physical energy validation. '
                          'Reused contract traces and compiler/block replications are not independent applications.'}
    (ROOT/'selection-analysis.json').write_text(json.dumps(analysis, indent=2)+'\n')
    print(json.dumps({k: analysis[k] for k in ('executions', 'valid_rows', 'exclusions',
                     'target_output_comparisons', 'unique_reference_positions')}, indent=2))
    print(f'Energy/cycle winner disagreements: {len(reversals)}; '
          f'compiler-changed energy winners: {len(changed)}/{len(paired)}')


if __name__ == '__main__':
    main()

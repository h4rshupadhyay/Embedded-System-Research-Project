"""Descriptive analysis of the exploratory probe; not held-out prediction."""
import collections
import json
from pathlib import Path

import probe

HERE=Path(__file__).resolve().parent


def main():
    verification=probe.verify_results(json.loads((probe.BASE/'selection-design.json').read_text()))
    data=json.loads((HERE/'results.json').read_text())
    groups=collections.defaultdict(dict)
    for row in data['rows']:
        groups[row['compiler'],row['filter'],row['maximum'],row['block']][row['variant']]=row
    comparisons=[]
    identical=0
    for key,rows in groups.items():
        best=min(rows.values(),key=lambda r:r['estimated_cpu_energy_nj'])
        trans=min((r for n,r in rows.items() if n.startswith('trans_')),key=lambda r:r['estimated_cpu_energy_nj'])
        control=min((r for n,r in rows.items() if not n.startswith('trans_')),key=lambda r:r['estimated_cpu_energy_nj'])
        cycle_best=min(rows.values(),key=lambda r:r['arm_zero_ws_cycles'])
        demand=rows['trans_hcub_demand']; eager=rows['trans_hcub_eager']; native=rows['trans_const']
        identical += native['artifacts']['firmware.bin']==rows['trans_csd']['artifacts']['firmware.bin']
        comparisons.append({'compiler':key[0],'filter':key[1],'maximum':key[2],'block':key[3],
            'winner':best['variant'],'cycle_winner':cycle_best['variant'],
            'best_transposed':trans['variant'],'best_nontransposed':control['variant'],
            'best_transposed_energy_overhead_percent':100*(trans['estimated_cpu_energy_nj']/control['estimated_cpu_energy_nj']-1),
            'demand_vs_native_percent':100*(demand['estimated_cpu_energy_nj']/native['estimated_cpu_energy_nj']-1),
            'demand_vs_eager_percent':100*(demand['estimated_cpu_energy_nj']/eager['estimated_cpu_energy_nj']-1),
            'winner_nj_per_output':best['estimated_cpu_energy_nj']/best['samples']})
    widths=[]
    for row in data.get('posthoc_width_controls',[]):
        key=(row['compiler'],row['filter'],row['maximum'],row['block'])
        mixed=groups[key][row['variant']]
        widths.append({'compiler':key[0],'filter':key[1],'maximum':key[2],'block':key[3],
                       'variant':row['variant'],
                       'uniform64_nj_per_output':row['estimated_cpu_energy_nj']/row['samples'],
                       'mixed_width_nj_per_output':mixed['estimated_cpu_energy_nj']/mixed['samples'],
                       'mixed_width_reduction_percent':100*(1-mixed['estimated_cpu_energy_nj']/row['estimated_cpu_energy_nj'])})
    resources=[]
    compilers=probe.toolchains()
    for row in data['rows']+data.get('posthoc_width_controls',[]):
        directory=HERE/row['directory']
        text=probe.command([compilers[row['compiler']].with_name('arm-none-eabi-nm'),'-S','--defined-only',directory/'firmware.elf']).stdout
        symbols={line.split()[3]:int(line.split()[1],16) for line in text.splitlines() if len(line.split())==4}
        selected={'probe_process','quant','h.0','reversed.0'}
        if row['variant'].startswith('cmsis'):selected.add('arm_fir_fast_q15' if row['variant'].startswith('cmsis32') else 'arm_fir_q15')
        if row['variant'] in ('direct32','direct64','fold32','fold64'):selected.add(row['variant'])
        code=sum(v for k,v in symbols.items() if k in selected or k.startswith('quant.'))
        # Readonly coefficient arrays are included when their conventional local
        # symbol exists; fixture input/printing/state-getter code is excluded.
        resources.append({'directory':row['directory'],'kernel_and_coefficient_symbol_bytes':code,
                          'included_symbols':{k:v for k,v in symbols.items() if k in selected or k.startswith('quant.')},
                          'probe_process_stack_bytes':next(s['bytes'] for s in row['stack_usage'] if s['function']=='probe_process'),
                          'state_allocation_bytes':row['state_allocation_bytes']})
    result={'result_sha256':probe.sha(HERE/'results.json'),'analysis_source_sha256':probe.sha(__file__),
            'verification':verification,'groups':len(groups),
            'energy_winners':dict(collections.Counter(r['winner'] for r in comparisons)),
            'cycle_winners':dict(collections.Counter(r['cycle_winner'] for r in comparisons)),
            'transposed_energy_wins':sum(r['winner'].startswith('trans_') for r in comparisons),
            'native_and_csd_identical_binaries':identical,
            'hcub_demand_beats_native_groups':sum(r['demand_vs_native_percent']<0 for r in comparisons),
            'hcub_demand_beats_eager_groups':sum(r['demand_vs_eager_percent']<0 for r in comparisons),
            'comparisons':comparisons,'posthoc_width_controls':widths,'resources':resources}
    (HERE/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Complete primary comparison','',
           'Descriptive; negative overhead means the best tested transposed kernel costs less modeled CPU energy than the strongest tested nontransposed control. These are 24 repeated experimental groups for three filter designs, not 24 independent applications.','',
           '| Compiler | Filter | Magnitude guarantee | Block | Best transposed | Best nontransposed | Transposed overhead |',
           '|---|---|---:|---:|---|---|---:|']
    for r in comparisons:
        lines.append(f'| {r["compiler"]} | {r["filter"]} | {r["maximum"]} | {r["block"]} | {r["best_transposed"]} | {r["best_nontransposed"]} | {r["best_transposed_energy_overhead_percent"]:+.2f}% |')
    (HERE/'comparison.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('comparisons','resources','posthoc_width_controls')}))


if __name__=='__main__':main()

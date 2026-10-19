"""Derive transparent summary/proof data and a scientific plot from saved runs."""
from collections import Counter, defaultdict
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from simulator import ROOT, sha


def main():
    result=json.loads((ROOT/"results.json").read_text())
    groups=defaultdict(list)
    for row in result["rows"]:
        groups[(row["filter"],row["input"],row["contract"],row["optimization"],row["block"])].append(row)
    best_energy=lambda group:min(group,key=lambda row:row["estimated_cpu_energy_nj"])
    best_cycles=lambda group:min(group,key=lambda row:row["arm_zero_ws_cycles"])
    changes=[]
    proofs=[]
    for name,h in result["coefficient_arrays"].items():
        for contract,maximum in (("full_int16",32768),("adc11",1024)):
            proofs.append({"filter":name,"contract":contract,"maximum_abs_input":maximum,
                           "coefficient_abs_sum":sum(abs(c) for c in h),
                           "all_prefixes_abs_bound":maximum*sum(abs(c) for c in h),
                           "int32_safe":maximum*sum(abs(c) for c in h)<=2**31-1,
                           "max_folded_product_abs_bound":max(2*maximum*abs(c) for c in h[:len(h)//2]),
                           "full_domain_maximum_sum_witness":sum(c*(32767 if c>=0 else -32768) for c in h)})
        for optimization in ("-O2","-Os"):
            for block in (1,16,64):
                full=best_energy(groups[(name,"adc","full_int16",optimization,block)])
                adc=best_energy(groups[(name,"adc","adc11",optimization,block)])
                if full["kernel"]!=adc["kernel"]:
                    changes.append({"filter":name,"optimization":optimization,"block":block,
                                    "full_contract_best":full["kernel"],"adc_contract_best":adc["kernel"],
                                    "modeled_energy_reduction_percent":100*(1-adc["estimated_cpu_energy_nj"]/full["estimated_cpu_energy_nj"])})
    summary={"results_sha256":sha(ROOT/"results.json"),"rows":len(result["rows"]),
             "distinct_target_binaries":len(result["binaries"]),
             "target_output_comparisons":sum(257 for _ in result["binaries"]),
             "distinct_reference_output_positions":6*2*257,
             "comparison_groups":len(groups),"matched_contract_pairs":6*2*3,
             "model_energy_winners":dict(Counter(best_energy(g)["kernel"] for g in groups.values())),
             "timing_energy_best_choice_disagreements":sum(best_energy(g)["kernel"]!=best_cycles(g)["kernel"] for g in groups.values()),
             "contract_changes":changes,"arithmetic_certificates":proofs}
    (ROOT/"analysis.json").write_text(json.dumps(summary,indent=2))
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10})
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.8),gridspec_kw={"width_ratios":[1.65,1]})
    names=["direct64","direct32","cmsis64","cmsis32","fold64","fold32","fold64_wide"]
    labels=["Direct\n64-bit","Direct\n32-bit","CMSIS\nstandard","CMSIS\nfast","Folded\n64-bit","Folded\n32-bit","Wide-product\ncontrol"]
    group=groups[("lowpass_128","adc","full_int16","-O2",64)]
    values=[next(r for r in group if r["kernel"]==name)["estimated_cpu_energy_nj"]/257/1000 for name in names]
    bars=axes[0].bar(labels,values,color=["#94a3b8"]*5+["#2563eb","#d97706"])
    axes[0].bar_label(bars,fmt="%.2f",padding=3,fontsize=9)
    axes[0].set_title("128-tap lowpass: implementation comparison",fontsize=11)
    axes[0].set_ylabel("Modeled CPU energy per output (µJ)")
    full=best_energy(groups[("bandpass_256","adc","full_int16","-O2",64)])
    adc=best_energy(groups[("bandpass_256","adc","adc11","-O2",64)])
    bars=axes[1].bar(["Full int16 contract\nFolded 64-bit","ADC11 contract\nFolded 32-bit"],
                     [r["estimated_cpu_energy_nj"]/257/1000 for r in (full,adc)],color=["#94a3b8","#2563eb"])
    axes[1].bar_label(bars,fmt="%.2f",padding=3)
    axes[1].set_title("256-tap bandpass: best admitted choice",fontsize=11)
    reduction=100*(1-adc["estimated_cpu_energy_nj"]/full["estimated_cpu_energy_nj"])
    axes[1].text(.5,.9,f"{reduction:.1f}% lower modeled energy\nwith identical actual samples",ha="center",va="top",transform=axes[1].transAxes)
    for axis in axes:
        axis.set_ylim(0,6.2)
        axis.spines[["top","right"]].set_visible(False)
        axis.grid(axis="y",alpha=.18)
        axis.set_axisbelow(True)
    fig.suptitle("FIR baseline pilot · Cortex-M0 · GCC -O2 · block size 64",fontsize=13)
    fig.text(.5,.02,"Published 20 MHz / prefetch-off / zero-wait-state CPU model. Simulation estimates; no hardware measurements.",ha="center",fontsize=9)
    fig.tight_layout(rect=(0,.07,1,.93))
    fig.savefig(ROOT/"energy-comparison.png",dpi=180)
    fig.savefig(ROOT/"energy-comparison.svg")
    print(json.dumps({k:summary[k] for k in ["rows","distinct_target_binaries","target_output_comparisons","comparison_groups","timing_energy_best_choice_disagreements"]}))


if __name__=="__main__":
    main()

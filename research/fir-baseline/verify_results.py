"""Verify saved research artifacts without rerunning target binaries."""
from collections import defaultdict
import csv
import json
import platform
import re

import numpy as np

from simulator import ROOT, BUILD, sha, arm_zero_ws_cycles, estimated_energy_nj, ENERGY_WEIGHTS
from experiment import admitted, array_hash, decode_output


def main():
    result=json.loads((ROOT/"results.json").read_text())
    analysis=json.loads((ROOT/"analysis.json").read_text())
    assert analysis["results_sha256"]==sha(ROOT/"results.json")
    assert result["kernel_source_sha256"]==sha(ROOT/"kernels.c")
    assert result["fixture_source_sha256"]==sha(ROOT/"firmware.c")
    assert result["startup_source_sha256"]==sha(ROOT/"startup.s")
    assert result["cmsis_dsp"]["fixture_sha256"]==sha(ROOT/"cmsis_firmware.c")
    assert result["simulator_binary_sha256"]==sha(BUILD/"thumbulator/sim_main")
    assert result["energy_model"]["weights_nj"]==ENERGY_WEIGHTS
    with (ROOT/"results.csv").open() as file:
        csv_rows=list(csv.DictReader(file))
    assert len(csv_rows)==len(result["rows"])==720
    for csv_row,row in zip(csv_rows,result["rows"]):
        assert all(csv_row[key]==str(value) for key,value in row.items())
    traces={b["id"]:b for b in result["binaries"]}
    assert len(traces)==len({b["bin_sha256"] for b in traces.values()})==486
    references={}
    for name,h in result["coefficient_arrays"].items():
        for kind,item in result["inputs"].items():
            x=np.array(item["values"],dtype=np.int16)
            assert array_hash(x)==item["sha256"]
            values=np.clip(np.convolve(x.astype(np.int64),np.array(h,dtype=np.int64))[:len(x)]
                           //32768,-32768,32767).astype(np.int16)
            references[(name,kind)]=(values,x[-(len(h)-1):])
    for identity,artifact in traces.items():
        directory=BUILD/"cases"/identity
        for filename,expected in artifact["files"].items():
            assert sha(directory/filename)==expected,(identity,filename)
        row=next(row for row in result["rows"] if row["binary_id"]==identity)
        stdout=(directory/"firmware.stdout").read_text()
        y=decode_output(stdout,"O")
        history=decode_output(stdout,"H")
        expected,expected_history=references[(row["filter"],row["input"])]
        assert np.array_equal(y,expected) and np.array_equal(history,expected_history),identity
    groups=defaultdict(list)
    for row in result["rows"]:
        h=result["coefficient_arrays"][row["filter"]]
        maximum={"adc11":1024,"full_int16":32768}[row["contract"]]
        mapped={"cmsis32":"direct32","cmsis64":"direct64"}.get(row["kernel"],row["kernel"])
        assert admitted(mapped,h,maximum),row
        assert row["output_mismatches"]==0 and row["history_verified"]
        assert row["arm_zero_ws_cycles"]==arm_zero_ws_cycles(row)
        assert abs(row["estimated_cpu_energy_nj"]-estimated_energy_nj(row))<1e-7
        # In this emitted bank, no runtime coefficient pruning is used.
        logical=row["samples"]*(row["taps"]//2 if mapped.startswith("fold") else row["taps"])
        assert row["mul"]==logical*(6 if mapped=="fold64_wide" else 1),row["binary_id"]
        groups[(row["filter"],row["input"],row["contract"],row["optimization"],row["block"])].append(row)
    assert len(groups)==108
    assert len(result["rows"])+len(result["excluded"])==6*3*2*3*7
    for item in result["excluded"]:
        maximum={"adc11":1024,"full_int16":32768}[item["contract"]]
        mapped="direct32" if item["kernel"]=="cmsis32" else item["kernel"]
        assert not admitted(mapped,result["coefficient_arrays"][item["filter"]],maximum)
    assert len(result["microchecks"])==8
    for check in result["microchecks"]:
        assert check["arm_estimated_cycles"]==check["expected_arm_cycles"]
    # Only local file links are checked here; primary web provenance is in the audit.
    workspace=ROOT.parent.parent
    for filename in ["professor-topic-proposal.md","research/fir-baseline-findings.md","research/fir-baseline/README.md"]:
        file=workspace/filename
        for link in re.findall(r"\]\(([^)]+)\)",file.read_text()):
            if not link.startswith(("https://","http://")):
                assert (file.parent/link).exists(),(filename,link)
    source_files=["kernels.c","kernels.h","firmware.c","cmsis_firmware.c","startup.s","link.ld",
                  "simulator.py","experiment.py","cmsis_baseline.py","fetch_cmsis.py","test_kernels.py",
                  "analyze.py","verify_results.py","simulator-console.patch","results.json","results.csv",
                  "analysis.json","microchecks.json","energy-comparison.png","energy-comparison.svg","README.md"]
    manifest={"python":platform.python_version(),"numpy":np.__version__,
              "hashes":{name:sha(ROOT/name) for name in source_files},
              "verified_rows":720,"distinct_target_executions":486,
              "target_output_comparisons":486*257,"mismatches":0,
              "limitation":"Numerical/target-model evidence; no hardware or novelty verification"}
    (ROOT/"manifest.json").write_text(json.dumps(manifest,indent=2))
    print("Verified 720 rows, 486 distinct binaries, 124902 target outputs/histories, all safety exclusions, model calculations, raw artifact hashes, and local report links.")


if __name__=="__main__":
    main()

"""Exploratory target FIR experiment. Run: python research/fir-baseline/experiment.py

No hardware timing or energy is measured. Matrix and source data are fixed;
simulator events feed an explicit Arm-table timing estimate and a published
configuration-specific CPU energy model. See README.md and the result report.
"""
import csv
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from simulator import (BUILD, ROOT, PIN, FLAGS, ENERGY_WEIGHTS, setup, microchecks,
                       compile_firmware, run, arm_zero_ws_cycles, estimated_energy_nj,
                       command, sha)

KERNELS=("direct64","direct32","fold64","fold32","fold64_wide")


def admitted(kernel, h, maximum):
    if kernel in ("direct32","fold32") and maximum*sum(abs(int(c)) for c in h)>2**31-1:
        return False
    if kernel in ("fold32","fold64") and any(
            2*maximum*abs(int(c))>2**31-1 for c in h[:len(h)//2]):
        return False
    return True


def array_hash(values):
    return hashlib.sha256(np.asarray(values,dtype="<i2").tobytes()).hexdigest()


def header(h,x,block):
    return (f"#define TAPS {len(h)}\n#define BLOCK {block}\n#define SAMPLES {len(x)}\n"
            +"static const int16_t coefficients[TAPS]={"+",".join(map(str,h))+"};\n"
            +"static const int16_t input_data[SAMPLES]={"+",".join(map(str,x))+"};\n")


def decode_output(stdout,prefix):
    line=re.search(rf"^{prefix}:([a-f0-9]*)$",stdout,re.M)
    if not line:
        raise AssertionError(f"Missing target output {prefix}: {stdout[:100]}")
    values=np.array([int(line.group(1)[i:i+4],16) for i in range(0,len(line.group(1)),4)],
                    dtype=np.uint16)
    return values.view(np.int16)


def check_instruction_subset(disassembly):
    ordinary={"adc","adcs","add","adds","adr","and","ands","asr","asrs",
              "bic","bics","bl","blx","bx","cmn","cmp","eor","eors",
              "ldmia","ldm","ldr","ldrb","ldrh","ldrsb","ldrsh","lsl","lsls",
              "lsr","lsrs","mov","movs","mul","muls","mvn","mvns","neg","negs","nop",
              "orr","orrs","pop","push","rev","rev16","revsh","ror","rors",
              "rsb","rsbs","sbc","sbcs","stmia","stm","str","strb","strh",
              "sub","subs","sxtb","sxth","tst","uxtb","uxth"}
    function=""
    seen=set()
    for line in disassembly.splitlines():
        label=re.match(r"^[a-f0-9]+ <([^>]+)>:",line)
        if label:
            function=label.group(1)
        # Thumb code is printed as one/two four-hex-digit halfwords. Object
        # data appear as eight-digit words plus ASCII and must not be decoded.
        fields=line.split("\t")
        if len(fields)<3 or not re.fullmatch(r"[a-f0-9]{4}(?: [a-f0-9]{4})?",fields[1].strip()):
            continue
        mnemonic=fields[2].split()[0].split(".")[0]
        if not mnemonic:
            continue  # .short exit and .word literal-pool data.
        if mnemonic=="svc" and function=="Reset_Handler":
            continue  # Only the fixture's out-of-region simulator exit.
        assert mnemonic in ordinary or re.fullmatch(r"b(eq|ne|cs|cc|mi|pl|vs|vc|hi|ls|ge|lt|gt|le)?",mnemonic), (function,line)
        seen.add(mnemonic)
    return sorted(seen)


def main():
    sim=setup()
    micros=microchecks(sim)
    (ROOT/"microchecks.json").write_text(json.dumps(micros,indent=2))
    data=json.loads((ROOT.parent/"fir-streaming-pilot.json").read_text())
    filters={name:np.array(item["coefficients"],dtype=np.int16)
             for name,item in data["filters"].items() if not name.startswith("halfband")}
    rng=np.random.default_rng(20261019)
    inputs={"adc":rng.integers(-1024,1024,257,dtype=np.int16),
            "full":rng.choice(np.array([-32768,-32767,-1,0,1,32766,32767],dtype=np.int16),257)}
    rows=[]
    exclusions=[]
    binaries=[]
    for name,h in filters.items():
        print(f"Running {name}",flush=True)
        assert np.array_equal(h,h[::-1])
        for kind,x in inputs.items():
            contracts={"full_int16":32768,"adc11":1024} if kind=="adc" else {"full_int16":32768}
            reference=np.clip(np.convolve(x.astype(np.int64),h.astype(np.int64))[:len(x)]//32768,
                              -32768,32767).astype(np.int16)
            history=x[-(len(h)-1):]
            for optimization in ("-O2","-Os"):
                for block in (1,16,64):
                    for kernel in KERNELS:
                        allowed=[c for c,m in contracts.items() if admitted(kernel,h,m)]
                        for contract in contracts:
                            if contract not in allowed:
                                exclusions.append({"filter":name,"input":kind,"contract":contract,
                                                   "optimization":optimization,"block":block,"kernel":kernel,
                                                   "reason":"32-bit accumulator or folded-product proof fails"})
                        if not allowed:
                            continue
                        identity=f"{name}-{kind}-b{block}-{optimization[1:]}-{kernel}"
                        directory=BUILD/"cases"/identity
                        directory.mkdir(parents=True,exist_ok=True)
                        (directory/"case_data.h").write_text(header(h,x,block))
                        binary=compile_firmware(directory,optimization,kernel)
                        mnemonics=check_instruction_subset((directory/"firmware.disasm").read_text())
                        events,stdout=run(sim,binary)
                        output=decode_output(stdout,"O")
                        retained=decode_output(stdout,"H")
                        assert np.array_equal(output,reference),(identity,"output mismatch")
                        assert np.array_equal(retained,history),(identity,"history mismatch")
                        binary_hash=sha(binary)
                        artifacts={p.name:sha(p) for p in directory.iterdir()
                                   if p.suffix in (".elf",".bin",".h",".disasm",".stdout",".stderr",".map")}
                        binaries.append({"id":identity,"bin_sha256":binary_hash,"files":artifacts,
                                         "output_hash":array_hash(output),"history_hash":array_hash(retained),
                                         "mnemonics":mnemonics})
                        for contract in allowed:
                            rows.append({"filter":name,"input":kind,"contract":contract,
                                         "optimization":optimization,"block":block,"kernel":kernel,
                                         "samples":len(x),"taps":len(h),"binary_id":identity,
                                         "bin_sha256":binary_hash,"outputs_verified":len(output),
                                         "output_mismatches":0,"history_verified":True,
                                         **events,"arm_zero_ws_cycles":arm_zero_ws_cycles(events),
                                         "estimated_cpu_energy_nj":estimated_energy_nj(events)})
    result={
        "status":"exploratory target baseline; no hardware validation or novelty claim",
        "simulator_commit":PIN,"simulator_binary_sha256":sha(sim),
        "simulator_patch_sha256":sha(ROOT/"simulator-console.patch"),
        "compiler":command(["arm-none-eabi-gcc","--version"]).stdout.splitlines()[0],
        "compiler_common_flags":FLAGS,"optimizations":["-O2","-Os"],"lto":False,
        "kernel_source_sha256":sha(ROOT/"kernels.c"),
        "fixture_source_sha256":sha(ROOT/"firmware.c"),
        "startup_source_sha256":sha(ROOT/"startup.s"),
        "coefficient_arrays":{n:h.tolist() for n,h in filters.items()},
        "inputs":{n:{"values":x.tolist(),"sha256":array_hash(x)} for n,x in inputs.items()},
        "energy_model":{
            "source":"https://arxiv.org/html/2301.12806v1#S2.SS5",
            "configuration":"20MHz, prefetch OFF, zero wait states; CPU model only",
            "weights_nj":ENERGY_WEIGHTS,"our_hardware_validation":False},
        "timing_model":{
            "source":"https://support.arm.com/documentation/ddi0432/c/programmers-model/instruction-set-summary?lang=en",
            "formula":"NI + RAM_reads + RAM_writes + Flash_data_reads + 2*taken_branches + BL",
            "type":"Arm-table-based zero-wait-state architectural estimate; single-cycle MUL",
            "our_hardware_validation":False,"raw_ticks_are_cycles":False},
        "microchecks":micros,"rows":rows,"excluded":exclusions,"binaries":binaries,
        "limitations":[
            "Generic scalar C controls, not a claim of best FIR implementations; CMSIS-DSP not yet integrated.",
            "Only six lowpass/bandpass test filters; halfband-specific optimizations excluded.",
            "Shared actual ADC samples under both contracts isolate admissibility from data effects.",
            "Full-scale edge stream separately checks compiled target boundary/saturation behavior.",
            "257 outputs include startup history; initialization/input acquisition/reference/printing excluded.",
            "All recurring state copies, output writes, calls and stream-loop/tail work included.",
            "Shared ADC traces reused across contracts; these are not independent runs.",
            "Single pinned compiler/architecture and two optimization flags; no cross-platform conclusion.",
            "No physical energy measurements; model errors are not guaranteed per-pair bounds.",
        ],
    }
    (ROOT/"results.json").write_text(json.dumps(result,indent=2))
    with (ROOT/"results.csv").open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"rows":len(rows),"binary_executions":len(binaries),"exclusions":len(exclusions),
                      "target_output_comparisons":len(binaries)*257,"mismatches":0}))


if __name__=="__main__":
    main()

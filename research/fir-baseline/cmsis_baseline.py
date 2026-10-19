"""Add unmodified CMSIS-DSP v1.14.4 scalar Q15 baselines to results.json.

Run after experiment.py. Requires the pinned sparse CMSIS checkout and Core
headers described in README.md. Existing generic binary executions are reused.
"""
import csv
import json

import numpy as np

from simulator import (ROOT, BUILD, FLAGS, setup, command, sha, run,
                       arm_zero_ws_cycles, estimated_energy_nj)
from experiment import admitted, array_hash, header, decode_output, check_instruction_subset

DSP_PIN="3a04f817a4380c00ff51f9bcdc6c4e4bb7a18b80"
LIBRARIES={"cmsis64":"arm_fir_q15", "cmsis32":"arm_fir_fast_q15"}


def compile_case(directory,opt,kernel):
    cmsis=BUILD/"cmsis-dsp"
    include=["-I",cmsis/"Include","-I",BUILD/"cmsis-core","-I",directory]
    source=cmsis/"Source"/"FilteringFunctions"/f"{LIBRARIES[kernel]}.c"
    common=["arm-none-eabi-gcc",*FLAGS,opt,*include,"-Wall","-Wextra","-Werror"]
    library_object=BUILD/f"{kernel}-{opt[1:]}-{sha(source)[:12]}.o"
    if not library_object.exists():
        command([*common,"-c",source,"-o",library_object])
    command([*common,f"-DCMSIS_KERNEL={LIBRARIES[kernel]}","-c",ROOT/"cmsis_firmware.c",
             "-o",directory/"firmware.o"])
    startup=BUILD/f"startup-{sha(ROOT/'startup.s')[:12]}.o"
    if not startup.exists():
        command(["arm-none-eabi-gcc",*FLAGS,"-c",ROOT/"startup.s","-o",startup])
    command(["arm-none-eabi-gcc",*FLAGS,"-nostdlib","-T",ROOT/"link.ld","-Wl,--gc-sections",
             f"-Wl,-Map={directory/'firmware.map'}",startup,directory/"firmware.o",library_object,
             "-lgcc","-o",directory/"firmware.elf"])
    command(["arm-none-eabi-objcopy","-O","binary",directory/"firmware.elf",directory/"firmware.bin"])
    (directory/"firmware.disasm").write_text(command([
        "arm-none-eabi-objdump","-d",directory/"firmware.elf"]).stdout)
    return directory/"firmware.bin"


def main():
    cmsis=BUILD/"cmsis-dsp"
    assert command(["git","rev-parse","HEAD"],cmsis).stdout.strip()==DSP_PIN
    assert not command(["git","status","--porcelain"],cmsis).stdout.strip()
    sim=setup()
    result=json.loads((ROOT/"results.json").read_text())
    result["rows"]=[x for x in result["rows"] if not x["kernel"].startswith("cmsis")]
    result["excluded"]=[x for x in result["excluded"] if not x["kernel"].startswith("cmsis")]
    result["binaries"]=[x for x in result["binaries"] if not x["id"].split("-")[-1].startswith("cmsis")]
    added=0
    for name,values in result["coefficient_arrays"].items():
        print(f"CMSIS {name}",flush=True)
        h=np.array(values,dtype=np.int16)
        assert len(h)>=4 and len(h)%2==0 and np.array_equal(h,h[::-1])
        for kind,item in result["inputs"].items():
            x=np.array(item["values"],dtype=np.int16)
            contracts={"full_int16":32768,"adc11":1024} if kind=="adc" else {"full_int16":32768}
            reference=np.clip(np.convolve(x.astype(np.int64),h.astype(np.int64))[:len(x)]//32768,
                              -32768,32767).astype(np.int16)
            for opt in ("-O2","-Os"):
                for block in (1,16,64):
                    for kernel in LIBRARIES:
                        allowed=[c for c,m in contracts.items() if admitted(
                            "direct32" if kernel=="cmsis32" else "direct64",h,m)]
                        for contract in contracts:
                            if contract not in allowed:
                                result["excluded"].append({"filter":name,"input":kind,"contract":contract,
                                    "optimization":opt,"block":block,"kernel":kernel,
                                    "reason":"32-bit accumulator proof fails"})
                        if not allowed:
                            continue
                        identity=f"{name}-{kind}-b{block}-{opt[1:]}-{kernel}"
                        directory=BUILD/"cases"/identity
                        directory.mkdir(parents=True,exist_ok=True)
                        (directory/"case_data.h").write_text(header(h,x,block))
                        binary=compile_case(directory,opt,kernel)
                        mnemonics=check_instruction_subset((directory/"firmware.disasm").read_text())
                        events,stdout=run(sim,binary)
                        output=decode_output(stdout,"O")
                        history=decode_output(stdout,"H")
                        assert np.array_equal(output,reference),(identity,"output mismatch")
                        assert np.array_equal(history,x[-(len(h)-1):]),(identity,"history mismatch")
                        artifacts={p.name:sha(p) for p in directory.iterdir()
                                   if p.suffix in (".elf",".bin",".h",".disasm",".stdout",".stderr",".map")}
                        result["binaries"].append({"id":identity,"bin_sha256":sha(binary),"files":artifacts,
                            "output_hash":array_hash(output),"history_hash":array_hash(history),"mnemonics":mnemonics})
                        added+=1
                        for contract in allowed:
                            result["rows"].append({"filter":name,"input":kind,"contract":contract,
                                "optimization":opt,"block":block,"kernel":kernel,"samples":len(x),"taps":len(h),
                                "binary_id":identity,"bin_sha256":sha(binary),"outputs_verified":len(x),
                                "output_mismatches":0,"history_verified":True,**events,
                                "arm_zero_ws_cycles":arm_zero_ws_cycles(events),
                                "estimated_cpu_energy_nj":estimated_energy_nj(events)})
    result["cmsis_dsp"]={"commit":DSP_PIN,"version":"v1.14.4","loop_unroll_macro":False,
        "core_headers_version":"CMSIS_5 5.9.0","fixture_sha256":sha(ROOT/"cmsis_firmware.c"),
        "source_hashes":{name:sha(cmsis/"Source"/"FilteringFunctions"/f"{symbol}.c")
                         for name,symbol in LIBRARIES.items()},
        "core_header_hashes":{p.name:sha(p) for p in (BUILD/"cmsis-core").glob("*.h")}}
    result["limitations"][0]="Generic C controls plus unmodified CMSIS-DSP v1.14.4 scalar default; no claim of globally best FIR code."
    (ROOT/"results.json").write_text(json.dumps(result,indent=2))
    with (ROOT/"results.csv").open("w",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=list(result["rows"][0]))
        writer.writeheader(); writer.writerows(result["rows"])
    print(json.dumps({"additional_binary_executions":added,"total_binaries":len(result["binaries"]),
                      "total_rows":len(result["rows"]),"excluded":len(result["excluded"]),"mismatches":0}))


if __name__=="__main__":
    main()

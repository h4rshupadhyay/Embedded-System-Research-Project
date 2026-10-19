"""Four-case partial-direct target runner for the pinned FIR simulator fixture.

From the repository root: python research/fir-sharing-probe/partial-direct/run.py
Use --check to inspect prerequisites, or --verify to audit saved raw artifacts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys

HERE = Path(__file__).resolve().parent
SHARING = HERE.parent
BASE = SHARING.parent / "fir-baseline"
sys.path.insert(0, str(BASE))
from simulator import (FLAGS, LABELS, arm_zero_ws_cycles,
                       command, estimated_energy_nj, run, sha)

DESIGN = BASE / "selection-design.json"
FROZEN = SHARING / "results.json"
RESULT = HERE / "results.json"
DESIGN_SHA = "bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f"
FROZEN_SHA = "57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa"
CASES = [(compiler, block) for compiler in ("gcc10", "gcc15") for block in (1, 64)]
COMPILER_FLAGS = [*FLAGS, "-O2", "-Wall", "-Wextra", "-Werror", "-fstack-usage"]


def frozen_data():
    if sha(DESIGN) != DESIGN_SHA or sha(FROZEN) != FROZEN_SHA:
        raise RuntimeError("frozen design or sharing results SHA256 changed")
    design = json.loads(DESIGN.read_text())
    baseline = json.loads(FROZEN.read_text())
    h = design["filters"]["speech_minphase48"]["coefficients"]
    assert len(h) == 48 and sum(map(abs, h[:2])) == 12778
    assert sum(map(abs, h[2:])) == 59731
    return design, baseline, h


def reference(h, x):
    return [max(-32768, min(32767, sum(h[k] * x[n-k]
                                      for k in range(min(n+1, 48))) // 32768))
            for n in range(len(x))]


def expected_history(x):
    return ([0] * 47 + x)[-47:]


def compiler_paths():
    gcc10 = os.environ.get("FIR_GCC10") or shutil.which("arm-none-eabi-gcc")
    gcc15 = Path(os.environ.get("FIR_GCC15") or
                 BASE / "build/toolchains/arm-gnu-toolchain-15.2.rel1-x86_64-arm-none-eabi/bin/arm-none-eabi-gcc")
    return {"gcc10": Path(gcc10).resolve() if gcc10 else None,
            "gcc15": gcc15 if gcc15.exists() else None}


def prerequisites(baseline):
    missing = []
    simulator = Path(os.environ.get("FIR_SIMULATOR") or BASE / "build/thumbulator/sim_main")
    if not simulator.exists() or sha(simulator) != baseline["simulator_sha256"]:
        missing.append("pinned baseline Thumbulator binary")
    paths = compiler_paths()
    identities = {}
    for label, path in paths.items():
        if path is None or not path.exists():
            missing.append(f"{label} Arm compiler")
            continue
        actual = {"sha256": sha(path), "version": command([path, "--version"]).stdout.splitlines()[0]}
        expected = baseline["compilers"][label]
        if actual != expected:
            missing.append(f"{label} compiler identity differs from frozen probe")
        else:
            identities[label] = actual
    return simulator, paths, identities, missing


def firmware(x, block):
    # Exact probe.py stream, marker, and O:/H:/G:/M: fixture. BLOCK moves
    # above our fixed header so its state allocation can be compiled.
    return '''#include "kernel.h"
static struct { uint64_t lo; ProbeState state; uint64_t hi; } storage;
static int16_t source[SAMPLES];
static int16_t destination[SAMPLES+4];
extern void measured(void);
void process_stream(void) {
 for(uint32_t off=0;off<SAMPLES;off+=BLOCK) {
  uint32_t b=SAMPLES-off; if(b>BLOCK)b=BLOCK;
  probe_process(&storage.state,source+off,destination+2+off,b);
 }
}
static void put(char c){*(volatile uint32_t*)0xe0000000=(uint32_t)c;}
static void hex32(uint32_t v){for(int s=28;s>=0;s-=4){unsigned d=(v>>s)&15;put(d<10?'0'+d:'a'+d-10);}}
static void hex16(int16_t v){uint32_t u=(uint16_t)v;for(int s=12;s>=0;s-=4){unsigned d=(u>>s)&15;put(d<10?'0'+d:'a'+d-10);}}
int main(void) {
 for(unsigned i=0;i<SAMPLES;++i)source[i]=input_data[i];
 probe_init(&storage.state); storage.lo=storage.hi=0x5a5a5a5a5a5a5a5aULL;
 destination[0]=destination[1]=destination[SAMPLES+2]=destination[SAMPLES+3]=23130;
 measured(); put('O');put(':');for(unsigned i=0;i<SAMPLES;++i)hex16(destination[i+2]);put('\\n');
 put('H');put(':');for(unsigned i=0;i<TAPS-1;++i){uint64_t v=(uint64_t)probe_get_state(&storage.state,i);hex32((uint32_t)(v>>32));hex32((uint32_t)v);}put('\\n');
 put('G');put(':');hex32((uint32_t)storage.lo);hex32((uint32_t)(storage.lo>>32));hex32((uint32_t)storage.hi);hex32((uint32_t)(storage.hi>>32));
 hex16(destination[0]);hex16(destination[1]);hex16(destination[SAMPLES+2]);hex16(destination[SAMPLES+3]);put('\\n');
 put('M');put(':');hex32(probe_state_bytes());put('\\n');return 0;
}
'''.replace('#include "kernel.h"', f'#define BLOCK {block}\n#define SAMPLES {len(x)}\n'
             + '#include "kernel.h"\n'
             + 'static const int16_t input_data[SAMPLES]={' + ','.join(map(str, x)) + '};')


def check_instruction_subset(disassembly):
    """Same Thumb whitelist and parser as fir-baseline/experiment.py."""
    ordinary = {"adc","adcs","add","adds","adr","and","ands","asr","asrs",
                "bic","bics","bl","blx","bx","cmn","cmp","eor","eors",
                "ldmia","ldm","ldr","ldrb","ldrh","ldrsb","ldrsh","lsl","lsls",
                "lsr","lsrs","mov","movs","mul","muls","mvn","mvns","neg","negs","nop",
                "orr","orrs","pop","push","rev","rev16","revsh","ror","rors",
                "rsb","rsbs","sbc","sbcs","stmia","stm","str","strb","strh",
                "sub","subs","sxtb","sxth","tst","uxtb","uxth"}
    function = ""
    seen = set()
    for line in disassembly.splitlines():
        label = re.match(r"^[a-f0-9]+ <([^>]+)>:", line)
        if label:
            function = label.group(1)
        fields = line.split("\t")
        if len(fields) < 3 or not re.fullmatch(r"[a-f0-9]{4}(?: [a-f0-9]{4})?", fields[1].strip()):
            continue
        mnemonic = fields[2].split()[0].split(".")[0]
        if not mnemonic:
            continue
        if mnemonic == "svc" and function == "Reset_Handler":
            continue
        assert mnemonic in ordinary or re.fullmatch(r"b(eq|ne|cs|cc|mi|pl|vs|vc|hi|ls|ge|lt|gt|le)?", mnemonic), (function, line)
        seen.add(mnemonic)
    return sorted(seen)


def decode(stdout):
    encoded = re.search(r"^O:([a-f0-9]*)$", stdout, re.M)
    history = re.search(r"^H:([a-f0-9]*)$", stdout, re.M)
    guards = re.search(r"^G:([a-f0-9]*)$", stdout, re.M)
    size = re.search(r"^M:([a-f0-9]+)$", stdout, re.M)
    if not all((encoded, history, guards, size)):
        raise AssertionError("missing O:/H:/G:/M: target output")
    values = [int(encoded[1][k:k+4], 16) for k in range(0, len(encoded[1]), 4)]
    values = [v-65536 if v >= 32768 else v for v in values]
    states = [int(history[1][k:k+16], 16) for k in range(0, len(history[1]), 16)]
    states = [v-2**64 if v >= 2**63 else v for v in states]
    return values, states, guards[1], int(size[1], 16)


def verify_output(stdout, h, x, block):
    values, states, guards, size = decode(stdout)
    assert values == reference(h, x), "target outputs differ from arbitrary-precision reference"
    assert states == expected_history(x), "target retained chronological history differs"
    assert guards == "5a5a5a5a" * 4 + "5a5a" * 4, "target state/output guard differs"
    assert size == 2 * (48 + block), "target state allocation differs"
    return size


def raw_events(stderr):
    found = dict(re.findall(r"^([^:\n]+):\s+([0-9]+)\s*$", stderr, re.M))
    events = {key: int(found[label]) for label, key in LABELS.items()}
    assert sum(int(n) for n in re.findall(r"^\s*\d+:\s*(\d+),", stderr, re.M)) == events["instructions"]
    opcode = re.search(r"^16:\s*\d+,\s*\[([^\]]+)\]", stderr, re.M)
    events["mul"] = int(opcode[1].split(",")[13])
    ticks = list(map(int, re.findall(r"(?:raised|cleared) at cycle (\d+)", stderr)))
    assert len(ticks) == 2
    events["raw_tick_delta"] = ticks[1] - ticks[0] - 2
    events["instructions"] -= 1
    events["flash_fetches"] -= 1
    assert all(v >= 0 for v in events.values())
    return events


def stack_diagnostics(directory):
    usage = "\n".join(p.read_text() for p in directory.glob("*.su"))
    return [{"function": match[0], "bytes": int(match[1]), "kind": match[2]}
            for match in re.findall(r"\S+:\d+:\d+:(\S+)\t(\d+)\t(\S+)", usage)]


def compile_case(simulator, compiler, label, block, h, x, edge=False):
    directory = HERE / "build" / "target" / (f"edge-{label}-b{block}" if edge else f"{label}-b{block}")
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "kernel.h", directory / "kernel.h")
    shutil.copyfile(HERE / "kernel.c", directory / "kernel.c")
    (directory / "firmware.c").write_text(firmware(x, block))
    common = [compiler, *COMPILER_FLAGS, f"-DBLOCK={block}", "-I", directory]
    commands = []

    def invoke(args):
        commands.append([str(arg) for arg in args])
        return command(args)

    objects = []
    for source, output in ((directory / "kernel.c", directory / "kernel.o"),
                           (directory / "firmware.c", directory / "firmware.o"),
                           (BASE / "startup.s", directory / "startup.o")):
        invoke([*common, "-c", source, "-o", output])
        objects.append(output)
    elf = directory / "firmware.elf"
    invoke([compiler, *FLAGS, "-nostdlib", "-T", BASE / "link.ld",
            "-Wl,--gc-sections", f"-Wl,-Map={directory / 'firmware.map'}",
            *objects, "-lgcc", "-o", elf])
    invoke([compiler.with_name("arm-none-eabi-objcopy"), "-O", "binary",
            elf, directory / "firmware.bin"])
    disassembly = invoke([compiler.with_name("arm-none-eabi-objdump"), "-d", elf]).stdout
    (directory / "firmware.disasm").write_text(disassembly)
    mnemonics = check_instruction_subset(disassembly)
    match = re.search(r"^[0-9a-f]+ <probe_process>:\n.*?(?=^[0-9a-f]+ <|\Z)",
                      disassembly, re.M | re.S)
    assert match, "probe_process absent from target disassembly"
    (directory / "probe_process.disasm").write_text(match[0])
    events, stdout = run(simulator, directory / "firmware.bin")
    commands.append([str(simulator), "-s", str((directory / "firmware.bin").resolve())])
    assert events == raw_events((directory / "firmware.stderr").read_text())
    state_bytes = verify_output(stdout, h, x, block)
    sizes = invoke([compiler.with_name("arm-none-eabi-size"), elf]).stdout
    (directory / "size.txt").write_text(sizes)
    (directory / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
    artifacts = {p.name: sha(p) for p in sorted(directory.iterdir()) if p.is_file()}
    return {"compiler": label, "filter": "speech_minphase48", "variant": "partial_direct32x2",
            "maximum": 32768, "block": block, "samples": len(x),
            "state_allocation_bytes": state_bytes, "stack_usage": stack_diagnostics(directory),
            "elf_size": sizes, "mnemonics": mnemonics, **events,
            "arm_zero_ws_cycles": arm_zero_ws_cycles(events),
            "estimated_cpu_energy_nj": estimated_energy_nj(events),
            "outputs_verified": len(x), "retained_state_verified": True, "guards_verified": True,
            "directory": str(directory.relative_to(HERE)).replace("\\", "/"),
            "artifacts": artifacts,
            "assembly_review_status": "pending manual inspection of probe_process.disasm"}


def verify_saved(data, h, x):
    assert data["stage"] == "post-audit missing-control"
    assert data["design_sha256"] == DESIGN_SHA and data["sharing_results_sha256"] == FROZEN_SHA
    assert data["timed_input_sha256"] == hashlib.sha256(struct.pack("<257h", *x)).hexdigest()
    assert data["source_sha256"] == source_hashes()
    rows = data["rows"]
    assert {(r["compiler"], r["block"]) for r in rows} == set(CASES)
    edge = edge_input(h)
    edge_rows = data["target_edge_checks"]
    assert {r["compiler"] for r in edge_rows} == {"gcc10", "gcc15"}
    for row in rows + edge_rows:
        assert row["filter"] == "speech_minphase48" and row["variant"] == "partial_direct32x2"
        case_x = edge if row in edge_rows else x
        assert row["maximum"] == 32768 and row["samples"] == len(case_x)
        if row in edge_rows:
            assert row["block"] == 64
        directory = HERE / row["directory"]
        assert directory.resolve().is_relative_to(HERE.resolve())
        for name, digest in row["artifacts"].items():
            assert sha(directory / name) == digest, (directory, name)
        assert (directory / "kernel.c").read_bytes() == (HERE / "kernel.c").read_bytes()
        assert (directory / "kernel.h").read_bytes() == (HERE / "kernel.h").read_bytes()
        assert (directory / "firmware.c").read_text() == firmware(case_x, row["block"])
        assert verify_output((directory / "firmware.stdout").read_text(), h, case_x, row["block"]) == row["state_allocation_bytes"]
        events = raw_events((directory / "firmware.stderr").read_text())
        assert all(row[key] == value for key, value in events.items())
        assert row["arm_zero_ws_cycles"] == arm_zero_ws_cycles(events)
        assert abs(row["estimated_cpu_energy_nj"] - estimated_energy_nj(events)) < 1e-8
        assert row["mnemonics"] == check_instruction_subset((directory / "firmware.disasm").read_text())
    return {"verified_rows": len(rows), "verified_edge_runs": len(edge_rows),
            "verified_outputs": sum(r["outputs_verified"] for r in rows + edge_rows)}


def edge_input(h):
    aligned = [-32768 if c < 0 else 32767 for c in reversed(h)]
    assert sum(c * aligned[47-k] for k, c in enumerate(h)) > 2**31-1
    return [-32768, 32767, 0, -1, 1] * 53 + [0] * 48 + aligned


def source_hashes():
    return {name: sha(HERE / name) for name in
            ("kernel.h", "kernel.c", "run.py", "test_kernel.py", "host_harness.c")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report pinned prerequisites")
    parser.add_argument("--verify", action="store_true", help="audit saved target rows")
    args = parser.parse_args()
    design, baseline, h = frozen_data()
    x = design["inputs"]["adc_raw"][:257]
    assert len(x) == 257
    assert x == baseline["actual_input"]
    if args.verify:
        data = json.loads(RESULT.read_text())
        if len(data["rows"]) != 4 or len(data["target_edge_checks"]) != 2:
            raise RuntimeError("target rows and edge checks are pending; no raw evidence to verify")
        print(json.dumps(verify_saved(data, h, x)))
        return
    simulator, paths, identities, missing = prerequisites(baseline)
    if args.check:
        print(json.dumps({"ready": not missing, "missing": missing, "compiler_identities": identities}, indent=2))
        return
    if missing:
        raise RuntimeError("pinned target environment unavailable: " + "; ".join(missing))
    rows = [compile_case(simulator, paths[label], label, block, h, x)
            for label, block in CASES]
    edges = [compile_case(simulator, paths[label], label, 64, h, edge_input(h), True)
             for label in ("gcc10", "gcc15")]
    data = json.loads(RESULT.read_text())
    data.update({"status": "target rows generated; assembly review pending", "compilers": identities,
                 "simulator_sha256": sha(simulator), "rows": rows,
                 "target_edge_checks": edges,
                 "source_sha256": source_hashes(),
                 "pending_configurations": []})
    RESULT.write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(verify_saved(data, h, x)))


if __name__ == "__main__":
    main()

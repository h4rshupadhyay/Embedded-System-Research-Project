"""Pinned ISS event collection; separate documented timing/energy estimates."""
import hashlib
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
PIN = "c55ea1b1926b792d7aabb7e3495b55a7b69ef134"
SIM_URL = "https://github.com/PicoPET/thumbulator-stm32f0x.git"
FLAGS = ["-mcpu=cortex-m0", "-mthumb", "-std=c11", "-ffreestanding",
         "-fno-builtin", "-ffunction-sections", "-fdata-sections", "-g0"]
LABELS = {"Executed insns": "instructions", "RAM data reads": "ram_reads",
          "RAM writes": "ram_writes", "Flash data reads": "flash_reads",
          "Flash writes": "flash_writes", "Taken branches": "taken_branches",
          "Flash insn reads": "flash_fetches", "BL insns": "bl"}
ENERGY_WEIGHTS = {"nonmul": .964258, "mul": 1.652455, "taken_branches": 2.091986,
                  "ram_reads": 1.109833, "ram_writes": .650563, "flash_reads": .633621}


def command(args, cwd=None):
    p = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True,
                       timeout=60)
    if p.returncode:
        raise RuntimeError(f"{args}\n{p.stdout}\n{p.stderr}")
    return p


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def setup():
    BUILD.mkdir(exist_ok=True)
    directory = BUILD / "thumbulator"
    if not directory.exists():
        command(["git", "clone", "--quiet", SIM_URL, directory])
        command(["git", "checkout", "--quiet", PIN], directory)
    assert command(["git", "rev-parse", "HEAD"], directory).stdout.strip() == PIN
    header = directory/"sim_support.h"
    text = header.read_text()
    header.write_text(text.replace("#define DISABLE_PROGRAM_PRINTING 1",
                                   "#define DISABLE_PROGRAM_PRINTING 0"))
    patch = command(["git", "diff", "--", "sim_support.h"], directory).stdout
    (ROOT/"simulator-console.patch").write_text(patch)
    if not (directory/"sim_main").exists():
        p = command(["make", "board", "COPS=-std=c99 -O2 -fcommon -w"], directory)
        (BUILD/"simulator-build.log").write_text(p.stdout+p.stderr)
    return directory/"sim_main"


def compile_firmware(directory, optimization, kernel):
    directory.mkdir(parents=True, exist_ok=True)
    common = ["arm-none-eabi-gcc", *FLAGS, optimization, "-Wall", "-Wextra", "-Werror"]
    kernel_object=BUILD/f"kernels-{optimization[1:]}-{sha(ROOT/'kernels.c')[:12]}.o"
    if not kernel_object.exists():
        command([*common, "-I", ROOT, "-c", ROOT/"kernels.c", "-o", kernel_object])
    command([*common, "-I", ROOT, "-I", directory, f"-DKERNEL={kernel}", "-c",
             ROOT/"firmware.c", "-o", directory/"firmware.o"])
    startup_object=BUILD/f"startup-{sha(ROOT/'startup.s')[:12]}.o"
    if not startup_object.exists():
        command(["arm-none-eabi-gcc", *FLAGS, "-c", ROOT/"startup.s", "-o", startup_object])
    command(["arm-none-eabi-gcc", *FLAGS, "-nostdlib", "-T", ROOT/"link.ld",
             "-Wl,--gc-sections", f"-Wl,-Map={directory/'firmware.map'}",
             startup_object, directory/"firmware.o", kernel_object,
             "-lgcc", "-o", directory/"firmware.elf"])
    command(["arm-none-eabi-objcopy", "-O", "binary", directory/"firmware.elf", directory/"firmware.bin"])
    disassembly = command(["arm-none-eabi-objdump", "-d", directory/"firmware.elf"]).stdout
    (directory/"firmware.disasm").write_text(disassembly)
    return directory/"firmware.bin"


def run(sim, binary):
    p = command([sim, "-s", binary.resolve()])
    binary.with_suffix(".stdout").write_text(p.stdout)
    binary.with_suffix(".stderr").write_text(p.stderr)
    found = dict(re.findall(r"^([^:\n]+):\s+([0-9]+)\s*$", p.stderr, re.M))
    events = {key: int(found[label]) for label, key in LABELS.items()}
    opcode = re.search(r"^16:\s*\d+,\s*\[([^\]]+)\]", p.stderr, re.M)
    events["mul"] = int(opcode.group(1).split(",")[13])
    assert sum(int(n) for n in re.findall(r"^\s*\d+:\s*(\d+),", p.stderr, re.M)) == events["instructions"]
    ticks = re.findall(r"(?:raised|cleared) at cycle (\d+)", p.stderr)
    assert len(ticks)==2
    events["raw_tick_delta"] = int(ticks[1])-int(ticks[0])
    # Rising marker is not in NI. The closing STR is in NI but excluded from
    # RAM-write events. Remove its one NI and flash fetch. No other fixture
    # setup or output printing occurs in the measured body.
    events["instructions"] -= 1
    events["flash_fetches"] -= 1
    events["raw_tick_delta"] -= 2  # diagnostic only: empty-region marker cost
    assert all(v >= 0 for v in events.values())
    return events, p.stdout


def arm_zero_ws_cycles(e):
    """Arm DDI0432C table for this emitted subset, single-cycle MUL.

    Transfers count individually, including multi-register PUSH/POP/LDM/STM.
    NI counts BL once. All taken control transfers add2, BL one more.
    No peripheral latency, wait states, interrupts, or hardware validation.
    """
    return (e["instructions"] + e["ram_reads"] + e["ram_writes"] + e["flash_reads"]
            + e["flash_writes"] + 2*e["taken_branches"] + e["bl"])


def estimated_energy_nj(e):
    assert e["flash_writes"] == 0
    counters = {**e, "nonmul": e["instructions"]-e["mul"]}
    return sum(counters[key]*weight for key, weight in ENERGY_WEIGHTS.items())


def microchecks(sim):
    cases = {
        "empty": ("", {}, 0),
        "alu5": (".rept 5\nadds r0,#1\n.endr", {"instructions":5}, 5),
        "mul4": (".rept 4\nmuls r0,r1\n.endr", {"instructions":4,"mul":4}, 4),
        "memory3": (".rept 3\nstr r0,[r3]\nldr r2,[r3]\n.endr",
                    {"instructions":6,"ram_reads":3,"ram_writes":3},12),
        "branch3": ("1: subs r0,#1\nbne 1b", {"instructions":6,"taken_branches":2},10),
        "pushpop4": ("push {r0,r1,r2,r3}\npop {r0,r1,r2,r3}",
                     {"instructions":2,"ram_reads":4,"ram_writes":4},10),
        "call": ("bl 1f\nb 2f\n1: bx lr\n2:",
                 {"instructions":3,"taken_branches":3,"bl":1},10),
        "pop_pc": ("bl 1f\nb 2f\n1: push {r4,lr}\npop {r4,pc}\n2:",
                   {"instructions":4,"ram_reads":2,"ram_writes":2,"taken_branches":3,"bl":1},15),
    }
    results = []
    for name, (body, expected, cycles) in cases.items():
        directory=BUILD/"micro"/name
        directory.mkdir(parents=True,exist_ok=True)
        assembly=f""".syntax unified
.cpu cortex-m0
.thumb
.section .vectors,\"a\",%progbits
.word 0x20001ff0
.word Reset_Handler
.section .text,\"ax\",%progbits
.thumb_func
.global Reset_Handler
Reset_Handler:
ldr r6,=0x48000818
movs r7,#1
movs r0,#3
movs r1,#2
ldr r3,=0x20000000
str r7,[r6]
{body}
str r7,[r6,#16]
.short 0xdf01
b .
"""
        (directory/"micro.s").write_text(assembly)
        command(["arm-none-eabi-gcc", *FLAGS, "-nostdlib", "-T", ROOT/"link.ld",
                 directory/"micro.s", "-o", directory/"micro.elf"])
        command(["arm-none-eabi-objcopy", "-O", "binary", directory/"micro.elf", directory/"micro.bin"])
        events, _=run(sim,directory/"micro.bin")
        for key in ("instructions","ram_reads","ram_writes","flash_reads","taken_branches","bl","mul"):
            assert events[key]==expected.get(key,0),(name,key,events,expected)
        assert arm_zero_ws_cycles(events)==cycles,(name,events,cycles)
        results.append({"name":name,"events":events,"expected_arm_cycles":cycles,
                        "arm_estimated_cycles":arm_zero_ws_cycles(events)})
    return results

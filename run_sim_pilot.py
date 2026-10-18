#!/usr/bin/env python3
"""Correctness-gated active-region profiling; periodic idle is metadata only."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
VARIANTS = ("DIRECT", "CIRCULAR", "UNROLLED")
COUNTER_LABELS = {
    "instructions": "Executed insns", "C2": "RAM data reads", "C3": "RAM writes",
    "C4": "Flash data reads", "C5": "Taken branches", "C6": "Mul insns",
}


def run(command):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError(f"Command failed: {' '.join(map(str, command))}\n{result.stderr}")
    return result


def expected_checksum(taps, block, jobs):
    # Full-precision integer convolution, independent of the C kernel arithmetic.
    def sample(index):
        bits = (index * 100) & 0xffff
        return bits if bits < 32768 else bits - 65536

    checksum = 2166136261
    for n in range(block * jobs):
        total = sum(sample(taps + n - k) * (1000 - 10 * k) for k in range(taps))
        bits = (total // 32768) & 0xffff
        checksum = ((checksum ^ bits) * 16777619) & 0xffffffff
    return checksum


def parse_profile(stderr, expected_jobs):
    marker = re.compile(r"TeamPlay: GPIOC\[0\] (raised|cleared) at cycle (\d+),")
    markers = list(marker.finditer(stderr))
    if len(markers) != 2 * expected_jobs:
        raise ValueError("Missing active-region markers; use the patched TeamPlay simulator")
    jobs = []
    for index in range(expected_jobs):
        start, end = markers[2 * index:2 * index + 2]
        if start[1] != "raised" or end[1] != "cleared":
            raise ValueError("Unpaired active-region markers")
        stop = markers[2 * index + 2].start() if index + 1 < expected_jobs else len(stderr)
        summary = stderr[end.end():stop].split("Opcode statistics:", 1)[0]
        counters = {}
        for key, label in COUNTER_LABELS.items():
            found = re.search(rf"^{re.escape(label)}:\s*(\d+)\s*$", summary, re.MULTILINE)
            if found is None:
                raise ValueError(f"Missing interval counter {label}; rebuild the patched simulator")
            counters[key] = int(found[1])
        counters["C1"] = counters.pop("instructions") - counters["C6"]
        active = int(end[2]) - int(start[2])
        if active <= 0 or any(value < 0 for value in counters.values()):
            raise ValueError("Invalid active-region duration or counters")
        jobs.append({"sim_start_cycle": int(start[2]), "sim_end_cycle": int(end[2]),
                     "active_cycles": active, "counters": counters})
    return jobs


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taps", type=positive_int, default=16)
    parser.add_argument("--block", type=positive_int, default=64)
    parser.add_argument("--jobs", type=positive_int, default=4)
    parser.add_argument("--opt", choices=("O0", "O1", "O2", "O3", "Os"), default="O2")
    parser.add_argument("--period-cycles", type=positive_int,
                        help="common logical period; default twice the slowest marked call")
    parser.add_argument("--output", type=Path, default=Path("sim_pilot.json"))
    args = parser.parse_args()
    if args.taps > 100 or args.block > 1024 or args.jobs > 1024:
        parser.error("pilot limits: taps <= 100, block <= 1024, jobs <= 1024")
    # Pilot coefficients stay representable in Q15 in this range.
    if args.output.exists():
        parser.error(f"report already exists: {args.output}; choose a new --output")
    for tool in ("arm-none-eabi-gcc", "arm-none-eabi-objcopy"):
        if not shutil.which(tool):
            parser.error(f"required tool missing: {tool}")
    if not (ROOT / "thumbulator").is_file():
        parser.error("missing ./thumbulator; build and apply patches/thumbulator_stm32f0x.patch")

    try:
        # Fail before profiling if the host equivalence gate is red.
        run(["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_fir.py"])
        variants = []
        expected = expected_checksum(args.taps, args.block, args.jobs)
        with tempfile.TemporaryDirectory(prefix="fir-pilot-") as tmp:
            for variant in VARIANTS:
                elf, binary = Path(tmp) / f"{variant}.elf", Path(tmp) / f"{variant}.bin"
                run(["arm-none-eabi-gcc", "-mcpu=cortex-m0", "-mthumb", "-mfloat-abi=soft",
                     "-" + args.opt, "-fno-builtin", "-falign-loops=4", "-falign-functions=4",
                     "-Wall", "-Wextra", "-Werror", "-nostartfiles", "-T", "stm32f051.ld",
                     "-DSIM_PROFILE", "-DVARIANT_" + variant, f"-DN_TAPS={args.taps}",
                     f"-DM_BLOCK={args.block}", f"-DN_JOBS={args.jobs}",
                     "startup.s", "main.c", "fir.c", "-o", str(elf)])
                run(["arm-none-eabi-objcopy", "-O", "binary", str(elf), str(binary)])
                simulated = run([str(ROOT / "thumbulator"), "-s", str(binary)])
                result = re.search(r"^FIR_RESULT ([0-9a-f]{8}) ([0-9a-f]{8})$",
                                   simulated.stdout, re.MULTILINE)
                if result is None or int(result[1], 16) != args.jobs or int(result[2], 16) != expected:
                    raise ValueError(f"{variant}: Cortex-M0 output checksum failed independent reference")
                jobs = parse_profile(simulated.stderr, args.jobs)
                variants.append({"variant": variant, "completed_jobs": args.jobs,
                                 "checksum": int(result[2], 16), "jobs": jobs,
                                 "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest()})
        slowest = max(job["active_cycles"] for row in variants for job in row["jobs"])
        period = args.period_cycles or 2 * slowest
        if period < slowest:
            raise ValueError(f"period {period} cycles is below the slowest active interval ({slowest})")
        for row in variants:
            for index, job in enumerate(row["jobs"]):
                job.update(release_cycle=index * period, idle_cycles=period - job["active_cycles"])
        report = {
            "schema_version": 1, "physical_measurement": False, "idle_simulated": False,
            "scope": "Sequential marked FIR calls; logical release/idle schedule only. "
                     "No sleep, wake, current waveform, voltage, regulator or source-energy model.",
            "counter_boundary": "Marked call including marker/call overhead; excludes preparation/checksum",
            "period_validation": "Active-region lower bound only; preparation, wake and sleep not scheduled",
            "taps": args.taps, "block": args.block, "jobs": args.jobs,
            "opt": args.opt, "period_cycles": period,
            "compiler": run(["arm-none-eabi-gcc", "--version"]).stdout.splitlines()[0],
            "simulator_sha256": hashlib.sha256((ROOT / "thumbulator").read_bytes()).hexdigest(),
            "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                              for name in ("fir.c", "fir.h", "main.c", "startup.s", "stm32f051.ld",
                                           "run_sim_pilot.py", "patches/thumbulator_stm32f0x.patch")},
            "variants": variants,
        }
        # Exclusive creation protects earlier evidence, including against a concurrent writer.
        with args.output.open("x") as target:
            json.dump(report, target, indent=2)
            target.write("\n")
        print(f"Verified {len(variants)} variants × {args.jobs} jobs; wrote {args.output}")
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()

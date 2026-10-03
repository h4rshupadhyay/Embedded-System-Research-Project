#!/usr/bin/env python3
"""
run_experiments.py
==================
Automated cross-compilation, simulation, and energy estimation script for
the Q15 FIR filter study on the STM32F051 (ARM Cortex-M0) platform.

Experiment matrix: 3 variants × 5 opt-levels × 3 tap counts × 3 block sizes
                 = 135 conditions total (45 per variant).

Nikov 6-Counter Energy Model (48 MHz, 1-wait-state, prefetch ON):
  E_nJ = 0.972565·C1 + 0.652872·C2 + 1.031341·C3
        + 1.037625·C4 + 1.354954·C5 + 2.274651·C6

Counter definitions:
  C1 : Executed non-multiplication instructions
  C2 : SRAM data reads
  C3 : SRAM data writes
  C4 : Flash data reads
  C5 : Taken branches
  C6 : Hardware multiplication instructions

Simulator expected output format (one per line):
  Cycles:      <int>
  C1_Inst:     <int>
  C2_RAM_Rd:   <int>
  C3_RAM_Wr:   <int>
  C4_Flash_Rd: <int>
  C5_Branch:   <int>
  C6_Mul:      <int>
"""

import os
import subprocess
import re
import sys
import pandas as pd
import numpy as np
from scipy.stats import kendalltau, spearmanr

# ─────────────────────────────────────────────────────────────────────────────
# Experiment parameters
# ─────────────────────────────────────────────────────────────────────────────
VARIANTS    = ["VARIANT_DIRECT", "VARIANT_CIRCULAR", "VARIANT_UNROLLED"]
OPT_LEVELS  = ["-O0", "-O1", "-O2", "-O3", "-Os"]
TAPS        = [8, 16, 32]      # filter tap counts
BLOCKS      = [32, 64, 128]    # output block sizes

THUMBULATOR = "./thumbulator"   # path to compiled thumbulator binary
LINKER_SCRIPT = "stm32f051.ld"
OUTPUT_CSV  = "experiment_results.csv"

# ─────────────────────────────────────────────────────────────────────────────
# Nikov energy model coefficients
# ─────────────────────────────────────────────────────────────────────────────
COEFF = {
    "C1": 0.972565,   # non-multiplication instruction energy (nJ each)
    "C2": 0.652872,   # SRAM read energy
    "C3": 1.031341,   # SRAM write energy
    "C4": 1.037625,   # Flash read energy
    "C5": 1.354954,   # taken-branch energy
    "C6": 2.274651,   # hardware multiplication energy
}

def compute_nikov_energy(c1, c2, c3, c4, c5, c6):
    """Return estimated energy in nanojoules using the Nikov 6-counter model."""
    return (COEFF["C1"] * c1 +
            COEFF["C2"] * c2 +
            COEFF["C3"] * c3 +
            COEFF["C4"] * c4 +
            COEFF["C5"] * c5 +
            COEFF["C6"] * c6)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: run a shell command and return stdout
# ─────────────────────────────────────────────────────────────────────────────
def run(cmd, capture=False):
    """Run *cmd* as a shell string. Raises CalledProcessError on failure."""
    if capture:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    else:
        subprocess.run(cmd, shell=True, check=True)

# ─────────────────────────────────────────────────────────────────────────────
# Pre-flight checks
# ─────────────────────────────────────────────────────────────────────────────
def preflight():
    """Verify that required tools are available before starting the sweep."""
    missing = []
    for tool in ["arm-none-eabi-gcc", "arm-none-eabi-objcopy", "arm-none-eabi-size", THUMBULATOR]:
        if subprocess.run(f"which {tool}", shell=True,
                          capture_output=True).returncode != 0:
            missing.append(tool)
    if missing:
        print("ERROR: The following required tools were not found on PATH:")
        for m in missing:
            print(f"  • {m}")
        sys.exit(1)
    if not os.path.exists(LINKER_SCRIPT):
        print(f"ERROR: Linker script '{LINKER_SCRIPT}' not found in cwd.")
        sys.exit(1)
    print("Pre-flight OK — all tools found.\n")

# ─────────────────────────────────────────────────────────────────────────────
# Main experiment sweep
# ─────────────────────────────────────────────────────────────────────────────
def main():
    preflight()

    results = []
    total   = len(OPT_LEVELS) * len(TAPS) * len(BLOCKS) * len(VARIANTS)
    done    = 0

    for opt in OPT_LEVELS:
        for tap in TAPS:
            for block in BLOCKS:
                for variant in VARIANTS:
                    done += 1
                    label = f"[{done:>3}/{total}] {opt} | taps={tap:>3} | block={block:>4} | {variant}"
                    print(label, flush=True)

                    elf = f"firmware_{variant}_{opt.lstrip('-')}_{tap}t_{block}b.elf"
                    bin_file = f"firmware_{variant}_{opt.lstrip('-')}_{tap}t_{block}b.bin"

                    # ── 1. Cross-compile ──────────────────────────────────────
                    cmd_compile = (
                        f"arm-none-eabi-gcc "
                        f"-mcpu=cortex-m0 -mthumb -mfloat-abi=soft "
                        f"{opt} "
                        f"-D{variant} -DN_TAPS={tap} -DM_BLOCK={block} "
                        f"-fno-builtin -falign-loops=4 -falign-functions=4 "
                        f"-Wall -Wextra "
                        f"-T {LINKER_SCRIPT} "
                        f"startup.s main.c fir.c "
                        f"-o {elf} "
                        f"-nostartfiles"
                    )
                    try:
                        run(cmd_compile)
                    except subprocess.CalledProcessError as e:
                        print(f"  COMPILE ERROR — skipping: {e}")
                        continue

                    # ── 2. Extract Code Size & Create Raw Binary ─────────────
                    size_out = run(f"arm-none-eabi-size {elf}", capture=True)
                    # 'size' output: text  data  bss  dec  hex  filename
                    size_match = re.findall(r'\d+', size_out)
                    text_bytes = int(size_match[0]) if size_match else -1

                    try:
                        run(f"arm-none-eabi-objcopy -O binary {elf} {bin_file}")
                    except subprocess.CalledProcessError as e:
                        print(f"  OBJCOPY ERROR — skipping: {e}")
                        if os.path.exists(elf):
                            os.remove(elf)
                        continue

                    # ── 3. Simulate in Thumbulator ISS ────────────────────────
                    try:
                        sim_out = run(f"{THUMBULATOR} {bin_file}", capture=True)
                    except subprocess.CalledProcessError as e:
                        print(f"  SIMULATOR ERROR — skipping: {e}")
                        if os.path.exists(elf):
                            os.remove(elf)
                        if os.path.exists(bin_file):
                            os.remove(bin_file)
                        continue

                    # ── 4. Parse counter fields ───────────────────────────────
                    def parse(pattern, text, default=-1):
                        m = re.search(pattern, text)
                        return int(m.group(1)) if m else default

                    cycles      = parse(r'(\d+)\s+ticks',           sim_out)
                    total_insns = parse(r'Executed insns:\s*(\d+)', sim_out)
                    c6          = parse(r'Mul insns:\s*(\d+)',      sim_out)
                    c1          = (total_insns - c6) if (total_insns >= 0 and c6 >= 0) else -1
                    c2          = parse(r'RAM data reads:\s*(\d+)', sim_out)
                    c3          = parse(r'RAM writes:\s*(\d+)',     sim_out)
                    c4          = parse(r'Flash data reads:\s*(\d+)', sim_out)
                    c5          = parse(r'Taken branches:\s*(\d+)',   sim_out)

                    # ── 5. Compute estimated energy ───────────────────────────
                    energy_nj = compute_nikov_energy(c1, c2, c3, c4, c5, c6)

                    results.append({
                        "Opt":       opt,
                        "Taps":      tap,
                        "Block":     block,
                        "Variant":   variant,
                        "Cycles":    cycles,
                        "CodeSize":  text_bytes,
                        "C1":        c1,
                        "C2":        c2,
                        "C3":        c3,
                        "C4":        c4,
                        "C5":        c5,
                        "C6":        c6,
                        "Energy_nJ": energy_nj,
                    })

                    # Clean up temporary artifacts
                    if os.path.exists(elf):
                        os.remove(elf)
                    if os.path.exists(bin_file):
                        os.remove(bin_file)

    # ── 6. Save results ───────────────────────────────────────────────────────
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✓ Experiment complete! {len(df)} rows saved to '{OUTPUT_CSV}'")

    # ── 7. Quick summary: Kendall τ (Cycles vs Energy) per condition ──────────
    print("\n── Quick Rank-Correlation Summary (Cycles vs Energy_nJ) ──")
    taus = []
    for name, grp in df.groupby(["Opt", "Taps", "Block"]):
        if len(grp) < 2:
            continue
        tau, p = kendalltau(grp["Cycles"].values, grp["Energy_nJ"].values)
        taus.append(tau)
    if taus:
        arr = np.array(taus)
        print(f"  Mean Kendall τ : {arr.mean():.4f}")
        print(f"  Min  Kendall τ : {arr.min():.4f}")
        print(f"  Max  Kendall τ : {arr.max():.4f}")
        print(f"  Conditions with τ < 1.0 (potential rank flips): "
              f"{(arr < 1.0).sum()} / {len(arr)}")
    print("\nRun  'python3 analyze_rankings.py'  for the full statistical analysis.")


if __name__ == "__main__":
    main()

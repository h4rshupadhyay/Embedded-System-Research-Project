# Q15 FIR Energy & Performance Analysis on ARM Cortex-M0

This project provides an automated, reproducible research environment to investigate the **rank-preservation hypothesis** between execution cycle counts and microarchitectural energy consumption on an **ARM Cortex-M0 (Armv6-M / STM32F051)** bare-metal target.

It implements three bit-exact Q15 fixed-point Finite Impulse Response (FIR) filter variants, compiles them across multiple optimization levels and workload dimensions, simulates them cycle-accurately using a modified **Thumbulator** instruction-set simulator with STM32F0 event counters, and calculates energy using the validated **Nikov 6-counter model**.

---

## Table of Contents
1. [Repository Layout](#repository-layout)
2. [Prerequisites & Toolchain Setup](#prerequisites--toolchain-setup)
3. [Building the Instruction Set Simulator (Thumbulator)](#building-the-instruction-set-simulator-thumbulator)
4. [Manual Firmware Build & Inspection](#manual-firmware-build--inspection)
5. [Automated Experiment Sweep](#automated-experiment-sweep)
6. [Statistical & Rank-Flip Analysis](#statistical--rank-flip-analysis)
7. [Nikov 6-Counter Energy Model](#nikov-6-counter-energy-model)
8. [Summary of Key Findings](#summary-of-key-findings)

---

## Repository Layout

```
.
├── flags.mk               # Architecture, determinism, and 32-bit alignment compiler flags
├── stm32f051.ld           # Linker script mapping .text to Flash and .data/.bss to SRAM
├── startup.s              # Bare-metal Cortex-M0 vector table (MSP + Reset_Handler)
├── fir.h                  # Header file defining Q15 FIR prototypes
├── fir.c                  # Three FIR implementations (Direct, Circular, 4x Unrolled)
├── main.c                 # Testbench harness dispatching variants and buffer sizes
├── Makefile               # Convenience Makefile for compiling FIR firmware variants
├── run_experiments.py     # Automated sweep over 135 conditions -> experiment_results.csv
├── analyze_rankings.py    # Statistical evaluation script -> rank_flip_analysis.csv
├── thumbulator            # Compiled instruction-set simulator binary (from thumbulator-stm32f0x)
├── thumbulator-stm32f0x/  # Source code for the modified Thumbulator ISS
├── experiment_results.csv # Raw simulation results (135 conditions)
├── rank_flip_analysis.csv # Pairwise comparisons and cycle-gap threshold analysis
└── FINDINGS.md            # Detailed documentation of empirical findings & root-cause analysis
```

---

## Prerequisites & Toolchain Setup

### 1. Cross-Compiler Toolchain (`arm-none-eabi-gcc`)

You need the official Arm GNU toolchain to compile bare-metal Armv6-M (Thumb) binaries:

* **Ubuntu / Debian**:
  ```bash
  sudo apt-get update
  sudo apt-get install -y gcc-arm-none-eabi binutils-arm-none-eabi make git python3 python3-pip libssl-dev
  ```
* **macOS (Homebrew)**:
  ```bash
  brew install --cask gcc-arm-embedded
  brew install make git python3 openssl
  ```
* **Windows**:
  Download and run the installer from the [Arm Developer GNU Toolchain Downloads](https://developer.arm.com/downloads/-/arm-gnu-toolchain) (make sure to select "Add path to environment variables").

Verify the toolchain installation:
```bash
arm-none-eabi-gcc --version
```

### 2. Python Environment Setup

Install the required statistical and data processing packages:

```bash
pip3 install --user "numpy<2" pandas scipy matplotlib
```

> [!NOTE]
> Pinning `numpy<2` (e.g. `1.26.4`) avoids C-extension ABI conflicts with Linux distribution packages (`numexpr`, `bottleneck`).

---

## Building the Instruction Set Simulator (Thumbulator)

The modified **Thumbulator** ISS models the microarchitecture of the STM32F0 Cortex-M0, including bus stalls, flash wait states, branch latencies, and event counters.

```bash
# 1. Clone the repository
git clone https://github.com/PicoPET/thumbulator-stm32f0x.git
cd thumbulator-stm32f0x

# 2. Switch to the teamplay-D4.5 branch
git checkout teamplay-D4.5

# 3. Build the simulator binary
make

# 4. Copy the binary to the project root
cp sim_main ../thumbulator
cd ..
```

> [!TIP]
> This repository already includes the required patch in `sim_support.h`, `exmemwb_branch.c`, and `exmemwb_arith.c` to enable unconditional instruction counting, hardware `MULS` tracking ($C_6$), and stat reporting on branch-to-self termination (`while(1)`).

---

## Manual Firmware Build & Inspection

To manually build individual firmware binaries using the [`Makefile`](./Makefile):

```bash
# Build all three FIR variants at default -O2 (16 taps, 64 block size)
make clean && make

# Build with custom optimization level and filter dimensions:
make OPT=-O3 N_TAPS=32 M_BLOCK=128

# Inspect binary section sizes:
make size

# Inspect assembly disassembly of an implementation:
make disasm ELF=fir_unrolled.elf
```

To run a single binary in the simulator manually:
```bash
# Convert ELF to flat binary image:
arm-none-eabi-objcopy -O binary fir_unrolled.elf fir_unrolled.bin

# Execute in Thumbulator:
./thumbulator fir_unrolled.bin
```

---

## Automated Experiment Sweep

The [`run_experiments.py`](./run_experiments.py) script automates the full test matrix:
* **3 Algorithm Variants**: Direct-Loop, Circular-Buffer, 4x Loop-Unrolled
* **5 Optimization Levels**: `-O0`, `-O1`, `-O2`, `-O3`, `-Os`
* **3 Filter Tap Configurations**: 8, 16, 32 taps
* **3 Output Block Sizes**: 32, 64, 128 samples
* **Total**: $3 \times 5 \times 3 \times 3 = 135$ automated runs

Execute the sweep:
```bash
python3 run_experiments.py
```

This generates [`experiment_results.csv`](./experiment_results.csv) containing cycle counts, code sizes, individual microarchitectural event counters ($C_1 \dots C_6$), and computed Nikov energy ($E_{\text{nJ}}$).

---

## Statistical & Rank-Flip Analysis

Once `experiment_results.csv` is generated, run the statistical evaluator:

```bash
python3 analyze_rankings.py
```

This script computes:
1. **Global Rank Correlations**: Kendall's $\tau_b$ and Spearman's $\rho$.
2. **Top-1 Agreement**: Percentage of conditions where the fastest variant by cycle count is also the most energy-efficient.
3. **Pairwise Rank-Flip Rate**: Frequency of order reversals ($t_A < t_B$ but $E_A > E_B$) across all conditions.
4. **Cycle-Gap Threshold ($\Delta t$) Table**: How the inversion probability scales as the execution time difference $\Delta t = |t_A - t_B| / \min(t_A, t_B)$ increases.
5. **Optimization Level Pivot Summary**: Mean energy breakdown per variant across compiler flags.

---

## Nikov 6-Counter Energy Model

Energy ($E_{\text{nJ}}$) is calculated using the Nikov et al. linear regression model calibrated for the STM32F0 running at 48 MHz with 1 flash wait state and prefetch enabled:

$$E_{\text{nJ}} = 0.972565 \cdot C_1 + 0.652872 \cdot C_2 + 1.031341 \cdot C_3 + 1.037625 \cdot C_4 + 1.354954 \cdot C_5 + 2.274651 \cdot C_6$$

| Counter | Architectural Description | Energy Weight |
|---|---|:---:|
| **$C_1$** | Executed non-multiplication instructions ($\text{Total} - C_6$) | $0.972565\text{ nJ}$ |
| **$C_2$** | SRAM data read accesses | $0.652872\text{ nJ}$ |
| **$C_3$** | SRAM data write accesses | $1.031341\text{ nJ}$ |
| **$C_4$** | Flash memory data reads | $1.037625\text{ nJ}$ |
| **$C_5$** | Taken branch instructions | $1.354954\text{ nJ}$ |
| **$C_6$** | Hardware multiplication instructions (`MULS`) | $2.274651\text{ nJ}$ |

---

## Summary of Key Findings

* **Near-Perfect Monotonicity**: Global Kendall's $\tau_b = \mathbf{0.9836}$ ($p = 4.38 \times 10^{-64}$) and Spearman's $\rho = \mathbf{0.9991}$.
* **100% Top-1 Agreement**: The fastest implementation was always the most energy-efficient across all 45 test conditions.
* **Rank-Flip Boundary ($\Delta t \le 0.06\%$)**: Only 2 rank reversals occurred out of 135 pairwise comparisons (**1.48%** overall flip rate). Both occurred under `-O3` where execution times differed by only 6 cycles ($\Delta t \le 0.061\%$).
* **Safe Decision Margin**: For any cycle gap $\Delta t > 0.1\%$, the rank-flip probability is **0.00%**, confirming that clock cycles are an exceptionally reliable proxy for energy outside of sub-0.1% near-ties.
* **Top Performing Implementation**: `VARIANT_UNROLLED` achieved the lowest execution cycles and lowest energy across all optimization levels (up to **29.3% lower energy** than direct convolution).

For in-depth analysis, event counter breakdowns, and trade-off tables, see [`FINDINGS.md`](./FINDINGS.md).

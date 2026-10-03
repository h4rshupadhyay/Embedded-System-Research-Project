# Experimental Findings: Q15 FIR Performance & Energy Analysis on ARM Cortex-M0

This repository contains the bare-metal implementations, simulation pipeline, and statistical evaluations for Q15 FIR filter optimization on an ARM Cortex-M0 (STM32F051) target using the Nikov 6-counter energy model.

---

## 1. Quick Summary of Results

* **Total Evaluated Configurations**: 135 runs (3 variants × 5 optimization levels × 3 tap counts × 3 block sizes).
* **Global Correlation (Cycles vs. Energy)**:
  * **Kendall’s $\tau_b$**: **0.9836** ($p = 4.38 \times 10^{-64}$)
  * **Spearman’s $\rho$**: **0.9991** ($p = 5.59 \times 10^{-185}$)
* **Top-1 Agreement**: **100.0% (45 / 45 conditions)** — The fastest implementation in cycles was always the most energy-efficient.
* **Pairwise Rank Flips**: **2 out of 135 pairs (1.48%)**.
* **Cycle-Gap Inversion Threshold**: Both rank reversals were confined to **$\Delta t \le 0.061\%$** (6 clock cycles difference out of ~9,800 to 35,000 cycles). For any difference $\Delta t > 0.1\%$, the flip rate was **0.00%**.

---

## 2. Generated Data Files

| File | Description |
|---|---|
| [`experiment_results.csv`](./experiment_results.csv) | Raw dataset containing cycle counts, code size, individual event counters ($C_1 \dots C_6$), and Nikov energy ($E_{\text{nJ}}$) for all 135 runs. |
| [`rank_flip_analysis.csv`](./rank_flip_analysis.csv) | Pairwise comparison dataset recording relative cycle gap ($\Delta t$) and rank inversion boolean flag for all 135 pairs. |
| [`flags.mk`](./flags.mk) | Compiler flags enforcing determinism and 32-bit flash alignment. |
| [`stm32f051.ld`](./stm32f051.ld) | Memory linker script mapping code to Flash and data to SRAM. |
| [`startup.s`](./startup.s) | Bare-metal Cortex-M0 vector table and reset handler. |
| [`fir.h`](./fir.h) / [`fir.c`](./fir.c) | Q15 FIR filter implementations (`VARIANT_DIRECT`, `VARIANT_CIRCULAR`, `VARIANT_UNROLLED`). |
| [`main.c`](./main.c) | Testbench harness dispatching active variant and workload dimensions via macros. |
| [`run_experiments.py`](./run_experiments.py) | Python automation script executing the 135-condition sweep. |
| [`analyze_rankings.py`](./analyze_rankings.py) | Statistical evaluation script computing rank correlation, Top-1 agreement, and flip frequency. |

---

## 3. Pairwise Rank Flips vs. Execution Gap Threshold

| Relative Cycle Gap $\Delta t$ | Comparisons in Window | Inversions (Flips) | Flip Rate |
|---|:---:|:---:|:---:|
| $\le 0.01$ (1%) | 6 | 2 | **33.33%** |
| $\le 0.02$ (2%) | 7 | 2 | **28.57%** |
| $\le 0.05$ (5%) | 19 | 2 | **10.53%** |
| $\le 0.10$ (10%) | 36 | 2 | **5.56%** |
| $\le 0.20$ (20%) | 81 | 2 | **2.47%** |
| All Comparisons | 135 | 2 | **1.48%** |

---

## 4. Case Study: Root Cause of the Two Rank Flips

Both inversions occurred under **`-O3`** between `VARIANT_DIRECT` and `VARIANT_CIRCULAR`:

1. **`-O3`, 8 taps, 64 block**:
   * `CIRCULAR`: 9,804 cycles, **10,096.47 nJ**
   * `DIRECT`: 9,810 cycles, **9,956.81 nJ** (Energy winner despite taking 6 more cycles; $\Delta t = 0.0612\%$)
2. **`-O3`, 16 taps, 128 block**:
   * `CIRCULAR`: 34,908 cycles, **36,136.32 nJ**
   * `DIRECT`: 34,914 cycles, **35,476.98 nJ** (Energy winner despite taking 6 more cycles; $\Delta t = 0.0172\%$)

### Why the Flips Occurred
* On the Cortex-M0, single-cycle hardware multiplication (`MULS`) takes 1 clock cycle—the exact same duration as a simple add (`ADDS`) or move (`MOVS`).
* However, in the physical Nikov energy model, hardware multiplication draws **2.275 nJ per operation** (compared to **0.973 nJ** for non-multiplication instructions and **0.653 nJ** for SRAM reads).
* In both cases, compiler optimization differences led `CIRCULAR` to execute 28 more hardware multiplies and additional SRAM writes. Because $\Delta t$ was under 0.1%, the higher energy cost of the multiply unit dominated the negligible cycle savings, causing an energy rank reversal.

---

## 5. Variant Comparison: Energy by Optimization Level

Mean energy (nJ) across all tap counts and block sizes:

| Optimization Level | `VARIANT_CIRCULAR` | `VARIANT_DIRECT` | `VARIANT_UNROLLED` | Energy Winner |
|:---:|:---:|:---:|:---:|:---:|
| **`-O0`** | 63,427.5 nJ | 78,557.3 nJ | **60,897.7 nJ** | `UNROLLED` (-22.5%) |
| **`-O1`** | 24,273.5 nJ | 27,107.1 nJ | **22,162.9 nJ** | `UNROLLED` (-18.2%) |
| **`-O2`** | 24,417.1 nJ | 28,311.9 nJ | **21,055.4 nJ** | `UNROLLED` (-25.6%) |
| **`-O3`** | 24,382.7 nJ | 21,771.0 nJ | **21,021.0 nJ** | `UNROLLED` (-3.4%) |
| **`-Os`** | 29,537.5 nJ | 33,927.9 nJ | **23,997.7 nJ** | `UNROLLED` (-29.3%) |

`VARIANT_UNROLLED` achieved the highest performance and lowest energy across all conditions.

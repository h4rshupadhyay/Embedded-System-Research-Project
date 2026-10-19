# FIR target-baseline findings

19 October 2026. This completes the initial working-baseline phase. Results are from target instruction simulation with explicit timing and CPU-energy estimates; no hardware measurements or new-algorithm claim are made.

## Main result

Input-range contracts can change the cheapest **admitted** implementation even when the actual input samples are identical. In the tested 256-tap bandpass case, a full-int16 contract requires a wide accumulator, while an ADC11 guarantee admits a 32-bit accumulator. At block64, the best admitted implementation's estimated CPU energy decreases by 22.74% with `-O2` and 23.87% with `-Os`. All outputs remain identical to the same full reference. This is a contract-dependent code-selection result within the tested set, not energy saved merely by relabeling an unchanged binary.

The established CMSIS-DSP implementations were included. The result does not establish that input-range analysis, narrowing, symmetry or autotuning is novel. It supplies a working empirical foundation and a possible research direction; significance and originality relative to the closest studies still require justification.

## What now runs

[The fixture](fir-baseline/README.md) contains five scalar C controls and two unmodified library controls:

| Implementation | Product arithmetic | Accumulator | Admission |
|---|---|---|---|
| direct64 | 32-bit, exact 16×16 product | 64-bit | General input/coefficient contract |
| direct32 | 32-bit | 32-bit | Every prefix proved in range |
| fold64 | 32-bit, after a wide pre-add | 64-bit | Symmetry and product-range proof |
| fold32 | 32-bit, after a wide pre-add | 32-bit | Symmetry, product and accumulator proofs |
| fold64_wide | 64-bit product | 64-bit | General symmetric reference; diagnostic wide-product control |
| CMSIS standard | Official scalar `arm_fir_q15` | 64-bit | Its supported even-tap contract |
| CMSIS fast | Official scalar `arm_fir_fast_q15` | 32-bit | Same additional no-overflow proof |

The bank uses six even-length lowpass/bandpass filters at 64,128,256 taps. Compiler: Arm GCC 10.3.1, Cortex-M0 Thumb, `-O2` and `-Os`, no LTO. Block sizes are 1,16,64; 257 samples exercise tail blocks. All per-call state copying, output writes, stream-loop control and calls/returns are included. Setup, initial zeroing, input acquisition and result printing are excluded. Halfband-specific performance and other CMSIS build options are outside this pilot.

The numerical reference remains `clip_int16(floor(Σh[i]x[n-i]/32768))`. Fixed coefficients, all samples and all outputs are preserved. This is the same contract throughout; there is no approximate filtering.

## Verification evidence

- Five host test methods pass, including stream partitioning, history/canary checks, signed extrema, negative floor division, saturation, odd centers and safety gating. The C library runs with undefined-behavior sanitization. One regression method protects disassembly parsing from treating coefficient data as instructions.
- Eight assembly microchecks pass for known instruction/transfer/branch counts and the declared Arm-table timing formula.
- **486 distinct target binaries executed**, including 138 library-control binaries. **124,902 target outputs** and every retained history matched the independent full-convolution reference, with zero mismatches. These comparisons reuse 3,084 filter/input/output reference positions; they are not independent random workloads.
- **720 valid comparison rows** form 108 groups. Another **36 rows are explicitly excluded by safety proofs**, not silently timed as valid implementations. Shared ADC traces are reused across the two contracts.
- ELF, binary, linker map, disassembly, generated input and raw stdout/stderr are retained under `fir-baseline/build/cases/`; checksums are recorded in [results.json](fir-baseline/results.json). The flattened table is [results.csv](fir-baseline/results.csv); derived proofs and summaries are in [analysis.json](fir-baseline/analysis.json).

These are C-level arithmetic arguments plus host/target differential checks, not a formal proof of the compiler or ISS for every possible input.

## Simulator correction to the original plan

The pinned simulator's raw tick counter is unsuitable as verified Cortex-M0 timing. Its POP expression has a precedence error, and taken branch/link costs differ from the Arm zero-wait-state table. Actual microchecks confirm the discrepancy:

| Assembly body | Arm-table estimate | Raw tick diagnostic |
|---|---:|---:|
| Five ordinary ALU operations | 5 | 5 |
| Four MUL operations | 4 | 4 |
| Three store/load pairs | 12 | 12 |
| Three-iteration decrement/conditional-branch loop | 10 | 8 |
| PUSH/POP of four registers | 10 | 7 |
| BL, return and branch | 10 | 7 |
| BL, PUSH and PC-restoring POP, branch | 15 | 10 |

The empty-region check is zero after marker subtraction. No simulator timing handler was patched; its sole source change enables output printing outside measurement. [Microcheck records](fir-baseline/microchecks.json), [source/documentation audit](fir-simulator-audit.md).

For the emitted integer instruction subset, use the separate estimate:

`cycles = NI + SRAM_reads + SRAM_writes + Flash_data_reads + 2*taken_branches + BL`.

Individual transfers include the registers of PUSH/POP/LDM/STM. This matches the [Arm DDI0432C zero-wait-state instruction table](https://support.arm.com/documentation/ddi0432/c/programmers-model/instruction-set-summary?lang=en) under the stated single-cycle multiplier assumption. It is **not hardware-validated STM32 timing**, and it is not claimed to reproduce Nikov's separate event-to-time model. The executed binaries were screened against the supported instruction subset. Special-register operations, exceptions and peripheral latency in the measured body are excluded.

For energy, the verified events feed the explicitly identified **20 MHz, prefetch OFF, zero wait states** coefficient set from [Nikov et al., Table 2](https://arxiv.org/html/2301.12806v1). Raw ticks are not an input to this energy calculation. The complete equation and counter mapping are in the fixture README. The simulator's unused timer-frequency macro does not clock hardware or validate a 20 MHz implementation. These are CPU model estimates, excluding board/peripheral energy; the source model's error is not a guaranteed per-pair error bound for this experiment.

## Result 1: strong baselines matter

For the 128-tap lowpass, identical ADC samples, `-O2`, block64, all listed implementations satisfy even the full-int16 contract:

| Implementation | Dynamic MUL instructions | Arm-table cycles | Modeled CPU energy/output (µJ) |
|---|---:|---:|---:|
| direct64 | 32,896 | 842,475 | 3.203 |
| direct32 | 32,896 | 474,718 | 1.866 |
| CMSIS standard | 32,896 | 730,115 | 2.792 |
| CMSIS fast | 32,896 | 413,169 | 1.634 |
| fold64 | 16,448 | 503,924 | 1.921 |
| fold32 | 16,448 | 385,387 | 1.487 |
| Wide-product folded control | 98,688 | 1,396,302 | 5.403 |

Counts/cycles cover the whole 257-output region; energy is divided by 257. Fold32 is about 9.00% below CMSIS fast under this model/configuration. This is a measured-model comparison of specific code, not a new symmetry optimization or a claim that default scalar CMSIS is the best achievable production code. The difference does not inherit a physical confidence interval from the source model.

## Result 2: isolate the input contract from the signal

For the 256-tap bandpass, the integer coefficient absolute sum is 74258. The full-int16 sufficient prefix bound is `32768*74258=2433286144`, exceeding `INT32_MAX`. More than failure of a sufficient bound is available: choosing a full-range input window with the coefficient signs produces a sum of **2433249006**, which also exceeds `INT32_MAX`. A universal 32-bit exact accumulator is therefore unsuitable for that full input contract.

Under ADC11, the bound becomes `1024*74258=76040192`, safely within int32. The folded pre-add/product proof also holds. Both contracts are tested using **the very same ADC samples and binaries** for shared eligible implementations. The new guarantee admits additional implementations; it does not alter coefficients, precision, samples or output bits.

| Contract, `-O2`, block64 | Best admitted candidate in this experiment | Modeled CPU energy/output |
|---|---|---:|
| Full int16 | fold64 | 3.763 µJ |
| ADC11 | fold32 | 2.907 µJ |

The modeled reduction is 22.74%. Across the six matched bandpass256 block/flag cases it ranges from **14.35% to 23.87%**. The best candidate changes in **6 of the 36 matched ADC contract comparisons**; the other filters already admit int32 under the full domain. This is a bounded result, not a universal advantage of narrower input contracts.

## Result 3: source-level product counts can hide helper work

The general wide-product folded C control computes half as many logical FIR products, but this toolchain lowers each to a software wide multiply containing six MUL instructions. Thus the lowpass128 run executes 98,688 MULs, compared with 32,896 in direct64: **three times as many target MULs despite half as many source FIR products**.

The product-range-certified fold64 control uses 16,448 MULs instead. This explains the large difference between the two folded controls. It does not establish that all wide multiplication or all folded FIR code behaves this way. The general wide-product version is a diagnostic control; an improvement against it alone would be a weak optimization claim. The important comparisons include product-safe folding and the production library.

## Negative result and research meaning

The minimum Arm-table timing and minimum modeled-energy candidates agree in **all 108 groups**. This pilot therefore supplies no evidence that selecting the fastest candidate increases estimated energy. There is no reason to revive the earlier proxy-failure framing on these results.

The strongest supported direction is an **empirical study of correctness-constrained FIR implementation selection**, with intermediate width and guaranteed input range made explicit. Its ingredients are established; the potential contribution is substantive new controlled evidence, explanations and a reproducible artifact. This baseline phase alone does not secure novelty or publication significance.

Before treating it as the final paper contribution, position these interactions against the closest processor-aware FIR/word-length studies, justify application contracts and filters, and test whether the findings persist beyond this one compiler/configuration and default library path. Full-range assumptions, low observed amplitudes and physical energy must remain distinct. [Next-direction literature screen](fir-next-direction-screen.md).

![Illustrative model estimates](fir-baseline/energy-comparison.png)

The plot is generated directly from saved results; [SVG](fir-baseline/energy-comparison.svg), [plot/analysis script](fir-baseline/analyze.py).

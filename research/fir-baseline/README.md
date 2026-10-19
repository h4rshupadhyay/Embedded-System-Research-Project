# Exact FIR target baseline experiment

This is an **exploratory research fixture**, not a production DSP library. It answers whether arithmetic contracts change the most efficient valid implementation among the tested alternatives. No new FIR algorithm, hardware measurements or universal implementation optimum is claimed.

## Numerical contract and alternatives

For every input sample, accumulate the exact integer FIR sum and emit `clip_int16(floor(sum/32768))`. Coefficients are fixed signed 16-bit integers; history initially contains zeros. Every output and the final retained history are checked against independent unfolded convolution. Negative division, saturation, signed extrema, odd centers and block partitions are tested on the host with undefined-behavior sanitization.

The scalar C controls are `direct64`, `direct32`, `fold64`, `fold32`, and `fold64_wide`. The first four use 32-bit products; `fold64_wide` deliberately represents a general wide-product control for symmetric pre-additions. It is a diagnostic about compiler lowering, not a strong competing optimization. Folded variants require exactly symmetric coefficients. A folded pre-addition is always at least 32 bits.

Let M bound the absolute value of every admitted input and A be the integer coefficient absolute sum. Admit a 32-bit accumulator only if `M*A <= INT32_MAX`. This bounds every prefix, not just observed final results. Admit a folded 32-bit product only if each paired coefficient satisfies `2*M*abs(h[i]) <= INT32_MAX`. The center product, if any, uses the ordinary 16×16 bound. Wider references remain available when a proof fails. See [kernels.h](kernels.h).

The added production controls are unmodified CMSIS-DSP v1.14.4 `arm_fir_q15` and `arm_fir_fast_q15`. The fast version is admitted only with the same proven 32-bit safety condition. These are the default scalar paths with `ARM_MATH_LOOPUNROLL` undefined, not an exhaustive sweep of CMSIS build options. Their even-tap constraint is respected. The measured bank is symmetric, so lag-order coefficients equal the reversed coefficient array expected by CMSIS. Library descriptors are initialized in RAM before measurement; all recurring library work is measured.

## Fixed experiment

Six lowpass/bandpass test FIRs use 64,128,256 taps. Integer coefficient arrays come from the earlier numerical pilot and are saved verbatim in results.json. Halfband-specific performance is excluded because its zeros and odd lengths need specialized baselines.

Use 257 samples, block sizes 1,16,64, and GCC `-O2`/`-Os`, Cortex-M0/Thumb, without LTO. The nonmultiple length exercises final short blocks. All kernels are compiled separately from the fixture to prevent coefficient constant folding from silently changing the comparison. These are complete finite streams with initial history, not warmed steady-state measurements.

The same synthetic signed-11-bit ADC samples are considered under both an ADC11 guarantee and a full-int16 contract. Wide valid binaries and their event traces are shared between those contract rows. This isolates the effect of admissibility from changes in actual data. A separate full-range edge stream exercises compiled-target saturation and signed-boundary behavior. Coefficients/code are in Flash; input buffers, state and outputs are in SRAM.

The measurement includes the outer stream loop, kernel calls/returns, input-to-state copies, all FIR work, output writes, tail blocks and recurring history copies. Fixture initialization, initial zeroing, input acquisition/preparation, reference calculation and UART output are excluded. This is CPU filtering cost, not sensor acquisition or board energy.

## Simulator and measurement scope

Pinned PicoPET Thumbulator commit: `c55ea1b1926b792d7aabb7e3495b55a7b69ef134`. Build it with host GCC `-std=c99 -O2 -fcommon -w`. `-fcommon` accommodates upstream global hook declarations; it does not change the target program. The sole simulator source patch enables console printing. No instruction behavior or timing handlers are patched. [Patch](simulator-console.patch).

Start/stop use the upstream GPIO marker interface with prefetch disabled (`-s`, no `-pw` or `-pb`). The assembly wrapper prepares marker registers before the measured region, calls `process_stream`, and closes the region after its return. The closing marker's one instruction and Flash fetch are removed. Raw ticks are retained only as diagnostics, subtracting the measured empty-marker overhead. Actual output/history printing happens after counters stop.

The linker budgets 64 KiB Flash and 8 KiB SRAM; the stack starts below `0x20002000`. The upstream simulator itself has a larger memory window. This linker budget is not a hardware memory-protection implementation.

### Timing

Do not use upstream raw ticks as Cortex-M0 cycles. The [audit](../fir-simulator-audit.md) records POP precedence and branch-cost problems. Eight assembly microchecks verify scoped instruction, transfer, multiply and branch counts against known programs.

For the emitted, statically checked integer instruction subset, use the explicit Arm DDI0432C zero-wait-state table:

`estimated_cycles = NI + SRAM_reads + SRAM_writes + Flash_data_reads + 2*taken_branches + BL`.

Each byte/halfword/word transfer counts once, including each register transfer of PUSH/POP/LDM/STM. The branch term includes PC-restoring POP; BL gets one additional cycle. MUL is the STM32F0 single-cycle implementation. Flash writes, exceptions, peripherals in the body, special-register operations and unhandled instructions are outside this model. The fixture's exit is outside the measured body. Both generic and CMSIS disassemblies are screened by the instruction whitelist.

This is an **Arm-table-based architectural timing estimate**, not hardware-validated STM32 timing or a reproduction of Nikov's unpublished event-to-time reconstruction. Microchecks establish consistency with documentation, not physical timing accuracy.

### Energy

Apply Nikov et al., Table 2, configuration `[20 MHz, prefetch OFF, wait states 0]`:

`E[nJ] = .964258*(NI-MUL) + 1.652455*MUL + 2.091986*taken_branches + 1.109833*SRAM_reads + .650563*SRAM_writes + .633621*Flash_data_reads`.

[Primary model paper](https://arxiv.org/html/2301.12806v1). Counters overlap intentionally: loads and branches are also non-MUL instructions. Instruction fetches are not Flash data reads. These estimates do not use raw ticks. The paper's validation error is not a guaranteed bound for these FIRs or pairwise comparisons. This project has no independent hardware calibration or measurements.

## Reproduce

Requirements already used locally: Python 3.10, NumPy, host GCC 11.4, Arm GCC 10.3.1 and binutils, Git, Make, and the host OpenSSL libraries needed by upstream. Exact compiler text and source/data hashes are recorded in results.json.

1. Run `python -m unittest discover -s research/fir-baseline -p 'test_*.py' -v` from the repo root.
2. Run `python research/fir-baseline/experiment.py`. It builds the pinned simulator if absent, verifies the eight assembly cases, and writes the generic-control results.
3. Obtain the pinned CMSIS sources/headers using `python research/fir-baseline/fetch_cmsis.py`, then run `python research/fir-baseline/cmsis_baseline.py` to append library comparisons. The generic executions are reused rather than rerun.
4. Run `python research/fir-baseline/analyze.py` to generate the summary/proof data and 2D PNG/SVG plot, then `python research/fir-baseline/verify_results.py` to check all saved artifacts and write the manifest.

`build/cases/` contains generated inputs, ELF/bin, linker map, disassembly and raw stdout/stderr for every distinct target binary. results.json stores their checksums; results.csv is the flattened table. Shared contract rows are not independent executions. Keep or archive build artifacts with the results when sharing a paper; they can also be rebuilt from the pinned sources and saved inputs.

The scripts are intentionally small research probes. Their build caches assume unchanged toolchain settings; use a fresh build directory for an independent reproduction or toolchain change.

On this host, Matplotlib emits an unavailable-Axes3D warning because of the installed package mix. The experiment uses 2D plotting only; the PNG was rendered and visually inspected. No benchmark/test failure depends on 3D plotting.

## Limits before a paper claim

The fixture is a baseline platform, not itself a novel contribution. The experiment samples one compiler/architecture, two flags, six test filters and two synthetic streams. A final paper needs a clear comparison with the closest empirical/compiler research, broader justified workloads, and a reason the measured interaction matters. CMSIS is pinned for reproducibility rather than asserted to be the newest release. Model-based differences must remain labeled as such.

## Separate held-out selection validation

The [fixed validation protocol](../fir-validation-protocol.md) defines the next experiment. Its files are separate from the pilot: [selection-design.json](selection-design.json), `selection-results.json`, `selection-results.csv`, [selection_validation.py](selection_validation.py), and [validation_firmware.c](validation_firmware.c). The six new task-motivated designs include odd and nonsymmetric filters. Synthetic raw ADC11 samples and the same samples multiplied by 32 distinguish a range guarantee from a changed representation. This is a held-out policy test relative to the pilot, not a representative population study or application-quality validation.

Requirements add SciPy 1.15.3 and official Arm GNU Toolchain 15.2.Rel1, extracted under `build/toolchains/arm-gnu-toolchain-15.2.rel1-x86_64-arm-none-eabi/`. Download the Linux x86_64 arm-none-eabi `.tar.xz` and `.sha256asc` from [Arm's official package directory](https://developer.arm.com/-/media/Files/downloads/gnu/15.2.rel1/binrel/arm-gnu-toolchain-15.2.rel1-x86_64-arm-none-eabi.tar.xz). The verified SHA256 is `597893282ac8c6ab1a4073977f2362990184599643b4c5ee34870a8215783a16`. This is a newer pinned release, not an assertion that it is the latest. The existing GCC 10.3.1, pinned simulator and CMSIS dependencies must also be available. CMSIS stays at v1.14.4 to isolate compiler effects.

Run from the repository root:

```bash
python3 -m unittest discover -s research/fir-baseline -p 'test_*.py' -v
python3 research/fir-baseline/selection_validation.py --prepare
python3 research/fir-baseline/selection_validation.py --smoke
python3 research/fir-baseline/selection_validation.py --run
python3 research/fir-baseline/selection_validation.py --verify
```

`--prepare` saves literal arrays and source/protocol hashes before target evaluation. Preserve the original saved design with reported results; regeneration after source edits is a new artifact. The runner rejects changed source/protocol hashes. Compiler/source/flag caches and raw cases are isolated under `build/selection-validation/`. No pilot results are overwritten.

All valid candidates must pass target output, retained-history and state/output-canary checks. Both CMSIS default and `ARM_MATH_LOOPUNROLL` builds are included, with reversed coefficients and an extra state slot where appropriate. All nine candidate slots are accounted for, including explicit exclusions for odd library tap counts, missing symmetry or failed safety proofs. Winner agreement and regret are computed against the best valid tested candidate separately for architectural cycle estimates and modeled CPU energy. No post-evaluation policy tuning belongs in the held-out result.

Run `python3 research/fir-baseline/analyze_selection.py` for descriptive analysis. The [validation findings](../fir-selection-validation-findings.md) explain the fixed-policy failures and the novelty boundary.

An identified baseline omission is corrected separately: CMSIS supports odd logical filters through zero extension. Run `python3 research/fir-baseline/padded_cmsis_check.py`, then the same command with `--verify`, to reproduce 48 supplementary 66-tap CMSIS binaries for the logical 65-tap filter. Its [supplement results](selection-padded-cmsis.json) preserve the original policy and results while adding the exact padded library alternatives to the oracle. This is a post-evaluation strengthening of the candidate set, not another independently held-out policy test. Appending a zero is done in lag order before reversing the full coefficient array; target outputs must still match the original unpadded reference.

# FIR selection validation: protocol fixed before target evaluation

19 October 2026. This is the bounded next stage approved after the [novelty audit](fir-current-novelty-audit.md). It extends the existing simulator fixture; it does not introduce a new FIR algorithm. The pilot results are development data. The new filter bank is held out from policy development, not a statistically sampled population of deployed filters.

## Question and fixed prediction

Can the pilot's simple arithmetic-based policy choose the cheapest valid exact Q15 FIR in a stronger candidate set on new designs and a newer compiler?

Fix this policy before looking at new target results:

1. For exactly symmetric integer coefficients, choose `fold32` if all narrow-accumulator and paired-product proofs hold; otherwise choose `fold64` if the paired-product proof holds.
2. Otherwise choose `direct32` if its accumulator proof holds, or `direct64`.

The wide-product folded control remains diagnostic and is included in the oracle candidate set but is never preferred by the policy. This conservative fallback is safe even when a wide folded implementation might be faster. Do not revise this policy after inspecting validation outcomes; later changes require a separate evaluation set.

Admission uses established sufficient conditions: `M*sum(abs(h)) <= INT32_MAX` for all int32 prefixes, and `2*M*abs(h_pair) <= INT32_MAX` for folded int32 products. Direct products always fit int32 for int16 operands. Generic folding requires exact coefficient symmetry, including after quantization. A failed sufficient proof excludes a candidate; it is not automatically an overflow witness.

## New designs and their limits

Use six designs chosen for diversity in length, coefficient structure and plausible filtering tasks, with no gain-based tuning:

| Identifier | Floating design before fixed Q15 coefficient rounding | Reason for inclusion |
|---|---|---|
| speech_lp48 | 48-tap Hamming lowpass, 3.4 kHz cutoff, 16 kHz sampling | Short speech-band lowpass |
| sensor_lp80 | 80-tap Blackman lowpass, 100 Hz cutoff, 1 kHz sampling | Different window and length |
| vibration_bp192 | 192-tap Kaiser(beta=5) bandpass, 100–1000 Hz, 4 kHz sampling | Longer, broad bandpass; inspect actual range boundary |
| biosignal_bp96 | 96-tap Hamming bandpass, 0.5–40 Hz, 360 Hz sampling | Low-frequency bandpass; an illustrative numeric workload, not a validated clinical filter |
| mains_bs65 | 65-tap Hamming bandstop, 48–52 Hz, 360 Hz sampling | Odd-length center term and library applicability boundary; no specified notch attenuation is promised |
| speech_minphase48 | Homomorphic minimum-phase conversion of a 95-tap speech lowpass, producing 48 taps | Nonsymmetric FIR, requiring direct fallback; not numerically interchangeable with speech_lp48 |

Each filter defines its own fixed reference. No coefficient changes are allowed between implementations of that filter. Use SciPy 1.15.3 `firwin(..., scale=True)` and `minimum_phase(..., method='homomorphic', half=True, n_fft=32768)`, round to nearest-even at scale 32768, assert representability, and save literal integer arrays plus design parameters. These are author-designed application-motivated examples, not filters copied from production systems or evidence of application-level signal quality. [SciPy firwin](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.signal.firwin.html), [minimum_phase](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.signal.minimum_phase.html).

## Inputs and representation control

Use 513 seeded (`20261020`) signed ADC11 samples in [-1024,1023], including explicit negative/positive extrema, and a second stream made by multiplying those samples by 32 before conversion to int16. Compare the raw stream under both an ADC11 guarantee (M=1024) and a full-int16 guarantee (M=32768). The shifted stream has only the full-int16 guarantee.

This separates (a) unchanged samples with different static guarantees from (b) a changed numeric representation. An 11-bit ADC does not automatically justify M=1024 after shifting its codes into Q15. Synthetic signals exercise numerical implementation; they do not establish real-signal quality or data-distribution generality.

The reference is `clip_int16(floor(sum(h*x)/32768))`, exact products/sums and one final quantizer. All outputs and retained history must match. 513 samples exceed the longest filter and exercise tail blocks, but still include startup history; do not label these steady-state measurements.

## Candidate and compiler checks

Reuse the five generic kernels and unmodified CMSIS-DSP v1.14.4 standard/fast Q15 routines. Add both default and `ARM_MATH_LOOPUNROLL` CMSIS builds. CMSIS requires an even tap count of at least four; exclude it for odd designs. For nonsymmetric filters supply reversed lag coefficients to CMSIS. Allocate its documented extra state slot for loop-unrolled code. Exclude fast CMSIS wherever the accumulator proof fails.

Compare Arm GCC 10.3.1 with the official Arm GNU Toolchain 15.2.Rel1 Linux x86_64 bare-metal package, verifying its published SHA256. This is a newer pinned compiler, not a claim to test the latest release. All builds use Cortex-M0 Thumb, `-O2`, no LTO, with the existing common flags and memory layout; block sizes 1,16,64. Keep compiler-specific object caches separate. Changing only the compiler isolates compiler effects while holding the library version fixed; no claim about current CMSIS releases follows. [Arm installation guide](https://learn.arm.com/install-guides/gcc/arm-gnu/), [CMSIS v1.14.4 contracts](https://arm-software.github.io/CMSIS-DSP/v1.14.4/group__FIR.html).

## Measurements, failure conditions and interpretation

Preserve raw ELF/binary/disassembly/output/events and checksums. Verify target output and history before admitting a timing/energy row. An unsupported instruction, build failure or mismatch is an explicit failed validation, never a silently dropped candidate. Verify simulator hash and source hashes; retain the existing instruction/timing microchecks.

Primary costs are verified target events and the explicitly qualified Arm-table zero-wait-state estimate. Secondary CPU energy uses the pilot's unchanged Nikov model/configuration; no hardware validation or physical confidence interval is implied.

For each filter/contract/compiler/block group, report chosen candidate, exhaustive best valid candidate within the declared set, winner agreement, and regret `(chosen_cost / best_cost - 1)` separately for architectural cycles and modeled CPU energy. Report all groups, not only gains. Attribute policy failures using matched instruction, multiply, memory and branch counts. Do not count reused traces or repeated reference outputs as independent application samples.

**Decision:** If the fixed rule transfers and the only explanation remains “int32 is cheaper when valid,” classify the result as useful engineering/replication with limited field novelty. If it fails, first determine whether an existing library setting or established optimization already explains/fixes the failure. A repeatable, previously unresolved implementation interaction could justify a narrower empirical contribution, but a failed rule alone is not proof of novelty. Stop this stage after this matrix and its causal analysis; do not tune a replacement policy on it and call that held-out validation.

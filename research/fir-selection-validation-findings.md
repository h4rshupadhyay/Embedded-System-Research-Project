# Held-out FIR selection validation: findings and contribution boundary

19 October 2026. The [fixed protocol](fir-validation-protocol.md) was written before new target evaluation. The simple pilot-derived policy was not changed after observing validation results. [Frozen designs](fir-baseline/selection-design.json), [raw result table](fir-baseline/selection-results.csv), [full results and artifact hashes](fir-baseline/selection-results.json), [descriptive analysis](fir-baseline/selection-analysis.json).

## Decision

**The bounded validation is complete. Arithmetic admission alone does not select the best tested implementation. The resulting counterexamples are useful empirical evidence, but they do not yet establish a new algorithm or a substantial field-level research contribution.** Do not promote the fixed selection rule as our novel method. Much of its failure is explained by established library unrolling, state-copy costs and compiler-dependent generated code.

**After correcting the odd-length library baseline, the practical comparison contains 570 target executions and 292,410 correct output comparisons. The unchanged policy chooses the modeled-energy winner in 77/108 groups, with 5.25% mean and 51.83% worst overhead.** The initial protocol-only results below are retained separately from that post-evaluation correction.

Keep the working FIR artifact and these results. For the professor, the defensible project is an exploratory empirical study of correctness-constrained FIR selection, with explicit preliminary findings and unresolved originality. Meaningful field novelty is not secured by adding these cases or discovering a timing/energy reversal. A research paper may report an original empirical finding, but it must establish what prior work does not already explain.

## What was fixed and what was evaluated

The policy chooses `fold32` when symmetry and both narrow-width proofs hold; otherwise `fold64` when its product proof holds; otherwise `direct32` when its accumulator proof holds; otherwise `direct64`. These are sufficient arithmetic conditions, not new theorems or a learned cost model. The policy deliberately does not consult measured validation costs or choose a library variant.

The held-out bank comprises six newly designed numeric workloads: speech lowpass48, sensor lowpass80, vibration bandpass192, biosignal bandpass96, mains bandstop65 and nonsymmetric minimum-phase speech48. Their literal coefficients and design parameters are saved. These are application-motivated synthetic examples, **not production filters or validated application/clinical specifications**. Each has its own fixed bit-exact reference; the linear/minimum-phase speech filters are not interchangeable computations.

Compare GCC 10.3.1 and official Arm GNU Toolchain 15.2.Rel1, Cortex-M0 Thumb, `-O2`, no LTO, blocks 1/16/64. Both compilers use the same CMSIS-DSP v1.14.4 sources to isolate compiler effects. The newer release is pinned, not asserted to be the latest; no current-CMSIS performance claim follows. Official archive SHA256 was verified. The candidate set adds default and `ARM_MATH_LOOPUNROLL` builds of both standard and fast Q15 CMSIS to the five generic kernels. Odd-length library exclusions and missing symmetry are explicit. CMSIS coefficients are reversed for its interface, including the nonsymmetric filter.

The actual streams are 513 signed ADC11 samples and the same codes multiplied by 32. Only the unshifted stream admits an ADC11 guarantee; relabeling the shifted stream as small-magnitude would be invalid. Full-int16 and ADC11 contract rows share the raw stream's eligible binaries. State preparation and canary initialization are outside the measured region; recurring streaming work is included, as in the pilot. All finite streams include startup and tail blocks.

## Verification and accounting

- All ten host test methods pass, including the original UBSan kernel checks and five new selection/reference/representation regressions.
- Before the full matrix, 40 target smoke binaries cover reversed nonsymmetric CMSIS coefficients, odd centers, symmetric folding, tail blocks and guard preservation on both compilers.
- The full matrix executes **522 distinct binaries**. **267,786 target output comparisons** match the independent Python arbitrary-precision reference, with correct retained history and all eight state/output canaries intact.
- These executions reuse **6,156 distinct reference positions**, not hundreds of independent application streams.
- **762 valid rows plus 210 explicit exclusions account for all 972 candidate slots**: six filters × two compilers × three block sizes × three input/contract combinations × nine variants. There are **108 selection groups**.
- The saved artifact verifier reconstructs references, checks binary/output/disassembly hashes, verifies candidate admission and accounting per group, recomputes costs and policy regret, and compares CSV/JSON. The original 486-run pilot remains separate.

The simulator, event mapping, architectural timing assumptions and energy coefficients are unchanged from the [audited pilot](fir-simulator-audit.md). Timing is an Arm-table zero-wait-state estimate, not raw simulator ticks or hardware timing. Energy is a configuration-specific CPU model estimate, not board energy. Differential checks and arithmetic bounds do not formally verify the compiler, library C semantics or ISS.

## Result 1: the fixed rule does not transfer universally

Regret means `(policy cost / lowest valid tested cost) - 1`. It is overhead relative to the oracle candidate, not a claimed energy-saving percentage. Averages below weight the experimental groups equally; repeated contracts/compiler/block cases are not a statistical population sample.

| Compiler | Groups | Modeled-energy winner agreement | Mean energy regret | Worst energy regret |
|---|---:|---:|---:|---:|
| GCC 10.3.1 | 54 | 35/54 | 5.25% | 36.38% |
| GCC 15.2.Rel1 | 54 | 45/54 | 4.99% | 51.83% |
| Combined | 108 | 80/108 | 5.12% | 51.83% |

Architectural-cycle agreement is 47/108, with mean regret 5.35% and worst regret 54.20%. Narrow admission is still necessary for correctness, but it is not a sufficient cost decision.

| Held-out filter | Modeled-energy agreement | Worst energy regret | Explanation to retain |
|---|---:|---:|---|
| speech_lp48 | 15/18 | 5.12% | Older compiler, block1: CMSIS unrolled wins |
| sensor_lp80 | 15/18 | 6.29% | Same block1 limitation |
| vibration_bp192 | 17/18 | 7.56% | Older compiler, ADC11 block1 limitation |
| biosignal_bp96 | 15/18 | 6.64% | Older compiler, block1 limitation |
| mains_bs65 | 18/18 | 0% | Fold32 wins within the smaller applicable set; CMSIS is excluded |
| speech_minphase48 | 0/18 | 51.83% | Direct fallback overlooks established library optimizations |

On the five symmetric designs the energy rule succeeds in 80/90 groups. This is narrower than claiming universal transfer. The odd filter's perfect result does not establish superiority against a hypothetical competent odd-length library implementation.

### Practical library baseline correction

The [official CMSIS documentation](https://arm-software.github.io/CMSIS-DSP/v1.14.4/group__FIR.html) explicitly documents zero extension for odd filters. Thus the original protocol excluded a valid practical library alternative for mains65. We corrected the comparison in a separate **post-evaluation supplement**, preserving the original design, source and result files. [Supplement runner](fir-baseline/padded_cmsis_check.py), [results and expanded selection groups](fir-baseline/selection-padded-cmsis.json).

Append one zero to the 65-tap **lag-order** coefficients, then reverse the complete 66-element array for CMSIS. This preserves the reference computation, includes the extra library state/update cost, and checks its retained history projected onto the original logical 64-sample history. It adds 48 binaries, 72 contract rows and 24,624 correct output comparisons; all history and canary checks pass. The original policy remains unchanged.

With that stronger candidate set, mains65 agreement falls to **15/18**, with worst modeled-energy overhead **4.80%**. Overall agreement is **77/108**, mean energy overhead **5.25%**, worst **51.83%**; architectural-cycle agreement is **38/108**. The combined matrix has 570 binaries and 834 admitted rows. This closes the identified odd-filter baseline gap without tuning the policy. It does not make the candidate set globally optimal.

The expanded comparison has 39 timing/energy winner disagreements, with modeled energy penalties approximately 0.020–2.001%. The earlier 33/108 and 1.825% maximum below refer strictly to the original protocol candidate set. Both have the same interpretation: small, unvalidated physical margins.

## Result 2: stronger library controls explain the largest failure

For nonsymmetric speech48, GCC15, raw ADC11, block64, both candidates have legal exact 32-bit accumulation:

| Candidate | Instructions | MUL | Taken branches | Architectural cycles | Modeled µJ/output |
|---|---:|---:|---:|---:|---:|
| Policy: direct32 | 285416 | 24624 | 25578 | 390030 | 0.764717 |
| Best: CMSIS fast, unrolled | 196208 | 24624 | 3012 | 252932 | 0.503677 |

The policy's energy overhead is 51.83%. Both compute the same number of products; the library organizes four outputs together and changes loop/data reuse. This is a concrete failure of our deliberately simple fallback, **not evidence that unrolling is new**. The first-party [CMSIS source](https://github.com/ARM-software/CMSIS-DSP/blob/3a04f817a4380c00ff51f9bcdc6c4e4bb7a18b80/Source/FilteringFunctions/arm_fir_fast_q15.c) documents its four-output loop. FIR blocking/search and the inadequacy of operation counts already appear in [SPIRAL's FIR study](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf).

At block1, the library's four-output body cannot run; its `ARM_MATH_LOOPUNROLL` build still changes history-copy organization. Therefore do not attribute all its gains to four-output convolution reuse. Matched counts and disassembly are needed for the particular case. The source-level distinction is directly visible in the pinned library's separate convolution and state-copy unrolling branches.

The modeled-energy winner changes in **10 of 54 compiler-matched groups**, all at block1. A newer compiler is not uniformly better for every kernel. The wide-product folded control still executes six machine MULs per paired product on both compilers for even-length filters; this observation persists, but remains a diagnostic rather than a strong improvement baseline.

## Result 3: timing/energy rankings can differ, with small margins

Unlike the original pilot's 0/108 disagreements, the stronger candidate set yields **33/108 groups** with different architectural-cycle and modeled-energy winners. Each disagreement is between folded32 and CMSIS fast unrolled. Choosing the cycle winner incurs only **approximately 0.020–1.825% modeled energy overhead**. These are model predictions with no physical uncertainty estimate; do not claim measured energy reversals or a robust physical proxy failure.

Example: speech lowpass48, GCC15, raw samples, full-int16 guarantee, block64:

| Candidate | MUL | Architectural cycles | Modeled µJ/output |
|---|---:|---:|---:|
| Fold32 | 12312 | 253122 | 0.498346 |
| CMSIS fast unrolled | 24624 | 252932 | 0.503677 |

CMSIS is about 0.075% faster under the cycle estimate but costs about 1.07% more under the energy model. Relative to fold32, its weighted non-MUL and MUL terms add about 12375 and 20345 nJ; reduced branch, SRAM-read and Flash-data terms subtract about 22506, 12299 and 3548 nJ; SRAM writes add about 8367 nJ. The net is only 2735 nJ over 513 outputs. This decomposition explains the model's near tie without implying a hardware-confirmed difference. The reused [energy model](https://arxiv.org/html/2301.12806v1) is not our invention.

## What this contributes now

The useful new local evidence is a **falsified simple policy**, reproduced across two compiler versions with exact arithmetic admission, stronger library builds, full streaming accounting and explicit counterexamples. The post-evaluation causal analysis is descriptive; it did not tune a replacement rule or claim another held-out success.

This advances the project beyond an unsupported proposal: it identifies where range/symmetry alone fail and quantifies the cost. It does **not** by itself settle field originality, establish a new optimizer, or support a physical energy-saving claim. The closest prior work already motivates processor-aware width optimization, FIR blocking and generated-code analysis. Continue writing the empirical argument only around a clearly differentiated finding; do not expand the matrix merely to inflate novelty.

Professor wording:

> “We tested a fixed arithmetic-based FIR selection rule on six new designs and two compiler versions. After including a documented zero-padded library baseline, it chose the modeled-energy winner in 77 of 108 groups. Established library optimizations beat its fallback by substantial margins, which we explain using target events and generated code. The project is feasible and the empirical findings are reproducible; originality relative to earlier FIR/code-generation work remains a claim to establish, not an assumption.”

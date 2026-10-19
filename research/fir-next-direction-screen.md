# Screen: coefficient-aware exact FIR accumulator partitioning

19 October 2026. FIR-only targeted primary-source screen. Candidate: preserve an exact wide-accumulator FIR and final Q15 quantizer, but compute provably safe groups in int32 and widen only at group boundaries.

## Decision

**Do not present this basic idea as our novel replacement algorithm.** Coefficient-aware width reduction, architecture-aware word-length selection and narrow partial accumulation followed by wider reduction are established techniques. This screen did not establish that every detail of a particular embedded partition optimizer has been published, but it found enough direct overlap that novelty must not be inferred from a new combination of labels.

A further practical issue can eliminate the partitioning problem entirely: many filter/input contracts permit the whole FIR to accumulate exactly in int32. Those deserve an optimized int32 full-FIR baseline, not an artificially expensive always-int64 comparison.

## Direct evidence

1. [MathWorks, *Fixed-Point Precision Rules for Avoiding Overflow in FIR Filters*](https://www.mathworks.com/help/dsp/ug/fixed-point-precision-rules-for-avoiding-overflow-in-fir-filters.html), gives coefficient-sign/input-range endpoints and full-precision accumulator sizing without precision loss. Thus proving narrower FIR accumulation from known coefficient values and input domains is standard. The formulas can be applied to a subset of terms directly; this is our elementary deduction, not an identified new theorem.

2. Daniel Ménard and Olivier Sentieys, [*DSP Code Generation with Optimized Data Word-Length Selection*, SCOPES 2004, pp. 214–228](https://link.springer.com/chapter/10.1007/978-3-540-30113-4_16), explicitly optimizes software fixed-point formats with processor architecture, subword parallelism and multiple-precision instructions under an accuracy constraint. The publisher abstract was inspected; the author-uploaded primary paper's indexed figures include an FIR data-flow optimization example. Do not claim processor-aware FIR precision selection or code generation is broadly new. Its stated accuracy constraint is not automatically our bit-exact wide-integer contract; this is a distinction, not secured novelty.

3. Daniel Ménard et al., [*High-Level Synthesis under Fixed-Point Accuracy Constraint*, 2012](https://onlinelibrary.wiley.com/doi/10.1155/2012/906350), §3.1 discusses grouping operations by shared operators and coupling word-length optimization with scheduling/resource assignment. This is hardware synthesis and accuracy-constrained optimization, rather than necessarily exact int32-to-int64 software chunks. Nevertheless it directly rules out broad novelty claims for combining grouping, cost and arithmetic width. The primary full text was inspected.

4. [Doppler's first-party *HalfbandDecimatorQ15* implementation documentation](https://doppler-dsp.github.io/doppler/gallery/hbdecim_q15/), sections “AVX2 inner loop” and “Q15 arithmetic budget,” explicitly describes int32 SIMD partial accumulators and an int64 horizontal reduction in a Q15 FIR implementation, and explains why an int16 symmetric pre-add can overflow. This is implementation precedent, not a peer-reviewed optimality result. Its safety claims were not independently verified here; cite it only as evidence that this arithmetic organization already exists. Do not reuse its asserted numerical limits without a separate proof and source inspection.

## Cheap analytical gate before further work

Let `M=max(abs(a),abs(b))` for a guaranteed integer input domain `[a,b]`, and let `A=Σ|h[i]|`. A sufficient condition for every prefix of any ordinary exact accumulation order to fit int32 is

`M*A <= 2147483647`.

For full int16 input, `M=32768`, so `A<=65535` suffices. In coefficient units scaled by 32768, that is approximately coefficient L1 gain below 2. For signed 11-bit input, `M=1024`, so `A<=2097151` suffices: approximately L1 gain below 64. These are direct integer arithmetic deductions. An actual full-sum proof may be tighter through signed coefficient bounds. Symmetric pre-additions must themselves be widened, and prefix bounds—not merely the final result's observed range—must remain safe.

If the entire filter fits, partitioning can only add widen/reduction overhead relative to a competent int32 baseline. When groups genuinely are needed, compare at least whole int64, whole int32 where certified, fixed-size safe chunks, simple greedy coefficient-bound chunks and any proposed optimizer. Include symmetry, locality, instruction support, compiler lowering and output blocking; do not credit an algorithm for removing an unnecessary baseline width.

## Defensible next action

First run the global range proof on the existing filter bank and declared ADC/int16 contracts. If almost everything fits int32, reject accumulator partitioning for this project. If enough application-motivated filters require widening, a narrow empirical question is feasible: **when does exact accumulator specialization improve complete embedded FIR execution over optimized safe baselines, and when do instruction/locality costs erase it?** Simulator-only execution is suitable for that question; energy claims require a compatible explicit model.

This is a possible empirical/compiler-specialization study, with originality still to establish. A meaningful algorithm paper would need an actual new optimization formulation or demonstrated missing capability beyond range analysis and greedy grouping. Do not promise that adding dynamic programming or a solver supplies that contribution automatically. The most useful immediate deliverable is a falsifiable range-and-cost screen, not another professor proposal asserting novelty before evidence.

## Existing filter-bank gate: root-agent calculation

The root agent checked the nine existing lowpass/bandpass/halfband filters against the global sufficient bound above. It reports full-int16 L1 sums of `43520, 53010, 62232` (lowpass), `50354, 62316, 74258` (bandpass), and `57611, 64983, 72277` (halfband). Seven of nine satisfy the full-int16 threshold of 65535; all nine satisfy the signed-11-bit threshold. This audit records the root's calculation; it did not independently rerun the numerical pilot.

Consequently, **reject partitioning as the main new algorithm for the present filter bank**. The evidence instead supports a manageable original empirical study: compare correctness-equivalent, contract-specialized FIR implementations and determine when proved-safe accumulator narrowing changes the best complete implementation. State the contribution as new controlled evidence, a reproducible artifact and quantified boundary conditions—not invention of narrowing, symmetry or autotuning. Begin with verified target cycles. Add modeled energy only after selecting and validating a suitable model. Whether the resulting empirical findings are substantial enough for the professor remains conditional on the measured results; a new experiment is original work but not automatically a meaningful research contribution.

# FIR-only new-topic audit

19 October 2026. Strict FIR-only, simulator-only college research scope. Old implementation grid and processor constraints do not apply. Targeted primary-source check, not exhaustive priority certification.

## Decision

Among the initial three ideas, transition-aware deadline-safe streaming FIR adaptation is more promising than generic sparse skipping or quality/precision tuning. However, the parent's **quantization-certified exact FIR early termination** is the sharper algorithmic research candidate, provided a feasibility pilot passes. It changes which products are needed while proving the final quantized output unchanged, rather than merely retuning familiar implementations. Its success is uncertain and must not be promised before overhead-inclusive measurements.

Suggested question: **When can the remaining products of a fixed-point FIR output be skipped with a certificate that the final quantized output is unchanged, and can the certificate save net simulated energy after all bound-maintenance and checking costs?**

The proof principle is standard interval reasoning. Candidate originality lies in an efficient FIR-specific bound/check organization, formal arithmetic contract, and demonstrated net benefit with a characterization of failure regimes. No exact duplicate was found in this search; that does not prove novelty.

## Initial three candidates: nearest work and risks

### 1. Deadline-aware block/implementation switching

[Gačić, Püschel & Moura, *Fast Automatic Software Implementations of FIR Filters*, ICASSP 2003, author PDF](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf) automatically searches FIR algorithm and coding alternatives, including blocking/unrolling and time/frequency-domain alternatives. Thus block-size tuning, FIR autotuning and architecture-sensitive crossovers are established.

[SPIRAL's primary publication index](https://spiral.ece.cmu.edu/pub-spiral/allabstract.jsp) also explicitly lists DSP transform code generation optimized for both runtime and energy, and quality-constrained multiplierless synthesis. Do not claim that adding energy or a quality constraint to an autotuner creates a new broad problem. Detailed exact scope of those entries needs inspection if pursuing this alternative.

[Sapio, *Runtime Adaptation in Embedded Computing Systems Using Markov Decision Processes*, 2019 dissertation](https://api.drum.lib.umd.edu/server/api/core/bitstreams/cd45c670-4609-41a1-963a-475f9f2b7b22/content), Chapter 2, addresses reconfigurable FIR-based channelizers and explicitly models transition states/costs. Therefore accounting for switching overhead is not novel either. This does not duplicate every scalar FIR streaming-batch policy.

A plausible narrower contribution would be a deadline-safe online policy for fixed-coefficient FIR streams under changing arrival rates, explicit pending partial blocks, and measured transition overhead, compared with an offline optimum. But changing block size does not intrinsically require history migration: compatible kernels can share a canonical delay line. Do not invent a migration cost that a sensible baseline avoids. The pilot must establish real competing regimes; if largest feasible batch always wins, there is little algorithmic problem left.

### 2. Input-sparse/zero-run exact FIR

Sparse convolution is old: [Cuypers' author-contributed sparse convolution implementation, 2001](https://www.mathworks.com/matlabcentral/fileexchange/865-sparseconv) explicitly handles sparse input and sparse filter vectors. It is small author software rather than a peer-reviewed energy paper, but directly refutes novelty of sparse-input convolution itself. The site's automatically generated present-day citation year should not replace its recorded original release date.

[Ludwig et al., *Discrete-Time Randomized Sampling*, 2001, author-group PDF](https://dsp-group.mit.edu/wp-content/uploads/2024/11/Discrete-TimeRandom.pdf), §6.1, already discusses reducing nonzero convolution terms and checking multiply-by-zero operations for low-power FIR; its sampling process trades output quality, unlike exact skipping of naturally zero inputs.

An overhead-aware exact dense/sparse software switch could be a useful case study, but zero skipping plus a density threshold is not a strong algorithmic novelty claim. Dense real sensor samples are not naturally exactly zero merely because they are small; adding a zeroing threshold changes the signal and requires an explicit quality contract. Include scan/encoding cost, residual history, all output writes, and dense worst cases. Evaluate equal zero fraction with different run distributions to expose whether density alone is inadequate. This remains a candidate empirical insight rather than an established novel method.

### 3. Symmetry/precision/quality-aware FIR

[Ludwig, Nawab & Chandrakasan, *Low-Power Digital Filtering Using Approximate Processing*, 1996, MIT-hosted paper](https://dsp-group.mit.edu/wp-content/uploads/2024/11/Ludwig_Low-Power_DFiltering-1996.pdf) dynamically varies filter order with signal statistics and explicitly studies overhead. Adaptive approximate FIR energy-quality trade-offs are decades old.

[Sinha & Chandrakasan, *Energy Efficient Filtering Using Adaptive Precision and Variable Voltage*, 1999, paper](https://citeseerx.ist.psu.edu/document?doi=60a96099691294f33629c9b4237880c3edf7bddc&repid=rep1&type=pdf), DOI 10.1109/ASIC.1999.806528, already adapts to input bit precision using distributed arithmetic **without loss of accuracy**, with fixed throughput and voltage scaling. Therefore “data dependent exact energy reduction” is also not broadly new. It differs from the proposed whole-product omission based on a final output quantization cell.

Symmetric pre-addition, sparse coefficients, multiplierless coefficients and coefficient quantization are established. A new target processor or new plot of ripple/energy is insufficient alone. Software ISA-aware coefficient synthesis could be stronger, but needs a more focused optimization-literature check than was completed here.

## Recommended candidate: exact quantization-cell termination

For integer input/coefficients, compute a partial sum P and a conservative integer interval for the uncomputed residual, `r∈[L,U]`. If the declared monotone final quantizer Q satisfies `Q(P+L)=Q(P+U)`, every possible full sum gives the same output. Then omitted products do not change the declared reference output.

This supports truncation/rounding/saturation only when their definitions and tie conventions are explicit. Wrapped narrowing is not globally monotone, so endpoint equality alone is unsafe without a no-wrap proof or modular-aware handling. Use a sufficiently wide sum and prove all intermediate arithmetic/bounds avoid overflow; abs(INT_MIN), pre-add width and signed-shift semantics matter. Reordering terms is safe for exact wide integer sums, but not automatically for per-MAC saturating references.

A cheap candidate bound is `|r|≤M*Σ|h_remaining|`, with M a valid bound over the remaining input samples. Precompute coefficient suffix bounds; maintain rolling/tiled input bounds. Sorting taps changes access locality, so compare natural order, coefficient-magnitude order and tiled checks, counting metadata and loads. Bound evaluation/checking at every tap may cost more than the products saved.

### Hard feasibility limit

For an unsaturated output defined by an integer right-shift of s bits, a quantization cell contains at most `2^s` integer sums. A symmetric residual interval `[-R,R]` cannot fit in one cell unless `2R≤2^s−1`. For Q15 shift15, this requires `R≤16383`. If `M=1000`, the remaining coefficient absolute-sum must be at most16 under this simple bound. Many useful filters will reach that only after almost all products have been computed. This is an algebraic necessary condition for this bound's success, not a measured claim about any dataset.

Coarser **declared output precision** can create larger cells, but each experiment must compare against the full FIR followed by that same quantizer. Do not count changed precision as exact equivalence to a higher-precision baseline. Saturation cells are unbounded and may support early exit, but a method that only wins for unrealistically clipped inputs is a weak practical contribution.

## Pilot and substantive evaluation

Start with representative designed lowpass/bandpass/halfband filters and realistic fixed-point amplitudes, alongside adversarial quantization-boundary samples. Before target implementation, an oracle study should count the maximum safely omittable products using the candidate bounds. If that upper opportunity is already tiny, no implementation optimization can rescue it.

Proceed if a meaningful range of ordinary nonsaturated workloads offers enough safely omitted products to plausibly pay for bound maintenance, and a real simulated implementation demonstrates net benefit. Stop/reframe if gains exist only for all-zero input, deliberately tiny coefficients, heavy clipping, or ignoring checking costs. A useful negative finding can map feasibility limits, but should not be advertised as a successful energy-saving algorithm.

Compare optimized full FIR, exact zero-skipping, fixed-precision full FIR at the same final quantizer, and proposed bounds with dense fallback. Add oracle omission opportunities (not deployable) and ablations for bound tightness/check frequency/window maintenance. Report bit-exact output checks, actual target cycles and modeled energy, code/RAM overhead, tail latencies and worst-case slowdowns, early-exit rates and products omitted. Do not equate fewer multiplications with saved energy. Hold out filter designs and signal amplitude regimes when choosing thresholds/check schedules.

This candidate is scientifically more distinct than generic block tuning, but the pilot is essential. Existing interval arithmetic and precision-on-demand FIR prevent broad first-of-kind claims. The focused novelty claim should concern the specific safe product-skipping method and evidence, if both survive the next literature and feasibility checks.

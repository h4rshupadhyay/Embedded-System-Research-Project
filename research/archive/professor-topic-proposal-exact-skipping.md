# Research proposal for professor discussion

**Proposed title: Quantization-Certified Computation Skipping for Energy-Efficient Fixed-Point FIR Filters**

**Date:** 19 October 2026. **Scope:** FIR only; simulator-only college research; publication optional. This replaces the earlier time–energy ranking-search proposal. The earlier version is preserved in `research/archive/professor-topic-proposal-ranking-search.md`.

**Status after validation:** A specified numerical method and a stronger streaming pilot are complete. The current version is **not yet recommended as the final original energy-efficiency project**: its exactness argument is supported, but novelty remains unestablished and real-input skipping leaves little margin for unmeasured overhead. See the [validation findings](research/fir-validation-findings.md), [method contract](research/fir-method-contract.md) and [closer prior-art audit](research/fir-prior-art-validation.md). The sections below preserve the candidate proposal and its intended contribution; they are not claims of achieved novelty or energy savings.

**Next research action:** Establish a verified target-execution baseline for correctness-equivalent full FIRs: whole int64 accumulation, whole int32 where proved safe, and symmetry-aware versions with proper widening. The follow-up [direction screen](research/fir-next-direction-screen.md) rejects basic accumulator partitioning as a new algorithm: it is established, and seven of the nine existing filters already admit exact whole-int32 accumulation for full-int16 inputs; all nine do for signed ADC11 inputs. The candidate empirical question is whether input contracts and arithmetic requirements change the best complete FIR implementation once state, memory and compiler costs are included. Any contribution must come from substantial measured findings or a subsequently justified method; this is not a finalized replacement topic. Energy claims remain conditional on a verified compatible model.

## Recommendation

Investigate an FIR implementation that stops computing an output when a conservative bound proves that the remaining products cannot change its final quantized value. All coefficients, input samples, output samples and output precision remain fixed in each comparison. If the proof condition fails, it computes the remaining terms.

This is a promising **research-paper proposal**, conditional on demonstrating an effective implementation. The mathematical stopping rule is sound under the stated arithmetic contract. Net energy savings and the originality of a particular implementation remain research questions. A targeted primary-source search found no exact duplicate, but does not establish first-of-kind priority.

The topic is independent of the supplied paper's procedure and implementation grid. It retains the relevant application: embedded FIR energy efficiency.

## A pitch for the professor

> Fixed-point FIR filters accumulate products at a higher precision than their final outputs. Consequently, some remaining products may be unable to change an output after its prescribed quantization. We propose to exploit this using a conservative bound on the uncomputed contribution: stop only when every possible completed sum produces the same output. The research will develop an efficient bound and checking strategy, establish bit-exact equivalence to a full FIR reference, and evaluate whether saved arithmetic outweighs the additional control and memory work in simulation. The contribution would include the method and a characterization of the filters and signal regimes where it succeeds or fails.

## The idea, precisely

Let the full integer accumulator for output n be:

`S[n] = sum(h[i] * x[n-i], i=0,...,N-1)`

and let the declared reference output be `y[n] = Q(S[n])`. Start with a Q15 contract such as:

`Q(S) = saturate_to_int16(floor(S / 32768))`.

Use a sufficiently wide accumulator and bounds. This is consistent with the broad arithmetic organization documented for Arm's standard Q15 FIR: full product accumulation followed by truncation and saturation. Its fast Q15 implementation has a different overflow risk; an overflowing reference cannot silently be substituted. [Arm CMSIS-DSP FIR documentation](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html).

After computing some terms, let their exact sum be P. Suppose a valid bound establishes that the remaining sum r lies in `[L,U]`. Because Q is monotone, the condition

`Q(P + L) == Q(P + U)`

proves that `Q(P + r)` is the same value for every possible residual. Return that value and omit the remaining products. Otherwise continue computing.

**Example:** With the Q15 quantizer above, let `P = 337680` and `r` be bounded by `[-2000,2000]`. Every possible full sum lies in `[335680,339680]`; both endpoints quantize to 10. The final output is therefore exactly 10 without evaluating the remaining products. Merely deciding that coefficients or inputs look small would not provide this guarantee.

A simple starting bound is:

`R = M[n] * sum(abs(h[i]) for uncomputed i)` and `[L,U] = [-R,R]`,

where `M[n]` bounds the absolute value of every relevant sample in the current FIR window. Coefficient suffix sums can be precomputed. A maintained window maximum avoids rescanning all samples for every output, but its maintenance cost must be counted.

The interval argument is standard mathematics. It is **not itself the novelty claim**.

## What we would contribute

The proposed contribution is a concrete FIR software method whose certificate is cheap enough to be useful:

1. **Bound organization:** Develop and compare a shared window bound and tighter group bounds, including their storage and maintenance costs.
2. **Computation and check organization:** Choose term groups and certificate checkpoints to balance saved products against checks and memory locality. Preserve symmetric coefficient pairing where available.
3. **Exactness and limits:** Establish the output-equivalence argument under explicit arithmetic assumptions and derive conditions under which early exit cannot occur.
4. **Evidence of usefulness:** Demonstrate net simulated cycle/model-estimated-energy benefits over strong equivalent FIR baselines, and report unsuccessful regimes and worst-case overhead.

These are objectives, not completed contributions. Combining familiar techniques becomes meaningful research only if the resulting method and evidence add something beyond those components.

**Main research question:** Can an inexpensive residual certificate reduce the net cost of fixed-point FIR filtering while preserving every output bit?

Supporting questions concern bound tightness, coefficient ordering versus locality, symmetry, signal amplitude, quantization boundaries, and the cost of deciding when to bypass the mechanism.

## Originality relative to existing FIR research

| Primary source | What is already established | Candidate distinction |
|---|---|---|
| Pillai, [*On Low Power Floating Point Data Path Architectures*](https://www.collectionscanada.gc.ca/obj/s4/f2/dsk1/tape4/PQDD_0021/NQ47712.pdf), 1999, Chapter 8, especially §8.3.3 | Whole floating-point MACs, including product evaluation, can be bypassed when their contribution cannot affect the current finite-precision operation. The wider architecture has additional accuracy qualifications. | A collective remaining-sum certificate under exact integer accumulation and one final quantizer. Whole-product skipping based on precision is already an established broad idea. |
| Ludwig, Nawab and Chandrakasan, [*Low-Power Digital Filtering Using Approximate Processing*](https://dsp-group.mit.edu/wp-content/uploads/2024/11/Ludwig_Low-Power_DFiltering-1996.pdf), 1996 | Dynamically adjusts FIR order using signal statistics, accepting a controlled filtering-quality trade-off and considering adaptation overhead. | Keep the reference FIR and its quantizer fixed; certify that omitted products cannot alter its output. |
| Sinha and Chandrakasan, [*Energy Efficient Filtering Using Adaptive Precision and Variable Voltage*](https://citeseerx.ist.psu.edu/document?doi=60a96099691294f33629c9b4237880c3edf7bddc&repid=rep1&type=pdf), ASIC/SOC 1999, [DOI](https://doi.org/10.1109/ASIC.1999.806528) | Data-dependent, accuracy-preserving FIR computation using input bit precision, distributed arithmetic and voltage adaptation. Lossless data-dependent energy reduction is therefore already established. | Investigate omission of complete remaining products using a certificate about the final quantized output, implemented as embedded software. The inspected paper does not establish that mechanism. |
| Gačić, Püschel and Moura, [*Fast Automatic Software Implementations of FIR Filters*](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf), ICASSP 2003 | Automatic exploration of FIR algorithms and implementation alternatives. | A particular exact data-dependent skipping mechanism, with autotuning used only as supporting engineering if needed. |
| [Arm CMSIS-DSP FIR implementations](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html) | Production block FIR software, state handling and explicit fixed-point arithmetic behavior. | A reference and baseline foundation rather than a novelty source. |

**Defensible proposal wording:** “We investigate FIR-specific residual-bound certificates for exact product skipping and their overhead-inclusive usefulness.”

Avoid claiming the first adaptive FIR, first lossless FIR optimization, first energy-aware FIR, or invention of interval arithmetic. Before a final priority claim, expand the check within FIR to quantization-aware pruning, distributed-arithmetic early completion, product bypassing and relevant patent/author citation chains. The supporting [FIR-only originality audit](fir-only-originality-audit.md) records the alternatives examined and caveats. This is a targeted review, not an exhaustive systematic search.

## Feasibility: early evidence and a hard limitation

**Superseding evidence:** The following independent-window calculation was the original motivation. A subsequent [streaming pilot](research/fir-validation-findings.md) used symmetry-aware baselines, nine filters, real ECG segments, dynamic and static bounds, and several checking schedules. It found zero mismatches in 25,214,976 output comparisons across 6,156 configurations, reusing 626,688 reference output positions. That supports the numerical implementation, not compiled-code correctness or energy savings. In one illustrative 128-tap lowpass configuration, native ECG inputs omitted only 0.86% of folded products on average; including just the bound multiplications already increased the multiplication count by 0.70%. Other late-check variants leave small positive opportunities, with recurring control, memory and bound-maintenance costs still unpaid. The pilot therefore does **not** meet the project-selection checkpoint below.

An exploratory Python opportunity calculation was run and saved in [the analysis script](research/fir-skipping-opportunity.py) and [raw results](research/fir-skipping-opportunity.json). It used Hamming-window lowpass FIRs of 64, 128 and 256 taps, cutoff 0.10 relative to Nyquist, coefficients rounded after multiplication by 32768, 2,000 independent random integer windows per filter/amplitude, descending coefficient-magnitude evaluation, and checks every eight products. The bound used the window's actual maximum absolute input. Seed: 20261019.

Selected results for the **128-tap, 16-bit Q15-output contract**:

| Uniform integer input range | Mean products omitted |
|---|---:|
| -8 to 8 | 32.49% |
| -128 to 128 | 5.77% |
| -8192 to 8192 | 0.00% |

Every certified early output in this probe matched the full reference. These are finite experimental checks, alongside the general interval argument; they do not verify a future target implementation.

**These percentages are neither speedups nor energy savings.** The probe excludes all certificate overhead, uses independent rather than overlapping streaming windows, and does not exploit FIR symmetry in its baseline. The promising row uses signals occupying a very small fraction of the input range. It supplies a reason for a feasibility pilot, not evidence of practical deployment value. The raw output also explores 12- and 8-bit output contracts; those are separate references and cannot be counted as exact Q15 improvements.

There is a useful analytical limit. An unsaturated quantization cell for `floor(S / 2^s)` contains `2^s` integers. For a symmetric integer residual bound `[-R,R]` to fit inside one cell, necessarily:

`2R <= 2^s - 1`.

For shift 15 this requires `R <= 16383`. With a sample bound of 1000, the simple coefficient-tail absolute sum must therefore be at most 16. Often that means almost all products have already been computed. Even meeting this necessary condition is insufficient if the interval crosses a quantization boundary.

This identifies the central difficulty: tighter bounds must create enough extra opportunity to pay for themselves. Saturated outputs may permit other exits, but an algorithm that wins only through heavy clipping would have limited practical value.

## Scope of the initial design and evaluation

Keep fixed coefficients, 16-bit inputs and the exact Q15 output contract initially. Use exact wide integer accumulation. Consider groups of terms with precomputed absolute-coefficient sums and periodic checks. For symmetric FIRs, start from paired samples and a folded full-FIR baseline; charge for wider pre-additions and maintain the correct residual bound. Compare natural group order with magnitude-prioritized order, including index/metadata loads and access-locality costs.

A dense bypass policy is a candidate extension only if necessary. It must count its own decisions, bound-state maintenance and any reconstruction when re-enabled. It cannot be credited with an imaginary zero-cost fallback.

The primary comparisons should include an optimized full FIR with the same arithmetic contract, a symmetry-aware full FIR when applicable, exact zero/coefficient skipping where useful, and the proposed method. All must process the same complete stream, maintain valid history, and write every output. Zero coefficients and zero samples are not unique benefits of the proposal.

Use several FIR designs and signal regimes: lowpass, bandpass and halfband; quiet and active segments; transitions, impulses and quantization-boundary cases; dense nonzero signals as well as sparse ones. Include application-motivated data with defensible scaling and explain the output distribution—especially whether a result is dominated by repeated quantized zero or minus-one outputs. Do not choose signal amplitudes solely to produce wins. Hold out filters and amplitude regimes while choosing check schedules.

Report correctness, cycles, modeled energy, bounds/check overhead, products omitted, code/RAM size, tail latency and worst-case slowdown. A smaller multiply count alone cannot establish energy efficiency. Simulation and model outputs support model-level conclusions; physical energy savings remain unverified without hardware.

A software simulator is sufficient in principle. Tool selection remains open: first verify that a pinned target simulator provides the timing/events needed by a compatible energy model. The old draft's exact processor or simulator is not a dependency and is not yet an established working setup for this new study.

## What to do next

The next deliverable is a small **feasibility and novelty dossier**, before committing to a full energy-efficiency paper. The existing random-window product counts are insufficient to make that decision.

**Progress:** Items 1–3 below have now been completed as an initial exploratory study, with limitations recorded in the linked findings. Item 4 has not started because a strong novelty/usefulness case for this implementation has not emerged. The next research decision is whether a concrete cheaper mechanism can address the observed limitations; simply adding more workloads does not secure a new contribution.

1. **Freeze the reference and proposed mechanism.** Use one documented Q15 contract, wide exact accumulation, unchanged coefficients and every output retained. Write a short algorithm specification identifying precisely how bounds are maintained and when they are checked. State which parts are standard and which implementation decision is the proposed contribution.
2. **Complete a focused FIR prior-art comparison.** Follow the closest papers' references and citing papers for exact FIR product bypassing, early completion and quantization-based termination. Record the numerical guarantee, skipped unit of work, bound/decision mechanism and implementation cost. The deliverable is a cited comparison explaining the specific difference; another collection of keyword-search results is insufficient. If an equivalent mechanism exists, establish a meaningful new contribution before retaining a novelty claim.
3. **Strengthen the numerical feasibility pilot.** Extend the saved probe to overlapping input streams, a folded symmetry-aware reference, multiple FIR designs, ordinary active/quiet segments and quantization-boundary cases. Compare natural and grouped computation orders. Report product counts, certificate work and output distributions separately; do not invent energy weights or treat Python timings as MCU timings. Verify every emitted output against the full reference, including outputs that do not exit early.
4. **Measure the complete implementation if the opportunity survives.** Implement the strongest candidate and equivalent optimized baselines for one verified simulator/model configuration. Include history updates, bound maintenance, indexing, checks, fallback and output writes. This produces the first evidence for net cycles and model-estimated energy, including worst-case slowdowns.

**Decision:** Continue to the full paper when the method has an identifiable distinction from the closest FIR work and a useful, application-motivated operating regime with overhead-inclusive benefit. If ordinary workloads offer too little opportunity even before overhead, revise the mechanism or choose another FIR-specific research question before expanding the experiment grid. Record a failed pilot as evidence; do not force a positive energy-saving conclusion.

For the professor discussion, take the pitch, closest-work table, exact stopping example, preliminary results with their limitations, and this validation plan. Describe the topic as proposed research with a testable novelty hypothesis.

## Decision checkpoint

Proceed with an energy-saving algorithm claim only if a target implementation beats optimized equivalent baselines over a meaningful set of nonsaturated, application-motivated workloads after every recurring overhead is included. A broad universal gain is not required, but the useful regime must be explicit and credible.

If savings disappear after accounting for symmetry, bounds and checks, report the feasibility limits honestly. That could support an empirical limits paper, but would not validate the proposed successful optimization. Topic selection does not guarantee an energy improvement.

## Likely questions from the professor

**Is this a review paper or research paper?** The intended work is original research: a method, an exactness argument and new controlled experiments. Literature collection alone would produce a review, and a demonstration of the elementary interval rule alone would be too small a contribution.

**What is novel?** The candidate novelty is a particular inexpensive FIR residual-certificate implementation and the evidence that it enables useful exact product skipping. Broad data-dependent FIR optimization already exists. The targeted search supports investigating this gap; priority is not proven.

**How can skipping terms preserve the output?** The full accumulator may change, but the prescribed final quantizer maps every value in the certified completion interval to the same output. The mathematical FIR and final numeric contract remain the reference.

**Can it be done with simulators only?** Yes for correctness, target execution analysis and stated model-estimated energy. Do not present modeled energy as measured hardware energy.

**What is the main risk?** Most ordinary high-amplitude Q15 windows may not admit useful early exits, and checking may consume the saved cost. The preliminary calculation already exposes that risk.

## Provenance

Prepared using the research skill and a background primary-source FIR audit. The saved Python probe is an exploratory numerical analysis, not a completed embedded implementation. No target-cycle measurements or energy results have been obtained for the proposed method. The Sinha paper's full text was inspected by the background researcher; direct retrieval was intermittent during the main-agent check. All novelty statements are limited to the sources and targeted searches described here.

The follow-up study adds a directly inspected floating-point bypass thesis, a distributed-arithmetic citation-chain check, established static FIR range formulas, an explicit method contract and a reproducible continuous-stream numerical pilot. The current result is preliminary exactness/feasibility evidence with a cautious project-selection decision, not a validated energy-efficient original algorithm.

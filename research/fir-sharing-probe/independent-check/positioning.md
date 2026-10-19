# Contribution positioning: exact FIR implementations on the pinned Cortex-M0 model

20 October 2026. Task 2 literature and decision note; prepared before receiving the peer's partial-direct results. This note changes no coefficients, implementation, frozen result or experimental claim. It supports the [missing-baseline plan](../../../docs/superpowers/plans/2026-10-20-fir-baseline-check.md) and retains the [pursuit audit's](../../fir-sharing-pursuit-audit.md) conditional decision.

The defensible question is whether exact arithmetic specialization, FIR representation and source emission order produce a useful, explainable tradeoff **after competing forms receive comparable range information**. The current artifact can support a bounded empirical case study. It does not establish a new MCM algorithm, a new width-selection method, optimal scheduling, or physical energy savings. The peer comparison is pending; no outcome is assumed below.

## Closest inspected primary sources

These are targeted overlap checks, not an exhaustive novelty search. Full-text access means relevant passages of the author manuscript or official documentation were inspected; it does not imply an independent reproduction of the cited experiments.

| Primary source and inspected access | What is already established | Boundary relative to this artifact |
|---|---|---|
| Voronenko and Püschel, *Multiplierless Multiple Constant Multiplication*, 2007, [author manuscript](https://spiral.ece.cmu.edu/pubs/synth.pdf), introduction, §§1.2, 2 and Hcub description; full text | Exact products of one input with several constants share shift/add/subtract intermediates. Hcub targets add/subtract count. The introduction explicitly identifies software applicability and register pressure as a separate possible objective. The cost discussion explains its omission of shifts. | Applying Hcub to FIR software or observing that adder count misses register/shift costs is not a new algorithmic contribution. The paper does not establish best complete-stream Cortex-M0 code under this project's contract. |
| Gačić, Püschel and Moura, *Fast Automatic Software Implementations of FIR Filters*, 2003, [author manuscript](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf), §§4–5; full text | SPIRAL searches FIR algorithm/coding alternatives, including input/output locality, blocking and unrolling. Different computation orders with identical arithmetic counts have different runtimes. Its reported targets are Pentium 4 and UltraSPARC II. | FIR implementation selection and computation-order effects are established. This paper does not supply the present exact integer-domain, mixed-state-width Cortex-M0 comparison. |
| D'Alberto, Püschel and Franchetti, *Performance/Energy Optimization of DSP Transforms on the XScale Processor*, 2007, [author manuscript](https://users.ece.cmu.edu/~franzf/papers/hipeac07.pdf), §§2.2–4; full text | SPIRAL generates fixed-point FIR C for embedded XScale, tunes platform configurations and compares against IPP. Runtime and physically measured energy are distinct objectives with configuration-dependent results. | Generic embedded fixed-point generation and performance/energy optimization are prior work. Its hardware, routines and measurement setup differ; it provides neither this artifact's result nor a physical validation of our reused energy model. |
| Garcia and Volkova, *Towards the Multiple Constant Multiplication at Minimal Hardware Cost*, [author manuscript v2](https://arxiv.org/html/2210.02742v2), §§IV–VI; full text | Input-bound propagation supports word-length-aware MCM graph costs measured in one-bit adders. The work separates full-precision optimization from variants permitting bounded intermediate truncation and provides a coefficient-to-VHDL flow. | Width-aware MCM is established, including full-precision cases. Hardware bit costs differ from scalar 32/64-bit instructions, retained FIR state and software spills. Our exact-output comparison cannot borrow favorable truncation results. |
| Castañeda Lozano, Carlsson, Hjort Blindell and Schulte, *Combinatorial Register Allocation and Instruction Scheduling*, [author manuscript v5](https://arxiv.org/pdf/1804.02452), introduction, alternative instructions and ARM discussion; full text | Unison jointly handles register allocation, instruction scheduling and relevant transformations, including spilling and instruction alternatives. Its evaluation includes ARM, and its model discusses Thumb-2 features. | Coupling scheduling/register allocation is established. A changed source emission order in two GCC versions does not prove a new scheduling algorithm, optimality or a compiler defect. Thumb-2 results do not directly establish Cortex-M0 behavior. |
| MathWorks, [*Fixed-Point Precision Rules for Avoiding Overflow in FIR Filters*](https://www.mathworks.com/help/dsp/ug/fixed-point-precision-rules-for-avoiding-overflow-in-fir-filters.html), output limits and full-precision rule; official documentation | Coefficient-sign/input-domain bounds determine output extrema and full precision without overflow or precision loss. | Applying the same elementary bound to a coefficient subset or a retained suffix is our deduction, not a new range theorem. Correct C intermediate types still require inspection. |
| Ménard and Sentieys, *DSP Code Generation with Optimized Data Word-Length Selection*, SCOPES 2004, [publisher abstract](https://link.springer.com/chapter/10.1007/978-3-540-30113-4_16); **abstract only**, chapter restricted | Processor-aware software word-length selection already considers subword/multiple-precision operations and execution time under an accuracy constraint. | The abstract suffices to reject broad novelty in processor-aware precision selection. It does not establish the chapter's exact treatment of bit-exact FIR partial sums; no detailed claim about its algorithm is made here. |

## Candidate contribution and required evidence

The pursuit audit also identified a particularly close implementation precedent:
Doppler's [HalfbandDecimatorQ15 documentation](https://doppler-dsp.github.io/doppler/gallery/hbdecim_q15/),
“AVX2 inner loop” and “Q15 arithmetic budget” (read 20 October 2026), describes
int32 FIR accumulation lanes followed by reduction to int64. This directly
overlaps the narrow-partial/wide-reduction organization of the missing direct
control. Its AVX2 halfband decimator uses round-to-nearest output rather than
our floor quantizer, and differs from the scalar Cortex-M0 full-output filter.
Its stated lane-safety limits and implementation were not independently
validated here. Treat it as first-party implementation documentation, not a
peer-reviewed safety proof or novelty clearance. Our fixed two-group range
proof must stand independently; the partial-accumulation idea is not claimed
as a new algorithm.

The distinctions below are research judgments drawn from the inspected sources and this project's fixed protocol. A different target alone does not establish field-level novelty.

| Candidate claim | Additional evidence needed here | Defensible scope and limit |
|---|---|---|
| Exact suffix-state widths can make transposed software competitive despite a wide final sum. | Independently checked range certificates and code; ordinary mixed-width transposition versus uniform-width transposition; equally narrowed direct arithmetic; storage and frame accounting. | A demonstrated case or failure under the frozen contract. Exact coefficient-aware narrowing itself is established. |
| Cross-coefficient sharing improves complete FIR execution. | Hold state layout, width contract, input, boundary and toolchain fixed; compare `trans_hcub_demand` with `trans_const`, as well as the strongest nontransposed control. | Only the incremental ordinary-transposed/Hcub difference can be associated with this sharing implementation. A library gap combines several changes. No universal Hcub advantage follows. |
| Graph emission order changes generated-code costs. | Same graph and arithmetic under eager/demand emission; inspect generated instructions and traffic/frame differences in both compilers. | A controlled backend-sensitive observation. Source order is not a machine schedule, and aggregate counters alone do not prove the precise cause of a change. |
| A reproducible negative result exposes baseline sensitivity. | Show that the fixed partial-direct control removes an apparent advantage; explain which operations/costs changed; preserve unfavorable configurations. | Potentially useful college empirical work if the corrected finding has a coherent lesson. Discovering an obvious weak baseline alone is insufficient for a strong research headline. |
| A generally useful selector or optimizer chooses FIR forms. | Fresh evaluation designs, equal controls across globally wide contracts, a specified selection rule and validation outside the inspected cases. | Unsupported by the current fixed four-configuration gate and outside its scope. Building an optimizer is not authorized by this decision note. |

## What the missing partial-direct comparison decides

The [fixed protocol](../../../docs/superpowers/plans/2026-10-20-fir-baseline-check.md) requires one 48-tap filter, full-int16 guarantees, the two predetermined coefficient groups `[0,2)` and `[2,48)`, two compilers and block sizes 1/64. Its group bounds are `418709504` and `1957265408`; the full absolute bound is `2375974912`. Those figures are local deductions from the frozen coefficients, not literature results. They motivate testing native-width partial accumulation with a wide final combination. The group split must remain fixed before measurement.

**It can establish:** whether the motivating example survives this material arithmetic-fairness correction; how much the old wide-direct control overstated the tested transposed advantage; and whether surviving benefits trade against code, frame or retained state. It can also reveal compiler/block sensitivity. These statements require independently verified outputs/history/guards, artifact identity, counters and cost reconstruction, plus arithmetic and emitted-code inspection. Test equality alone is not a proof for every allowed stream.

**It cannot establish:** the fastest possible direct implementation; an optimal partition; a general transposed advantage across filters or cores; a new Hcub/scheduling/range algorithm; or novelty clearance. Four rows reuse one selected design and the saved 257-sample input stream. The full-int16 arithmetic proof covers the guaranteed input domain; the timed stream does not become representative merely because the proof is general. Other globally wide or symmetric cases would need equally fair controls before bank-wide claims.

## Timing and energy language

Nikov et al., [*Accurate Energy Modelling on the Cortex-M0 Processor for Profiling and Static Analysis*](https://arxiv.org/html/2301.12806v1), §§2.4–2.5 and Table 2, provide event-weighted CPU energy models. This project reuses the `[20 MHz, prefetch OFF, zero wait states]` model; its terms distinguish non-MUL instructions, MUL, taken branches and RAM/flash data accesses. The paper reports 2.80% MAPE for that configuration on its own workload evaluation. That statistic is **not** a confidence interval or pairwise error bound for these FIR rankings.

Our outputs remain simulator-derived event counts, an Arm-table timing estimate assuming zero wait states/single-cycle MUL, and estimated CPU energy. They are not measured wall-clock runtime, cycle-accurate validation of this local simulator build, board energy or end-to-end application energy. The source paper's validated simulator behavior does not transfer automatically to a modified build. Prefer “lower estimated CPU energy under the selected model” to “saves energy.” Small percentage rankings require particular restraint; this study supplies no physical uncertainty calibration.

## Conditional decision after the join

1. **Accept evidence first:** reject incomparable identities, missing artifact evidence, unsafe intermediate arithmetic, output/state/guard failures or inconsistent cost reconstruction. Repair evidence before interpreting the ranking.
2. **If an explained advantage/tradeoff survives:** frame a case study of exact representation and arithmetic choices on the pinned scalar setup. Report both compilers, both block sizes and all resource dimensions; specify the comparator in every percentage.
3. **If the advantage disappears:** revise the headline to baseline sensitivity or the corrected negative result. Retain the old library comparison only with its actual comparator named. Assess whether the corrected finding has enough substance for the college paper.
4. **If only routine scheduling sensitivity remains:** preserve the engineering artifact and reconsider the central paper question. Do not expand into an optimizer merely to manufacture novelty.

No numerical threshold, peer outcome or new target measurement is declared here. The bounded decision follows the existing pursuit audit; positive performance is not a prerequisite for a valid result, and an artifact alone is not a novelty claim.

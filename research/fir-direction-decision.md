# FIR direction decision after the second literature screen

20 October 2026. Scope: FIR only, simulator only, a college paper with a defensible original contribution; publication optional. The professor is the final evaluator, not an available research guide. The user has stated that time is not a limiting factor. Existing experimental artifacts and the current proposal are preserved.

**Follow-up:** The recommended bounded probe has now been executed. Its matched state-width and graph-emission controls support pursuing a narrow empirical case study, while a new-algorithm claim remains unsupported. See [completed findings and decision](fir-sharing-findings.md). The screen and proposed probe below record the reasoning before those measurements.

## Decision

**None of the three broad replacement topics is ready to be selected as an original contribution. Recommend one bounded investigation of cross-output computation sharing versus exact state and memory costs before selecting a new paper topic.** This recommendation ranks the value and feasibility of the next investigation; it does not certify a literature gap or predict a successful new algorithm.

A new mathematical theorem is not mandatory for this project. A substantial original empirical finding could qualify if it answers a specific question that the closest work leaves open and provides useful, reproducible guidance. Conversely, a familiar optimization implemented on another target, an expected failure of an intentionally incomplete heuristic, or absence of an exact-title duplicate is insufficient evidence of significance. These are assessment criteria, not a claim about an unavailable grading rubric.

This research pass compared primary papers, official implementations/documentation and publisher abstracts. Access limitations are recorded in the linked reports. No new kernels, optimizer, timing measurements or power-failure experiments were implemented or run.

## Comparison

| Direction | Closest work already covers | Remaining testable question | Decision and rejection test |
|---|---|---|---|
| Exact fixed-coefficient software generation | Exact constant-product sharing, width-aware graph design, platform-adapted FIR generation, and machine scheduling/allocation. [Hcub paper](https://spiral.ece.cmu.edu/pubs/synth.pdf), [MCM-Bits](https://arxiv.org/html/2210.02742v2), [SPIRAL FIR](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf). | Can sharing products across outputs retain a useful advantage after exact-width state, register pressure and complete streaming traffic are counted? Is any failure of existing graph-plus-compiler approaches structural rather than an ordinary missed schedule? | **First investigation**, because it reuses the existing numerical and target fixture. Reject a proposed realization if even its justified optimistic cost cannot beat the strongest legal baseline. Reject a new-method claim if any gain is fully recovered by known graphs, ordinary scheduling or coefficient specialization. [Detailed screen](fir-gap-codegen.md). |
| Deadline-constrained batching | Energy/deadline optimization of asynchronous sensor batching, FIR blocking/search and transition-aware DSP adaptation. The 2010 batching paper explicitly studies asynchronous sensor processing and includes filtering. [RTAS 2010](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/rtas10batching.pdf). | Do measured exact-FIR cost menus produce a meaningful failure of strong simple online batching policies under a justified arrival envelope? | **Lower priority.** Reject if largest-safe/deadline-flush batching with profiled kernels nearly exhausts the opportunity, or gains require invented migration/sleep costs. Irregular arrivals alone are not a gap. [Detailed screen](fir-gap-deadlines.md). |
| Intermittent execution | Crash-consistent tasks, resumable convolution, adaptive task granularity and calibrated FIR accelerator tiles. [SONIC/TAILS](https://g-ram.github.io/files/sonic_asplos_2019.pdf), [Chinchilla](https://www.usenix.org/system/files/osdi18-maeng.pdf), [Coala](https://repository.tudelft.nl/file/File_3355f89a-63cf-4a0d-a70c-9b75e3e140ed). | Can persistence/recovery reverse the ranking of exact direct, folded and transposed realizations at equal per-sample output visibility, beyond an obvious wide-state write penalty? | **Defer.** It needs a separately justified persistence and recovery model. Reject if a persistent input ring plus tuned continuation dominates, or the crossover comes only from arbitrary write costs, lost inputs or weaker output semantics. [Detailed screen](fir-gap-intermittent.md). |

The source sets do not establish that these narrower questions are globally unanswered. Their status is **candidate empirical questions**, not secured original topics. A generic FIR generator, online batch scheduler or crash-safe wrapper should not be presented as the invention.

## Recommended next question and probe

> Can cross-output constant-product sharing improve complete, bit-exact FIR software on a small scalar processor after the required state widths and memory traffic are counted, and do established generation/scheduling approaches miss any reproducible opportunity?

Why this is the first probe: it keeps the fixed coefficients, exact final quantizer and existing continuous-execution setting. Deadline and intermittent proposals introduce additional workload or hardware assumptions before they establish a contribution. This is a feasibility/research-value judgment, not evidence that code generation is more novel.

The key structural distinction is important. A direct dot product multiplies different delayed samples; conventional multiple-constant multiplication shares work among several constants multiplying the **same** sample. Cross-output or transposed organization can expose that sharing, but retains partial results and changes memory traffic. Symmetric folding already reduces products using a different organization. These deductions follow from the FIR equations and the MCM definition in the [Hcub paper](https://spiral.ece.cmu.edu/pubs/synth.pdf); neither identity is proposed as new.

Proposed bounded probe, not yet executed:

1. Use one existing symmetric application-motivated filter, the existing nonsymmetric control, and a tiny coefficient example solely for debugging. Keep the original full-range and ADC contracts explicit; choose diagnostic cases before inspecting their new costs.
2. Reuse existing SCM/MCM graphs. Represent every intermediate and retained state as an exact integer linear form; certify its range, pre-additions and shifts. Count state loads/stores and code/RAM requirements. Compare direct, folded and input-centric/transposed organizations without assuming their savings combine.
3. Establish optimistic costs for specified realizations under the pinned target's actual multiplier configuration. Treat these as opportunity screens, not universal lower bounds on every possible FIR implementation. If no credible headroom remains, stop before implementing a generator.
4. If headroom survives, hand-implement only the few diagnostic realizations, preserving all output bits, startup, retained history and short-block behavior. Compare with coefficient-specialized direct code, the strongest valid folded and CMSIS variants, and established graph/schedule alternatives. Include the wrappers and recurring state costs.
5. Separate three possible outcomes: no performance opportunity; an engineering improvement explained by established methods; or a specific inadequacy in the strongest existing approaches with a potentially substantive new remedy or empirical finding. Only the third supports advancing a new contribution claim. An unexpected result still needs a focused closest-work check.

Do not build a general optimizer, train a replacement selector or expand the full experimental grid before this gate. A small successful kernel is evidence of opportunity; it is not by itself the paper's originality argument.

## Additional temporal-contract check

Adding a bound on consecutive input differences is not a clean novelty escape. Chang and Jen's [1998 university publication record](https://scholar.nycu.edu.tw/en/publications/low-power-fir-filter-realization-with-differential-coefficients-a-2/) describes differential inputs/coefficient differences for low-power FIR realization; the [indexed primary paper](https://dihana.cps.unizar.es/proceedings/ICASSP/1998/pdf/author/ic982260.pdf) explicitly connects differential input with reduced word length. [2017 slope-bound verification case studies](https://www.sciencedirect.com/science/article/abs/pii/S1477842417300246) also cover value/slope reasoning. Only indexed primary abstracts/text were available in this follow-up; direct full-text retrieval failed. These are overlap warnings, not a completed mechanism-equivalence audit. Neither input differencing nor a newly named temporal contract currently establishes a contribution.

## Status of the current proposal

The [current proposal](../professor-topic-proposal.md) remains a documented empirical baseline, including its corrected selector result and explicit novelty boundary. This screen neither invalidates those reported experiments nor converts a replacement candidate into an approved final topic. The immediate decision is **one targeted code-generation/state-cost probe**, with the three broader ideas retained as literature-screened alternatives rather than promised contributions.

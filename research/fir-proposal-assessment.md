# Focused assessment of the current FIR proposal

19 October 2026. Read the current [proposal](../professor-topic-proposal.md), [validation findings](fir-selection-validation-findings.md) and [novelty audit](fir-current-novelty-audit.md). This note independently checks three closest primary sources; it does not rerun experiments or constitute an exhaustive novelty search.

**Verdict:** The proposal is a credible college empirical research project with original experimental work and a reproducible artifact. It currently demonstrates neither a new FIR algorithm nor a substantial field-level discovery. Those are different standards: an original contribution can be carefully obtained empirical evidence, but its significance must be argued against what existing work already teaches. The proposal now makes that distinction responsibly.

## What the source check confirms

| Primary source inspected | Established result and consequence |
|---|---|
| [Arm CMSIS-DSP v1.14.4 FIR documentation](https://arm-software.github.io/CMSIS-DSP/v1.14.4/group__FIR.html), full official page | Fast Q15 retains product precision in a 32-bit accumulator that can wrap; standard Q15 uses 64-bit accumulation. Block-state storage and an odd-length zero-padding workaround are documented. Thus numerical-domain tradeoffs and the practical padded baseline already exist; the project correctly studies and checks their consequences. |
| Gačić, Püschel and Moura, [*Fast Automatic Software Implementations of FIR Filters*](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf), author-hosted paper, especially abstract and introduction | SPIRAL searches FIR algorithm/coding alternatives, including loop unrolling and blocking, for platform performance. Architecture and data flow matter beyond arithmetic counts. The present failures of a range/symmetry-only selector therefore fit established mechanisms; demonstrating them locally does not establish a new optimization principle. |
| Ménard and Sentieys, [*DSP Code Generation with Optimized Data Word-Length Selection*](https://link.springer.com/chapter/10.1007/978-3-540-30113-4_16), publisher abstract only | Processor-aware word-length selection minimizes execution time under an accuracy constraint, accounting for subword and multiple-precision instructions. The proposal's exact-output constraint is a meaningful scope distinction, but processor-aware width optimization itself is established. Full-paper equivalence or a precise unaddressed gap cannot be concluded from this abstract. |

These sources do not prove that the exact joint Q15/Cortex-M0 experiment has appeared before. They do show why combining range proofs, folding and generated-code inspection is insufficient by itself to support a first-of-kind claim. That is an assessment inferred from the sources, rather than a claim of exhaustive literature coverage.

## What remains project-reported

The corrected **77/108** modeled-energy winner agreement, **5.25% mean / 51.83% worst overhead**, **570 executions** and **292,410 matching outputs** are reported by the [local validation findings](fir-selection-validation-findings.md). They were not independently reproduced here. They quantify a bounded negative result: arithmetic admission alone does not choose the cheapest valid member of this tested candidate set. Repeated compiler/block/contract groups are not 108 independent applications. The exact-output checks support artifact correctness; they do not validate physical energy or establish novelty.

The result worth retaining is the combination of explicit legality, fair library controls, complete-stream accounting and explained counterexamples. Its strongest defensible claim is a controlled characterization with reusable evidence. The simple selector's failure is less compelling as a standalone research discovery because tuned library behavior and state costs already provide expected counterexamples.

## Most useful immediate next step

Take a short evidence-based contribution statement to the professor now: one question, the corrected negative result, two concrete generated-code/state-cost counterexamples, and the three nearest precedents above. Settle whether the college assessment accepts an empirical characterization and reproducible artifact as the contribution. More rows or retuning this rule on inspected cases would not resolve that requirement. If a new algorithm is mandatory, first identify a specific unresolved problem that these established methods cannot address; the current proposal has not yet supplied one.

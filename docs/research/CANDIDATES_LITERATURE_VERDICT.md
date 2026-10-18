# Literature verdict on the two candidate questions

Assessed 19 October 2026. This extends the
[initial brainstorm](./RESEARCH_QUESTION_BRAINSTORM.md). Primary papers, author
copies, official proceedings, repositories and maintainer records were screened.
The two detailed audits record inspected sections and unresolved access limits:
[candidate A](./CANDIDATE_A_LITERATURE_CHECK.md) and
[candidate B](./CANDIDATE_B_LITERATURE_CHECK.md).

## Assessment

**Neither candidate is a confirmed unoccupied research gap. Candidate A is the
better-supported option for a small independent empirical study. Candidate B's
broad new-method claim is particularly weak and needs a benchmark/evaluation
reframing.** These are our judgments of the inspected evidence, not claims that
all possible related work has been exhausted.

| Candidate | Literature verdict | Remaining possible contribution | Recommendation |
|---|---|---|---|
| A: energy-estimator reliability on unfamiliar code | Energy bounds, safety margins, training-support problems, code deduplication and selective prediction all have precedents | Independently establish a useful reliability boundary and compare support policies against strong margins on genuinely separated measured code | Conditionally retain as replication/evaluation; no new-model development yet |
| B: contract-aware state/buffer/call testing of DSP libraries | Both generic sequence-based methods and DSP-specific structured testing exist; upstream tests already observe more than output values | A reproducible historical-defect benchmark and fair comparison isolating generator value from oracle value | Reframe; do not claim a new technique from combining existing ingredients |

## A: what changed after the deeper check

[WORTEX](https://drops.dagstuhl.de/storage/01oasics/oasics-vol121-wcet2024/OASIcs.WCET.2024.1/OASIcs.WCET.2024.1.pdf)
already removes duplicate blocks after register normalization and evaluates
whole programs. [Huybrechts et al., 2021](https://www.mdpi.com/1996-1073/14/13/3914)
already discusses sparse training support and safety margins for energy estimates.
Thus we cannot motivate A by asserting that these issues were ignored.

Broader uncertainty methods also have close precedents: [Pitot, 2025](https://proceedings.mlsys.org/paper_files/paper/2025/hash/40b8fb4f90004405e14b1ede6ab42373-Abstract-Conference.html)
provides conformal runtime bounds; [MPORA, 2026](https://drops.dagstuhl.de/storage/00lipics/lipics-vol375-ecrts2026/html/LIPIcs.ECRTS.2026.17/LIPIcs.ECRTS.2026.17.html)
addresses shifting runtime inputs; and [KMM-CP, 2026](https://proceedings.mlr.press/v337/laghuvarapu26a.html)
describes selective conformal correction under limited support overlap.
These are adjacent methods, not direct findings about the proposed MSP430
energy experiment, but they rule out claiming the general uncertainty mechanism.

**A question still worth a feasibility check:**

> After preserving the published preprocessing and deduplication, do residual
> source/instruction-pattern differences materially change held-out energy-bound
> violations, and can a frozen support policy improve the violation–inflation–
> retention trade-off beyond simple calibrated safety margins?

The inspected sources do not report this exact comparison. That is a bounded
finding, not evidence that changing the split alone creates a contribution.
Start with artifact/schema reconciliation and baseline reproduction. Then
determine whether meaningful residual overlap or shift exists without using
test energy labels to choose groups. Do not presuppose that reliability will
degrade. A useful result requires more than unsurprising failure on contrived
outliers or a policy that rejects almost everything.

## B: what changed after the deeper check

[Huuhtanen et al., 2015](https://doi.org/10.1109/ICST.2015.7102583)
already proposes algebraic/domain tests for FIR and IIR examples.
[MF++, 2022](https://andreil.eu/papers/icst22.pdf) synthesizes equivalent API-call
sequences from specifications. [STITCH, 2026 preprint](https://arxiv.org/html/2602.18689v1)
also models cross-call state and usage constraints. The coordinator inspected
its full-text method and evaluation setup, extending the abstract-only screening
explicitly recorded in the background B audit; no DSP-specific result is inferred.

The current [official FIRF32 tests](https://github.com/ARM-software/CMSIS-DSP/blob/main/Testing/Source/Tests/FIRF32.cpp)
execute consecutive calls and check output tails as well as numerical agreement.
This does not mean every state-buffer error is caught, but it makes an
output-only characterization inaccurate. [PR #317](https://github.com/ARM-software/CMSIS-DSP/pull/317)
documents a Q15 state-size issue investigated with host guard pages and ASan;
such existing checks must be serious baselines, not omitted competitors.

**A possible reframe, pending corpus feasibility:**

> Across independent historical DSP defect families, which documented memory
> and state observations add detection beyond existing tests and sanitizers,
> and does contract-aware generation still help when competing generators
> receive the same strong observations and execution budget?

Separate test generation from failure detection. An apparent benefit that comes
only from adding a guard page does not demonstrate a better generator. Recover
exact buggy/fixed versions and legal contracts before counting a defect;
disputed issues and behavior-preserving cleanup are not confirmed bug pairs.
Helium-specific fixes need a supported execution path, not the existing M0
simulator. The screened corpus does not yet establish enough independent
state/history defects for a convincing evaluation.

## Decision before investing further

The literature check supports **an inexpensive feasibility audit of A**, not a
commitment to a new energy estimator. Keep B only if a diverse executable corpus
and a specific oracle blind spot can first be demonstrated. Neither combining
known methods nor using a different library or dataset establishes originality.
If a novel-method contribution is required, neither present formulation has
cleared that bar.

This turn performed literature/artifact inspection only. No new energy model
was trained, no historical DSP bug was reproduced, and no comparative gain was
measured. No exhaustive forward-citation graph, all-database search or proof of
absence was obtained. Read the individual audits for full-text versus abstract
access, mutable-source limits and concrete stop conditions.

# Research-question shortlist after the negative result

Investigated 19 October 2026. Constraints: no target hardware; the user is open
to broader embedded systems. This is a research brainstorm, not a validated gap
or an implementation plan. The previous
[bounded result](./BOUNDED_STUDY_FINDINGS.md) remains unchanged.

**Deeper literature check:** read [the updated verdict](./CANDIDATES_LITERATURE_VERDICT.md)
before treating this initial shortlist as a research gap. Both candidates have
substantial prior art. A remains a conditional replication/evaluation candidate;
B needs a comparative benchmark framing, with strong existing generators and
memory checks. Neither has established novelty.

## Recommendation

Prioritize a small feasibility audit of **energy-estimator reliability on public
hardware measurements**. Keep **testing stateful DSP-library contracts** as the
strongest alternative if moving away from energy. Both have independently
checkable outcomes; neither needs our virtual circuit to supply its own truth.
The [background literature note](./RESEARCH_QUESTION_PRIOR_ART.md) gives additional
energy-model sources and access limits. The rankings below are our assessment.

| Direction | Evidence we could use without new hardware | Main risk | Priority |
|---|---|---|---|
| Reliability of empirical energy bounds on unfamiliar code | Public measured basic blocks and instruction records | Prior work may already establish the important reliability boundary | First feasibility check |
| Testing state/history/memory contracts in DSP libraries | Reference semantics, official regression fixes, sanitizers and emulation | Ordinary sanitizers or existing tests may already catch the proposed failures | Serious alternative |
| Firmware-emulation/fuzzer validity | Published firmware bug oracles and emulator artifacts | Crowded field, substantial setup, ambiguous hardware fidelity | Defer without a sharper question |

## A. When should an energy estimator decline to give a confident answer?

**Candidate question:**

> How does the empirical reliability of microcontroller energy bounds change
> when evaluation code comes from unseen sources and instruction-pattern
> families, and can a predictor that flags unsupported cases reduce
> underestimation without making its bounds or rejection rate impractical?

There is an accessible starting point rather than a hypothetical future dataset:
the authors' [MSP430FR5969 basic-block dataset](https://zenodo.org/records/11066623)
lists measured energy/time and instruction JSON with source identifiers.
It concerns MSP430, so our Cortex-M coefficients cannot be transferred to it.
Unrelated blocks also cannot stand in for equivalent program implementations.

**Local access/schema audit:** both CSV and instruction archive were downloaded
and matched the repository's MD5 checksums. The CSV has 30,085 unique block IDs
and 9,390 distinct file-ID prefixes; the archive contains 13,791 source JSON
files, so archive files must not be counted as measured groups without joining.
These are observations of the downloaded artifact, not a trained-model result.
The temporary inspection files are under
`/tmp/esproject-question-audit-20261019`.

Two replication questions need resolution: all CSV rows give `nb_samples=40`,
whereas the WORTEX paper describes 100 measurements; and `energy_per_inst`
agrees with `max_energy/nb_inst` within rounding in every CSV row, although the
record describes it using average energy. This can reflect artifact/documentation
version differences. Derive targets explicitly from named raw columns and resolve
the mismatch before claiming a faithful reproduction. These observations do not
by themselves invalidate the published results or establish a new contribution.
The verified file digests are `fb73e68156711747bd2eeebb926b0c15` (CSV) and
`230bbc59baff4c02a1af2ebd1d2b4729` (instruction archive).

**Closest precedent:** [WORTEX, WCET 2024](https://drops.dagstuhl.de/storage/01oasics/oasics-vol121-wcet2024/OASIcs.WCET.2024.1/OASIcs.WCET.2024.1.pdf)
already evaluates quantile models at block level and on four whole programs.
Neither energy prediction nor evaluation on new programs is the proposed novelty.
Our proposed distinction is a controlled stress test of empirical reliability
under source/template separation, followed by a useful unsupported-case policy.
Whether that adds enough beyond prior work remains unresolved.

**Tentative hypothesis, not a result:** estimates calibrated on mixed code may
underestimate more often on deliberately separated instruction-pattern families;
an unsupported-case policy may reduce those violations at a useful retained
fraction and bound inflation. We must allow either part to fail.

**Fair test:** first reproduce published quantile baselines. Compare random-block,
source-group and near-duplicate/template-separated splits with untouched test
groups and separate calibration. Compare simple instruction-count models, fixed
safety factors and feature-distance rejection before considering more elaborate
uncertainty machinery. All prospective predictors receive the same code-derived
inputs. A baseline using measured execution time gets a separate, explicitly
different information budget. Report violations, overestimation and retained
fraction together, with dependence handled by source/cluster.

**Evidence boundary:** observed dataset maxima are not certified maxima over all
inputs and states. A calibrated interval method does not automatically guarantee
coverage under a changed code distribution. Any guarantee needs its assumptions;
otherwise report empirical coverage within the tested distribution.

**Stop early if:** metadata cannot support meaningful separated groups; the
published baseline cannot be reproduced adequately; the difference is explained
only by trivial length extrapolation; or the fallback cannot beat a fixed safety
factor at comparable retained coverage. Finding no degradation could still support
a useful replication, but we cannot promise publication value.

## B. Which tests expose DSP-library failures that output comparisons miss?

**Candidate question:**

> At equal testing cost, do tests generated from legal state, buffer and call
> contracts expose more reproducible DSP-library defects than random signal
> tests and numerical output comparisons, beyond what sanitizers already find?

A concrete motivation is the official [CMSIS-DSP FIR history-copy fix #245](https://github.com/ARM-software/CMSIS-DSP/pull/245).
The discussion reports that ordinary tests missed the problem because the
affected data could be overwritten on the next call. This is a known, fixed
floating-point Helium issue, not a new discovery or evidence of a Q15/M0 defect.
The existing M0 simulator cannot execute its Helium path.

**Prior-art boundary:** fixed-point filter verification is well established;
[DSVerifier](https://ssvlab.github.io/dsverifier/) already addresses numerical
properties. [CMSIS-DSP's own test generators](https://github.com/ARM-software/CMSIS-DSP/blob/main/Testing/PatternGeneration/FIR.py)
are an essential baseline, not evidence that the library is untested.
The proposed research would concern comparative test effectiveness for actual
library contracts, not inventing differential testing or finding overflow.

**Tentative hypothesis:** tests that vary valid streaming schedules and buffer
boundaries, and inspect state/memory as well as outputs, expose a meaningful
additional class of defects at fixed test cost. This could be false if existing
tests plus sanitizers already detect the same defects efficiently.

**Fair test:** assemble executable historical buggy/fixed pairs from more than
one function or implementation path. Separate these from seeded mutations.
Compare official tests, randomized values with sanitizers, differential tests
and contract-generated sequences under equal runtime/call budgets. Keep defect
families out of test-generator tuning. Report unique root causes, false alarms,
time to discovery and minimized counterexamples, not only crash counts.

Only use block partitioning, aliasing, state sharing or buffer layouts when the
specific API/backend permits them. Different rounding, saturation and fast-kernel
preconditions can legitimately change outputs. For example,
[Arm's Q15 FIR source](https://github.com/ARM-software/CMSIS-DSP/blob/main/Source/FilteringFunctions/arm_fir_q15.c)
uses wide accumulation and output saturation; our wrapping FIR contract cannot
be its universal numerical oracle. Pin versions and instruction paths before
making cross-implementation comparisons.

**Stop early if:** there is no diverse executable defect corpus within available
emulators/host builds; results depend on violating documented preconditions;
or the method adds nothing beyond ordinary sanitizers and boundary canaries.
A single recovered historical bug or high mutation score is insufficient to
claim a new testing method.

## C. Firmware emulation: a reserve direction, not a new gap yet

An appealing broad question is whether emulator/model assumptions change which
firmware bugs are observable. However, software-only firmware fuzzing already
has direct precedent in [Fuzzware, USENIX Security 2022](https://www.usenix.org/conference/usenixsecurity22/presentation/scharnowski).
[FirmReBugger, 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/duong)
and its [official artifacts](https://github.com/FirmReBugger/FirmReBugger) also
provide bug-based evaluation infrastructure. Creating another emulator or
counting crashes would not by itself distinguish a contribution.

Revisit only after identifying a specific model assumption and a reference
oracle that can establish whether its effects are correct. Agreement between
two emulators alone does not establish real-device correctness. This option
currently offers less reuse and a less bounded study than A or B.

## What to choose now

**A has the clearest independent evidence available for an inexpensive first
audit. B offers a more direct move into embedded software correctness.** Neither
is ready to be called an unpublished gap. The next decision is which question
is worth a small feasibility probe, not which untested hypothesis to defend.

Searches covered energy-bound generalization, uncertainty and public data;
CMSIS/DSP testing, fixed-point verification and state/history defects; and
software-only firmware evaluation. Primary records and code were preferred.
This was targeted screening, not an exhaustive citation search. Absence of a
matching search hit does not establish novelty, and this turn ran no new model
comparison or bug-finding experiment.

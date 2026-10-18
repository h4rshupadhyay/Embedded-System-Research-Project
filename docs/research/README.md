# Research notes

These are dated assessments and experiment records. Earlier literature notes
describe earlier versions of the project; use the latest verdict and findings
below for the current position. Commands in these documents run from the
repository root.

## Current candidate questions

| Read | Purpose |
|---|---|
| [Combined literature verdict](./CANDIDATES_LITERATURE_VERDICT.md) | Latest assessment: neither candidate has established novelty |
| [Candidate A literature check](./CANDIDATE_A_LITERATURE_CHECK.md) | Energy-bound reliability on unfamiliar measured code; conditional empirical study |
| [Candidate B literature check](./CANDIDATE_B_LITERATURE_CHECK.md) | DSP state/buffer/call testing; needs a strong comparative benchmark framing |
| [Initial brainstorm](./RESEARCH_QUESTION_BRAINSTORM.md) | Candidate questions, dataset audit and feasibility gates |
| [Initial candidate prior art](./RESEARCH_QUESTION_PRIOR_ART.md) | Supporting energy-model sources and access limits |

The planned investigation is split between candidate A and peer investigation
of candidate B. No new candidate model or DSP testing framework is implemented.

## Completed simulation and protocols

| Read | Purpose |
|---|---|
| [Bounded-study findings](./BOUNDED_STUDY_FINDINGS.md) | Complete negative result: zero selection benefit in 207 primary conditions |
| [Bounded-study protocol](./BOUNDED_STUDY_PROTOCOL.md) | Fixed grid, replay exclusion, criterion and limits |
| [Energy-model documentation](./ENERGY_MODEL.md) | Equations, assumptions and reproduction commands |
| [Physical hypothesis protocol](./HYPOTHESIS_TEST_PROTOCOL.md) | Proposed hardware study; remains unexecuted |
| [Research-gap assessment](./RESEARCH_GAP.md) | Evolution and qualification of the original claims |

Canonical data and frozen provenance are in [results](../../results/README.md).
Archived generated summaries sometimes name protocols by filename without a
path; those protocols now live in this directory. The recorded model/profile
sources and result data have been retained without rewriting their hashes.

## Earlier literature and historical findings

- [Literature audit](./LITERATURE_AUDIT.md)
- [Physical-effects literature](./PHYSICAL_EFFECTS_LITERATURE.md)
- [Narrow-gap literature check](./NARROW_GAP_LITERATURE_CHECK.md)
- [Deep supply prior art](./DEEP_SUPPLY_PRIOR_ART.md)
- [Historical FIR findings](./FINDINGS.md)

The historical sweep predates the FIR correctness fixes. Its rank reversals and
cycle-gap observations are not evidence for equivalent implementations or a
validated selection threshold. These records are retained for traceability.

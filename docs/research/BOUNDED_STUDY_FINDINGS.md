# Outcome of the bounded broader simulation

Completed 18 October 2026 under the
[fixed follow-up protocol](./BOUNDED_STUDY_PROTOCOL.md).
**Recommendation: stop the current model as a route to an implementation-selection
contribution in this simulated FIR domain.** The predefined continuation criterion
was not met. The physical regulator-history hypothesis remains untested.

## What was evaluated

The [full result](../../results/bounded_energy_study/SUMMARY.md) covers 24 workload
configurations: taps 7/16/31, blocks 8/64, and O1/O2/O3/Os. The already inspected
16/64/O2 workload was a replay control, excluded from the primary analysis.
The other 23 configurations each had nine supply/cadence conditions, giving
**207/207 valid primary conditions**, nine valid control conditions, and 648
implementation/circuit evaluations. There were no recorded failures.

All three compiled implementations passed the output-checksum gate for every
workload. The six synthetic calibration pulses, supply parameters and history
fits were fixed before scoring any FIR cases. The circuit and fitting method
were unchanged from the initial experiment.

## Results

| Primary metric | Steady baseline | History predictor |
|---|---:|---:|
| Reference-best choices | 207/207 | 207/207 |
| Largest selection penalty | 0 J/job | 0 J/job |
| Mean absolute energy prediction error | 0.088672% | 0.101469% |

The predictors made **zero different choices**, so mean reference-energy savings
from using history were **0%**, below the fixed illustrative 1% criterion.
The history predictor's better prediction error in the original workload did
not persist in the broader set: its average error was slightly worse here.
Both error figures are relative to an uncalibrated virtual circuit, not hardware
accuracy claims.

This was not simply a test where UNROLLED always won. The common selected and
reference-best variant was UNROLLED in 135 primary conditions, CIRCULAR in 54,
and DIRECT in 18. Which variant was best changed with the workload; adding
history never improved its selection.

There were 18/207 conditions whose baseline best-two energy gap was at most 1%.
These share a small number of workload configurations and are not independent
experimental replicates. The smallest gap was 0.740245%; much closer ties remain
outside the observed coverage. No confidence interval or universal threshold
follows from these deterministic cases.

## Meaning for the project

We now have evidence against the *practical value of this particular added
history predictor for this fixed simulated benchmark family*. We should not
keep extending this same model solely to seek a favorable reversal. Neither
better training fit nor changing supply parameters after the result would
establish our proposed contribution.

This does not establish that physical regulator history is irrelevant. The
model still assumes constant active power per job, one deterministic input
family, a bidirectional averaged buck and illustrative parameters. It has no
measured instruction-current trace, identified LDO behavior or hardware evidence.
Any renewed study should have an independently motivated change in evidence
or question, such as calibrated demand/supply traces; this run alone does not
validate a replacement research gap.

The corrected FIR implementations, profiling harness and negative result remain
useful research infrastructure. The current evidence supports a reproducible
limited negative result, not a new validated energy-selection method or a claim
of publishable novelty.

## Verification and artifacts

All **30 tests passed**, including the real mini-study, checksum/equivalence,
conservation, lossless control, decision scoring and existing-output preservation.
Independent post-run checks verified source/input/profile hashes, simulator
consistency, calibration preceding profiles, full coverage and decision savings
recomputed directly from reference energies. The largest circuit conservation
residual was 9.04e-18 J over a complete pattern.

- [Frozen inputs and source hashes](../../results/bounded_energy_study/frozen_inputs.json)
- [Frozen pulse-only fits](../../results/bounded_energy_study/frozen_fits.json)
- [Complete machine-readable report](../../results/bounded_energy_study/report.json)
- [Verification record](../../results/bounded_energy_study/verification.json)
- [Condition results](../../results/bounded_energy_study/conditions.csv)
- [Implementation predictions](../../results/bounded_energy_study/predictions.csv)

The initial reports and historical sweep CSVs were retained. Reproduce with a
fresh directory using `make bounded-study STUDY_OUTPUT=results/new_bounded_run`.

# Initial software pilot

[sim_pilot.json](./sim_pilot.json) records the first corrected streaming workload:
three variants, four jobs each, 16 taps, 64 output samples/job, GCC `-O2`.

| Variant | Marked cycles/job | FIR MULS/job | Whole-stream checksum |
|---|---:|---:|---|
| Direct | 17,528 | 1,024 | `b0241172` |
| Pointer/circular | 17,338 | 1,024 | `b0241172` |
| Unrolled ×4 | 17,018 | 1,024 | `b0241172` |

All four jobs had the same marked duration within each variant in this run.
Checksums match the independent integer convolution. Marked regions contain the
FIR call and boundary overhead; stream preparation and output hashing are outside.
The JSON records individual C1–C6 values and source/binary/simulator hashes.

The common 35,056-cycle period is a logical projection, chosen as twice the
slowest marked interval. It is **not an executed periodic schedule**. CPU sleep,
wake-up, setup time between releases, current waveforms, regulator recovery and
source energy are unmodeled. This result establishes the software prerequisite;
it does not test the regulator-history hypothesis or establish an energy winner.

Reproduce using a new output filename:

```bash
make test
make pilot PILOT_OUTPUT=results/reproduced_pilot.json
```

The runner refuses to overwrite an existing report. The original
`experiment_results.csv` is retained as historical evidence and was not regenerated.

## Conditional supply-model experiment

[energy_hypothesis/SUMMARY.md](./energy_hypothesis/SUMMARY.md) contains the next
stage: a steady-loss baseline and fitted history predictor scored against a
synthetic averaged-buck circuit, using this pilot's counters. Wake/sleep demands
and supply parameters are illustrative. All nine initial cases select UNROLLED
with both predictors, so selection improvement is zero. See
[ENERGY_MODEL.md](../docs/research/ENERGY_MODEL.md) for equations, limits and reproduction.
These circuit simulations do not turn the software pilot into a physical
measurement or validate the hardware hypothesis.

## Bounded broader study

[bounded_energy_study/SUMMARY.md](./bounded_energy_study/SUMMARY.md) reports 24
workload configurations: 23 primary configurations (207 valid supply/cadence
conditions) and the original-workload control (nine valid conditions). Both
predictors selected the reference-best variant in every case, with zero selection
savings. See [the interpretation](../docs/research/BOUNDED_STUDY_FINDINGS.md) for the decision,
prediction errors, coverage limits and verification links. The fixed plan and fits
were saved before FIR evaluation. This remains uncalibrated simulation.

# Bounded follow-up simulation

Declared before generating the broader study results, 18 October 2026. The
initial nine-case result was already known and showed zero selection benefit.
This follow-up asks whether that result persists across a fixed broader FIR
workload set. It does not change the circuit or search supply parameters for
a reversal. The user has simulation only.

## Frozen scope and decision

The [machine-readable plan](../../configs/bounded_energy_study.json) specifies the
Cartesian product of taps {7,16,31}, block sizes {8,64}, and compiler settings
{O1,O2,O3,Os}, with four streaming jobs and three equivalent variants each.
The 16-tap, 64-output, O2 workload is a replay control excluded from the primary
endpoint because its result was already inspected. The other 23 workloads give
207 primary supply/cadence conditions; the control contributes nine separately
reported conditions. There are 648 planned implementation/circuit evaluations.
Tail lengths exercise the unrolled implementation's remainder path.

Keep every parameter, six calibration pulses, time-constant grid, three
resistances and three cadence factors in
[the existing supply configuration](../../configs/energy_model.json). Fit once per
resistance using calibration pulses only, and freeze all fits before evaluating
any FIR workload. Every compiled profile must pass the existing independent
checksum/equivalence gate. Save the plan, configuration and source hashes before
profiling; retain all failures and partial evidence.

Primary endpoint: mean over the 207 predefined non-control conditions of
`(reference_energy(B_choice) - reference_energy(H_choice)) / reference_best_energy`.
Use the existing 1e-10 J/job numerical tie tolerance and lexical tie-break.
Continue this model only if all primary conditions are valid and mean savings
exceed the existing illustrative 1% criterion. If all are valid but the mean is
at most 1%, recommend stopping this model as an implementation-selection method
in this simulated domain. Missing/invalid conditions produce an incomplete
result, not a positive claim or a confident negative conclusion. No statistical
confidence interval follows from this deterministic grid.

Secondary endpoints: changed choices; improved/worsened choices; both models'
reference-best agreement and energy regret; mean absolute prediction errors;
and near-tie cases where the best and second-best baseline energies differ by
at most 1%. Report the near-tie denominator even when zero, without restricting
the primary analysis to favorable subsets. Do not modify the grid or threshold
after inspecting outcomes. This is a local frozen analysis, not an external
preregistration or a guarantee of novelty.

## Interpretation limits

This broadens workload and compiler coverage while retaining the existing
constant-power-per-job reconstruction. It does not provide finer measured
current traces, data-dependent switching behavior, new kernels, an LDO model,
package comparisons or hardware calibration. A null result limits this specific
model and benchmark family. A positive result would justify better demand
traces and physical characterization; it would not establish the physical
hypothesis or publishable novelty. No result authorizes tuning parameters until
a reversal appears.

## Reproduce

```bash
make test
make bounded-study STUDY_OUTPUT=results/my_bounded_study STUDY_WORKERS=2
```

Use a fresh output directory. The runner requires the existing Arm tools and
patched simulator. `frozen_inputs.json` is written before calibration/profiling;
`frozen_fits.json` is written before evaluating the first FIR workload. Raw
profiles and per-workload results remain available if a run is interrupted.
The final `report.json`, `conditions.csv`, `predictions.csv` and `SUMMARY.md`
retain both evaluation and replay-control rows with explicit role labels.

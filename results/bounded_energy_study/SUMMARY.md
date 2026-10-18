# Bounded broader simulation result

**Physical hypothesis: not tested. All supply parameters/reference energies are synthetic.**

Primary coverage: 207 / 207 conditions.
Mean selection savings: 0.000000%; fixed useful-improvement criterion: 1.00%.
Recommendation: `stop_current_model_in_simulated_domain`.

Changed choices: 0; improved: 0; worsened: 0.
Baseline/reference-best agreement: 207 / 207.
History/reference-best agreement: 207 / 207.
Near-tie conditions (baseline best-two gap ≤ 1.00%): 18 / 207.

The already inspected original workload is a replay control, excluded from these primary metrics.

| Workload | Role | Valid conditions | Mean selection savings |
|---|---|---:|---:|
| t16_b64_O1 | evaluation | 9 | 0.000000% |
| t16_b64_O2 | replay_control | 9 | 0.000000% |
| t16_b64_O3 | evaluation | 9 | 0.000000% |
| t16_b64_Os | evaluation | 9 | 0.000000% |
| t16_b8_O1 | evaluation | 9 | 0.000000% |
| t16_b8_O2 | evaluation | 9 | 0.000000% |
| t16_b8_O3 | evaluation | 9 | 0.000000% |
| t16_b8_Os | evaluation | 9 | 0.000000% |
| t31_b64_O1 | evaluation | 9 | 0.000000% |
| t31_b64_O2 | evaluation | 9 | 0.000000% |
| t31_b64_O3 | evaluation | 9 | 0.000000% |
| t31_b64_Os | evaluation | 9 | 0.000000% |
| t31_b8_O1 | evaluation | 9 | 0.000000% |
| t31_b8_O2 | evaluation | 9 | 0.000000% |
| t31_b8_O3 | evaluation | 9 | 0.000000% |
| t31_b8_Os | evaluation | 9 | 0.000000% |
| t7_b64_O1 | evaluation | 9 | 0.000000% |
| t7_b64_O2 | evaluation | 9 | 0.000000% |
| t7_b64_O3 | evaluation | 9 | 0.000000% |
| t7_b64_Os | evaluation | 9 | 0.000000% |
| t7_b8_O1 | evaluation | 9 | 0.000000% |
| t7_b8_O2 | evaluation | 9 | 0.000000% |
| t7_b8_O3 | evaluation | 9 | 0.000000% |
| t7_b8_Os | evaluation | 9 | 0.000000% |

## Interpretation

This result covers the fixed FIR grid and flat per-job demand assumption only. It does not validate or generally reject the physical regulator-history hypothesis. There is no hardware calibration, finer instruction-current trace or statistical confidence interval. See BOUNDED_STUDY_PROTOCOL.md and frozen_inputs.json for the decision rule and scope.

Recorded failures: 0. All failures are retained in report.json.

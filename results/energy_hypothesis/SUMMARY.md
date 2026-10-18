# Conditional energy-model experiment

**Physical hypothesis: not tested. All supply parameters and reference energies are synthetic.**

Valid conditions: 9 / 9.
Mean reference-energy improvement from history choices: 0.000000%.
Mean absolute energy prediction error: steady 0.050645%, history 0.019618%.
Configured useful-improvement threshold: 1.000% (illustrative).
Conditional result: `no_material_simulated_improvement`.

| Condition | Steady choice | History choice | Reference best | Improvement |
|---|---|---|---|---:|
| R=0;period_factor=1.1 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |
| R=0;period_factor=2 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |
| R=0;period_factor=5 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |
| R=0.3;period_factor=1.1 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |
| R=0.3;period_factor=2 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |
| R=0.3;period_factor=5 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |
| R=2;period_factor=1.1 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |
| R=2;period_factor=2 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |
| R=2;period_factor=5 | UNROLLED | UNROLLED | UNROLLED | 0.000000% |

No measurement confidence interval is inferred from these deterministic simulations.

## Limitations

- Event weights are assumed nominal MCU-pin energy; boundary/applicability unvalidated.
- Within-job demand is flat; preparation and first-call MCU behavior are not modeled.
- Wake/sleep powers and all circuit parameters are illustrative, not measured.
- Reference is a bidirectional averaged synchronous buck, not STM32 internal LDO.
- No switching ripple, switching loss, package inductance or temperature model.
- No physical significance test or uncertainty confidence interval follows from this grid.
- Invalid cases are excluded and listed; conclusions cover valid simulated conditions only.

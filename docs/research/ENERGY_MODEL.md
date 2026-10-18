# Runnable energy-hypothesis model

This experiment asks whether adding supply history improves the choice among
equivalent FIR implementations compared with a segmentwise steady-loss model.
It uses an independently integrated virtual circuit to score both predictors.
**All supply parameters and reference energies are synthetic. The physical
hypothesis in [the protocol](./HYPOTHESIS_TEST_PROTOCOL.md) remains untested.**

## Run and inspect

```bash
python3 -m pip install -r requirements-model.txt
make test
make energy-model MODEL_OUTPUT=results/my_energy_experiment

# Use a different corrected pilot or configuration:
python3 run_energy_hypothesis.py --profile results/sim_pilot.json \
    --config configs/energy_model.json --output-dir results/another_experiment
```

The output directory must be new; existing results are preserved. The model
requires Python, NumPy and SciPy. Running a supplied pilot does not require the
Arm tools; generating a new pilot does. This implementation uses SciPy's Radau
ODE solver, rather than SPICE. See [the configuration](../../configs/energy_model.json)
and [the first result](../../results/energy_hypothesis/SUMMARY.md).

| Output | Contents |
|---|---|
| `SUMMARY.md` | Decisions, selection benefit, prediction errors and limitations |
| `report.json` | Complete configuration, fitted parameters, invalid cases, input/source hashes |
| `conditions.csv` | Choices, reference winners, regret and improvement per condition |
| `predictions.csv` | Per-job predictions and circuit accounting for each implementation |

In predictions, fields ending in `_j_per_job` are per-job energies. Circuit
fields such as `raw_source_j`, `conduction_j`, `load_j` and `storage_delta_j`
are totals over the complete repeated pattern, containing all configured jobs.
All internal units are SI: seconds, watts, joules, volts, amperes, ohms,
henries and farads. Event weights alone are configured in nJ/event.

## Equal work and assumed demand

The input profile must be marked as simulation, contain at least two variants,
and pass the independent stream-checksum gate for its taps, block and job count.
The supplied pilot uses 16 taps, 64 outputs/job, four streaming jobs and `-O2`.
DIRECT, CIRCULAR and UNROLLED have the same output-stream checksum `b0241172`.

For each marked job, assumed active energy is `sum(weight[k] * C[k]) * 1e-9`.
Active duration is cycles/clock; dividing energy by duration gives a **constant
power for that job**. This reconstruction does not recover instruction-level
current transitions. The six weights come from the published model in
[EnergyAnalyzer §4.1](https://arxiv.org/html/2305.14968v2#S4.SS1).
Treating them as nominal MCU-pin energy is an unvalidated boundary assumption;
it must be checked before adding real converter losses to avoid double counting.

Each job has configured wake demand, active demand and sleep demand. Every
variant receives the same period, calculated from the longest active interval
plus wake duration, multiplied by the configured cadence factor. Faster jobs
therefore sleep longer. Defaults are 48 MHz, 20 µs wake at 5 mW, and 50 µW sleep.
These are illustrative assumptions, not executed sleep or measured startup
traces. Preparation, copying and checksum computation are excluded.

## Three distinct energy calculations

**Steady baseline B.** For every segment of duration Δt and demand P:

```text
I_nominal = P / Vref
E_B = sum Δt * [P + R * I_nominal² + Vin * Iq]
```

This includes nonlinear conduction loss and quiescent power, as well as the
same wake/sleep demand used by the other models. It is the exact equilibrium
loss expression for this virtual power stage; it has no additional fitted
history term. It is only a strong baseline within this restricted circuit,
which has no switching modes or explicit startup state machine.

**Virtual circuit reference.** The averaged bidirectional synchronous buck has
inductor current i, capacitor voltage v and feedback-integrator state z:

```text
e = Vref - v
i_ref = Kp * e + z
d = clip[(v + R*i + L*(i_ref - i)/tau_inner) / Vin, 0, 1]
L * di/dt = Vin*d - v - R*i
C * dv/dt = i - P/v
dz/dt = Ki * e          [frozen when saturation would worsen windup]
P_source = Vin*d*i + Vin*Iq
```

This is a chosen idealized control law, not an identified commercial regulator.
Averaged power-stage and feedback modeling are established techniques; see
[TI, Applying Digital Technology to PWM Control-Loop Designs, §III](https://www.ti.com/download/trng/docs/seminar/Topic_7_Hagen.pdf).
That source does not validate these parameter values or this controller.

Defaults are Vin=5 V, Vref=3.3 V, L=22 µH, C=10 µF, Iq=2 µA,
tau_inner=10 µs, Kp=0.2 A/V and Ki=2000 A/(V·s). The sweep uses R=0, 0.3
and 2 Ω. R is a lumped series loss, not package inductance or an LDO parameter.
The upstream ideal source can absorb returned energy; a real non-sinking
supply requires a different model.

The full demand pattern is repeated until its boundary state converges, up to
100 warmup periods. Warmup energy is excluded. The final interval records:

```text
ΔU = 0.5*L*(i_end² - i_start²) + 0.5*C*(v_end² - v_start²)
E_source_raw = E_load + E_R + E_quiescent + ΔU
E_reference = E_source_raw - ΔU
```

Conservation error, stored-energy correction and voltage range are reported.
The code rejects failed convergence, integration failure, excessive conservation
error and rail excursions outside ±20% nominal. It also requires an attainable
nominal operating point for every segment (`Vref + R*P/Vref < Vin`), preventing
static saturation error from masquerading as additional history. This is a
conservative scope restriction even if a brief overload could be ridden through.

**History predictor H.** With nominal demand current I=P/Vref:

```text
dq/dt = (I - q) / tau
F = integral (I - q)² dt       [A²s, exact periodic solution]
E_H = E_B + a*F               [a in ohms]
```

The time constant is selected from a fixed candidate grid; a is fitted by
least squares to reference-minus-baseline energy on six separate synthetic
pulse experiments. The bound `a >= -R` prevents negative total conduction loss.
Each supply resistance is characterized separately. The fit is frozen before
scoring FIR cases; FIR reference energies are never used for fitting. The
reference is the differential-equation circuit, not this fitted correction.
This separation checks conditional prediction, not independent physical truth.

## Decision and current result

For each condition, B and H choose their minimum-energy variant. Their choices
are scored with the circuit's reference energy:

```text
D = E_reference(B_choice) - E_reference(H_choice)
relative_improvement = D / min_variant(E_reference)
```

The report averages relative improvement equally over valid configured cases.
It also reports each choice's energy above the reference minimum. A numerical
tie tolerance of 1e-10 J/job and a lexical tie-break make decisions reproducible;
this is not a measurement noise floor. Nonpositive reference-energy cases are
invalid because relative errors are undefined. Invalid cases are listed and
excluded; if none remain, the run fails before creating output.

The default grid has three resistances and three cadence factors (1.1, 2, 5),
for nine conditions and 27 implementation evaluations. The illustrative useful
improvement threshold was set to 1% in the configuration before evaluation.
It is unrelated to the historical 0.1% cycle-gap claim and has no calibrated
application meaning. Do not tune it after observing a favorable result.

**First run: all nine cases were valid; B, H and the circuit all chose UNROLLED.
Selection improvement was 0%.** The history correction can reduce prediction
error without changing a choice. Thus these virtual FIR cases do not support
a useful implementation-selection gain from additional history. They neither
validate nor refute the physical hypothesis. Tests separately demonstrate that
equal-load-energy traces can have different circuit losses when their cadence
differs, and verify that a lossless circuit cannot create a benefit from losses.

The [bounded broader follow-up](./BOUNDED_STUDY_FINDINGS.md) subsequently tested
23 additional workload/compiler configurations plus the original replay control.
All 207 primary conditions again had zero selection benefit. Mean absolute
prediction error was 0.088672% for the steady baseline and 0.101469% for history,
so the original prediction-error improvement did not persist across this grid.
The fixed continuation criterion was not met; stop this model as a path to an
implementation-selection contribution in this simulated domain.

## Limits and next evidence

The tests cover steady equilibrium, lossless operation, energy conservation,
solver-tolerance convergence, exact filter integrals, unavailable operating
points, independent-reference decision scoring and output preservation.
Deterministic runs do not supply measurement confidence intervals or p-values.
The initial grid contains one FIR workload/compiler setting, not a general population
or a test of transfer to uncharacterized supplies.

There is no switching ripple/loss, diode emulation, capacitor ESR, temperature
dependence, package inductance, STM32 internal LDO, voltage-dependent MCU
demand or clock-failure model. A smaller voltage dip alone is not an energy
benefit. Finer current traces and independently characterized steady/load-step
responses are needed before hardware claims. Changing the controller or losses
requires new physical justification and validation; searching parameters until
a ranking reverses would not establish the hypothesis.

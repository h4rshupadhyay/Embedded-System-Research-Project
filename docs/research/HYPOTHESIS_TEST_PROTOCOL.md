# Protocol: does regulator history improve implementation selection?

Proposed 18 October 2026. This is an experimental design, not completed validation. It tests the regulator-history hypothesis discussed in the conversation and the revised supply-study question in [RESEARCH_GAP.md](./RESEARCH_GAP.md). First establish whether an energy model makes costly implementation choices after established corrections; then test whether additional regulator dynamics improve those decisions.

**Initial implementation status:** the FIR history mismatch and signed-overflow
ambiguity have been corrected, with independent host-reference tests, sanitizer
checks and compiled Cortex-M0 checksum verification. `run_sim_pilot.py` profiles
consecutive jobs and emits logical cadence metadata. The first report is
[results/sim_pilot.json](../../results/sim_pilot.json). The user currently has simulation
only. An [uncalibrated averaged-buck experiment](./ENERGY_MODEL.md) now compares
a steady-loss baseline and a fitted history predictor against a synthetic circuit
reference. Its [first result](../../results/energy_hypothesis/SUMMARY.md) shows no
selection gain in nine virtual conditions. Executed sleep/wake, calibrated current
generation, identified regulator parameters and physical measurements remain
outstanding. The protocol below remains the design for the physical hypothesis;
the virtual experiment does not validate it.

**Bounded follow-up outcome:** the [broader fixed study](./BOUNDED_STUDY_FINDINGS.md)
finished with 207/207 valid primary conditions and nine replay-control conditions.
Both predictors chose the circuit-best implementation in every case, giving zero
selection savings; the history predictor's mean energy error was slightly worse.
The fixed 1% continuation criterion was not met, so the recommendation is to stop
this particular simulated model as an implementation-selection contribution.
The physical protocol below remains unexecuted; simulation does not supply its
measurement endpoint or confidence interval.

## Hypothesis and primary endpoint

For bit-exact implementations of the same job at fixed nominal MCU voltage and clock frequency, a separately calibrated regulator-history model yields a practically meaningful reduction in measured upstream energy of its selected implementation, relative to a strong baseline, on withheld workloads and execution conditions.

For each test condition c, freeze both models' choices before inspecting its energy measurements:

```text
b(c) = implementation selected by the corrected baseline
h(c) = implementation selected by the history model
D(c) = measured source energy/job of b(c)
       - measured source energy/job of h(c)
```

Positive D favors the history model. Specify the test population, condition weights and minimum useful mean improvement δ before the evaluation. If workloads have very different job energies, predefine an independently measured reference normalization or report separate workload groups; do not change weights after seeing results.

The primary superiority test is H0: mean D ≤ δ versus H1: mean D > δ. Use a predeclared confidence level, for example a two-sided 95% interval: a lower bound above δ supports the practically meaningful improvement claim; an upper bound at or below δ excludes an improvement larger than δ in the tested population; an interval spanning δ is inconclusive. This deliberately demands more than a positive point estimate. δ must come from application value and attainable measurement resolution, not the largest effect found afterward.

Also report energy penalty relative to the physically best resolved implementation, pairwise ordering, unresolved ties and absolute model error. Comparing the two selected implementations directly avoids making the primary result depend on a noisy minimum across many candidates. Confirm apparent physical winners with separate measurements or propagate selection uncertainty.

## 1. Establish equivalent computation

The original [fir.c](../../fir.c) direct implementation skipped terms when n < k,
whereas the other implementations used preceding samples supplied by
[main.c](../../main.c). The initial software stage now resolves this mismatch and
defines the common arithmetic/history contract in [fir.h](../../fir.h). Maintain the
independent reference gate as workloads and hardware are added. Preserve FIR state
across bursts when processing one continuous stream, retaining equal completed work
and outputs for every comparison.

This is a prerequisite: a faster program computing fewer terms cannot test the hypothesis. Do not reuse the present direct-versus-circular reversals as evidence.

## 2. Establish an observable measurement boundary

Use one MCU/package and an accessible external regulator, with fixed nominal voltages, frequency, sleep policy, memory placement, GPIO configuration and a stable documented decoupling network. Measure synchronized input and output voltage/current at the regulator boundaries:

```text
E_source = integral(V_in(t)  * I_in(t),  t_start, t_end)
E_MCU    = integral(V_out(t) * I_out(t), t_start, t_end)
```

If other output loads exist, characterize them or measure the MCU branch separately. External measurements do not directly expose STM32F051's internal core-regulator output; the device documents distinct external and internal supply domains. [STM32F051 datasheet](https://www.st.com/resource/en/datasheet/stm32f051t8.pdf)

Use synchronized acquisition or demonstrate repeatability adequate for separately acquired channels. Characterize shunt burden, offsets, bandwidth, channel skew and integration error. Choose sampling/bandwidth from observed waveform timescales and verify convergence of integrated energy with acquisition settings; sample rate alone is insufficient. Measure the entire wake–compute–sleep period, including recovery, after periodic operation stabilizes. Match start/end rail states or correct stored-energy changes. Use GPIO timing markers with their overhead included consistently.

The current spin loop must become a controlled hardware timing protocol before these measurements are possible. Exact board connections depend on the available equipment and regulator; none are assumed here.

## 3. Freeze calibration and progressively stronger baselines

| Model | Included information | Role |
|---|---|---|
| Cycle proxy | Runtime, common timing protocol, sleep/wake costs | Simple reference |
| Published event model | Applicable coefficients/events/settings, plus sleep/wake accounting | Existing software-energy reference |
| Corrected operating-point supply model B | Time-resolved load demand; measured nonlinear efficiency; quiescent consumption; known startup, shutdown and mode-transition costs | Primary baseline |
| History model H | Same demand inputs and calibration privileges as B, plus separately calibrated regulator dynamics | Primary challenger |

Converter efficiency, quiescent consumption and operating modes are established modeling components; see [Brunner et al., MASS 2024, §II](https://www.carloalbertoboano.com/documents/brunner24converters.pdf). Startup-current replay and equilibrium conversion efficiency are also established in [Wong et al., ENSsys 2020, §3](https://wilwan01.github.io/pdf/enssys2020.pdf). Their inclusion is a baseline requirement, not a proposed discovery.

Check that any reused event model works in its documented sustained-execution domain before calling later errors a burst-transfer failure. Check its measurement boundary to avoid counting conversion losses twice. Whole-program event totals do not supply a calibrated current waveform; prospective time-resolved demand requires a separately validated estimator.

Calibrate supply models with independent steady loads, load steps and pulse sequences spanning the intended range. Validate their predictions on unused sequences. SPICE is one implementation option; first test whether a simpler dynamic model suffices. Freeze model structure, parameters and selection rules before final evaluation.

## 4. Run a small physical pilot

Start with three correct FIR variants, a few workload sizes and one supply configuration. Include continuous execution and periodic bursts, with cadences chosen from measured recovery behavior. At a given condition use the same job and common release period/deadline for all variants; faster variants spend the remainder in the same sleep mode. Keep batch size fixed while varying cadence initially. Treat batching as a separate experiment because it changes per-release work.

Collect randomized paired repeats in blocks across sessions. Use the pilot's variation and calibration uncertainty to choose the later sample size for δ and the desired statistical power. Repeated jobs inside one acquisition are not independent experimental replicates. Report per-job energy, completed jobs, timing and rail behavior. Record deadline misses, resets and output errors separately.

Pilot decisions:

- If uncertainty exceeds the useful energy difference, improve measurement or report infeasibility at that resolution.
- If established corrections suffice, quantify the observed selection penalty and its uncertainty; do not force a reversal.
- If errors originate at MCU pins, investigate wake/initialization/Flash/state behavior before attributing them to the external regulator.
- If a resolved upstream discrepancy remains, test whether calibrated additional supply dynamics explain and predict it.

## 5. Separate a causal diagnostic from prospective prediction

**Diagnostic:** give B and H the same measured MCU-pin demand traces. Compare predicted source energy with measured source energy. This isolates the added supply-model capability. It does not establish an implementation-selection tool that works before measurement.

**Prospective test:** both models receive independently predicted demand for withheld variants/workloads, plus known supply/timing settings, without the measured evaluation traces. Freeze their choices, then measure the chosen and competing implementations. Reserve workload configurations, cadences and a separately characterized supply configuration from model tuning. A new regulator may require separate characterization; do not claim parameter-free transfer to unknown hardware.

An end-to-end gain that comes only from a better load predictor is not isolated evidence for regulator history. The diagnostic comparison, with identical load inputs, and controlled supply interventions must support that attribution.

## 6. Make the decision from independent results

Analyze paired D values using a method that respects workload/session dependence, such as a predeclared hierarchical or block bootstrap. Do not count every pair sharing an implementation or every repeated job as independent. Propagate systematic calibration uncertainty; resampling alone does not remove it. Publish the full predefined condition set, including cases with no benefit.

For each condition retain firmware/compiler identifiers, workload/input identifiers, supply configuration, period, session/block/order, outputs/checksum, completed-job count, timing, both energy measurements, acquisition/calibration settings and model predictions made before evaluation.

The hypothesis is supported only if H improves the predefined decision endpoint beyond δ and uncertainty on independent test conditions, and the additional regulator dynamics are supported by the controlled diagnostic. Better training fit, a smaller voltage dip, or beating cycles alone is insufficient. A precise negligible-benefit result limits the hypothesis within the tested domain; an imprecise result remains inconclusive.

Add a contrasting kernel before generalizing beyond FIR. The initial deliverable is a feasible pilot and a frozen evaluation protocol, not a promised rank reversal.

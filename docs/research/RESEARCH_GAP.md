# Research-Gap Assessment and Proposed Study

Assessed on 18 October 2026. Evidence and search limitations: [LITERATURE_AUDIT.md](./LITERATURE_AUDIT.md).

**Software-stage update:** the shared-history and arithmetic contract is now
implemented and checked against an independent reference. The initial
[simulation pilot](../../results/sim_pilot.json) records marked consecutive FIR calls
with matching output checksums. Its periodic idle values are projected metadata;
it does not model sleep, regulator dynamics or source energy. The historical
135-row CSV predates these fixes. See [the test protocol](./HYPOTHESIS_TEST_PROTOCOL.md)
for the outstanding hypothesis-validation stages.

## Assessment

**The original broad novelty claim is not defensible.** Existing research already compares compiler-generated versions of individual programs, including FIR benchmarks on Cortex-M0. It also investigates energy when configurations tie in performance. The claim that earlier work only aggregated heterogeneous benchmarks must be removed. See [Pallister et al., 2013 preprint / 2015 journal article](https://arxiv.org/abs/1303.6485) and [Georgiou et al., 2018](https://arxiv.org/abs/1802.09845).

Energy reduction despite increased execution time is also established on ARM microcontrollers; observing this phenomenon alone would not establish novelty. [Pallister, Eder and Hollis, 2014](https://arxiv.org/abs/1406.0403)

**A narrower candidate gap remains worth testing:** how reliably a cycle-only decision selects between equivalent implementations as their cycle gap shrinks, when physical measurement uncertainty and the error of an existing energy model are considered. This search did not establish that this exact evaluation has already been published; that is a bounded search result, not proof of absence or a claim of first discovery.

## Proposed gap paragraph

> Prior studies compare execution time and energy for alternative compilations of individual embedded programs, including FIR benchmarks on Cortex-M0, and use energy to distinguish configurations tied in performance. Consequently, neither per-kernel comparison nor energy–time disagreement is itself a new contribution. We propose a controlled study of when execution cycles provide sufficient evidence for choosing the lower-energy implementation of a bit-exact Q15 FIR filter on STM32F051. The study will measure pairwise ordering agreement and the energy cost of choosing the fastest variant as functions of cycle gap, workload dimensions, compiler settings and input data. It will distinguish physically resolved energy differences from measurement ties, and evaluate whether an existing event-counter model improves decisions over a cycle-only baseline on held-out workload configurations. The intended contribution is a reproducible characterization of the decision limits of these proxies within a stated operating configuration, rather than a new energy model or a universal cycle-gap threshold. Novelty of this particular combination remains provisional pending the unresolved literature checks in the audit.

Literature basis: [Pallister et al.](https://arxiv.org/abs/1303.6485), [Georgiou et al.](https://arxiv.org/abs/1802.09845), and the existing [EnergyAnalyzer model](https://arxiv.org/html/2305.14968v2#S4.SS1).

## Mathematical framing

Let F be the faster variant and S the slower variant under the same fixed clock frequency, with t_F < t_S and positive average powers P_F and P_S over the measured interval. Define g = (t_S - t_F) / t_F. Since E = P t:

```text
Energy rank reversal: E_F > E_S  iff  P_F / P_S > 1 + g.
Rank agreement:       E_F < E_S  iff  P_F / P_S < 1 + g.
Energy tie:           E_F = E_S  iff  P_F / P_S = 1 + g.
```

These are algebraic identities, not new theoretical contributions. An observed maximum reversal gap is descriptive. An empirical decision threshold requires a specified population of variants and workloads, independent validation and uncertainty analysis.

## Evidence needed before claiming a contribution

1. **Equivalent computations.** The corrected [fir.c](../../fir.c) now passes independent-reference tests for supplied history, arithmetic and split streams; compiled Cortex-M0 runs verify stream checksums. Keep this gate for every new workload. The historical CSV's direct/circular reversals involved different computations and are invalid evidence of equivalent-implementation reversals.
2. **Independent physical evidence.** Measure time and energy over the same FIR execution interval, separate setup overhead, repeat experiments and quantify the uncertainty of pairwise differences. Classify unresolved cases as ties.
3. **Model provenance.** The current coefficients appear in EnergyAnalyzer §4.1; verify the applicable hardware configuration and counter definitions before applying them. Using published coefficients does not constitute developing or independently validating a new energy model. [EnergyAnalyzer](https://arxiv.org/html/2305.14968v2#S4.SS1)
4. **A useful comparison.** Compare cycle-only selection with the published counter model using pairwise agreement, top-choice agreement and excess energy relative to the measured best variant. Keep threshold selection and evaluation workloads separate; account for dependence between pairs sharing a configuration.
5. **Adequate scope.** Sample near ties intentionally and report their denominator. Test additional kernels or operating settings before suggesting the result generalizes beyond this FIR/platform configuration.

The existing 135-row simulation sweep is exploratory evidence. It does not yet substantiate claims of verified functional equivalence, hardware measurement, a validated 0.1% threshold, a newly trained model, held-out validation or noise-floor analysis.

## Follow-up: supply dynamics and package effects

The subsequent [physical-effects literature assessment](./PHYSICAL_EFFECTS_LITERATURE.md) checks the proposed droop, transient LDO and LQFP/WLCSP directions, including the attached methodology. These effects must not be introduced as unexplored physics: software-directed droop mitigation and trace-driven SPICE regulator simulation already have direct precedents. [VRSync, ISCA 2012](https://radu.teodorescu.us/assets/pdf/miller_isca2012.pdf)

A possible extension is whether supply-path dynamics change energy ordering among equivalent MCU implementations at a stated measurement boundary, beyond ordinary conversion loss and quiescent overhead. This remains a candidate question, not a demonstrated gap or promised reversal. Start with an accessible external regulator and a fixed MCU/package; a matched-package comparison needs additional electrical characterization and control of board/die variation. The linked assessment records known prior art, platform corrections and unresolved full texts.

The [focused follow-up literature check](./NARROW_GAP_LITERATURE_CHECK.md) finds substantially closer precedents: MCU execution plus analog supply modeling and physical validation in [Fused, ISPASS 2020](https://wilwan01.github.io/pdf/ispass2020.pdf); measured startup traces and equilibrium converter efficiency in [Wong et al., ENSsys 2020](https://wilwan01.github.io/pdf/enssys2020.pdf); and load-versus-source energy optima in [Shrivastava and Calhoun, 2013, §3/Figure 6](https://www.mdpi.com/2079-9268/3/3/215). Consequently, neither supply-aware simulation nor a changed source-energy optimum is sufficient novelty.

**Revised supply-study question:** at fixed nominal voltage/frequency, does a calibrated stateful supply model improve the choice among equivalent implementations on held-out workload/supply conditions, beyond cycles, the published event model, and a time-resolved load-dependent steady-efficiency baseline with quiescent and startup costs? This is a plausible incremental empirical contribution; the search has not established that it is unpublished. Beating a cycle-only baseline would not isolate transient supply causation. The physical pilot must resolve energy differences and demonstrate useful improvement over the stronger baseline before this direction supports a contribution claim.

The [deep adversarial literature audit](./DEEP_SUPPLY_PRIOR_ART.md) further weakens broader interpretations: ISLPED 1999 already reports small timing/energy disagreements among compiler settings in a converter-inclusive model, and Simba 2024 evaluates supply-dependent firmware policies. The exact additional-value comparison above was not located in the inspected evidence, but absence of a paper matching every protocol detail is not proof of a substantive gap. **Status: scientifically valid, falsifiable candidate; originality provisional; physical effect and practical benefit unvalidated.** A measured-trace diagnostic and prospective selection using independently predicted traces must be evaluated separately. Known supply modes and startup costs belong in the baseline; the claimed improvement must come from additional regulator dynamics and persist beyond measurement uncertainty on withheld conditions.

**Simulation status:** the [runnable model](./ENERGY_MODEL.md) now evaluates a
separately fitted history predictor against an independently integrated synthetic
buck circuit. In the [first nine virtual cases](../../results/energy_hypothesis/SUMMARY.md),
the steady baseline and history predictor select the same reference-best FIR
variant, giving zero selection improvement. This conditional result is not
physical validation, evidence of novelty, or a general rejection of the candidate.

**Bounded broader outcome:** the [fixed follow-up](./BOUNDED_STUDY_FINDINGS.md)
completed all 207 primary conditions across 23 additional FIR workload/compiler
configurations, plus nine original-workload control conditions. The steady and
history predictors selected the circuit-best implementation in every case;
selection savings were zero, and average prediction error was slightly worse
with history. The predefined continuation criterion was not met. Stop the current
model as a path to an implementation-selection contribution in this simulated
domain. The physical hypothesis remains untested, and this negative result does
not independently validate a different gap or establish that all supply-history
models lack value.

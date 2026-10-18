# Focused literature check: supply-aware MCU implementation selection

Checked 18 October 2026. This follow-up narrows the question in [PHYSICAL_EFFECTS_LITERATURE.md](./PHYSICAL_EFFECTS_LITERATURE.md). It records additional primary evidence, including important precedents absent from that note. It is a bounded search, not a systematic review or proof of absence.

**Deeper follow-up:** [DEEP_SUPPLY_PRIOR_ART.md](./DEEP_SUPPLY_PRIOR_ART.md) finds a closer ISLPED 1999 compiler-comparison precedent, 2024 supply-aware software-policy comparisons, voltage-dependent program analysis, and 2025 experiment infrastructure. It retains the additional decision value of regulator history as a provisional empirical gap, with stronger baselines and explicit physical/predictive validation requirements. This later assessment qualifies the verdict below.

## Verdict

**A broad claim that MCU energy models overlook temporal supply behavior is not defensible.** Primary work already combines executable MCU models, event/state current estimates, startup-current traces, analog supply circuitry and physical validation. Likewise, compiler-driven shaping of software power profiles predates this project. The sources below establish these overlaps; the novelty judgments are our assessment.

**The proposed decision-focused study remains a candidate empirical contribution, not a confirmed empty research gap.** None of the inspected full texts below establishes the complete proposed evaluation: bit-exact, fixed-voltage kernel alternatives; controlled burst/supply changes; measured source-energy rankings with uncertainty; comparison against cycles and a published counter model; and prediction on withheld supply/workload combinations. Partial access to other sources prevents treating this result as an exhaustive exclusion.

Changing MCU or adding SPICE would not be sufficient novelty. A potentially useful result would establish whether *stateful supply dynamics add predictive value beyond measured MCU-pin energy, load-dependent steady efficiency, quiescent current and ordinary startup costs*. Rank reversals must be observed rather than assumed.

**Decision:** retain this as a narrowly scoped empirical study, but do not present it as an established novel mechanism or modeling method. The strongest unresolved question is the *additional implementation-selection accuracy* obtained from supply history, at fixed nominal voltage/frequency, after accounting for established conversion effects. A new combination of FIR and STM32 parts alone is a weak novelty argument.

## Additional primary sources and overlap

### 1. Sliper et al., Fused, ISPASS 2020

**Access:** Full 10-page author-hosted paper inspected. [Author PDF](https://wilwan01.github.io/pdf/ispass2020.pdf), [project source](https://github.com/UoS-EEC/fused). The PDF prints DOI **10.1109/ISPASS48437.2020.00022**; use its primary metadata rather than a conflicting third-party entry.

**Evidence:** §§III–V describe an MSP430FR5994 hardware platform, synchronized current/logic measurements, an event/state current estimator, and SystemC-AMS external circuitry. §IV explicitly includes Cortex-M0 and MSP430 CPU models executing unmodified binaries. Event counts are aggregated within configurable time steps rather than only once per program. §§VI–VII evaluate current/timing prediction and an intermittent-system case study.

**Overlap:** Executable MCU simulation coupled to an analog supply and physically fitted activity models is already published. It is inappropriate to describe all previous instruction/event models as supply-independent fixed-total models.

**Limit:** The demonstrated system uses a storage capacitor, switching and constrained supply to study intermittent execution. The inspected evaluation does not establish the proposed near-tie source-energy ranking comparison or isolate fast regulator recovery loss.

### 2. Wong et al., Energy-aware HW/SW Co-modeling of Batteryless Wireless Sensor Nodes, ENSsys 2020

**Access:** Full seven-page author-hosted paper inspected. [Author PDF](https://wilwan01.github.io/pdf/enssys2020.pdf), [DOI](https://doi.org/10.1145/3417308.3430272).

**Evidence:** §3.1 distinguishes event/state active-current estimates from supply-path operating points. It explicitly replays measured MCU-startup current/time before the first instruction. Figure 5 labels its buck/boost representation as an equilibrium model using an efficiency lookup table. §4.1 compares simulated and measured current profiles for the same firmware on a physical MSP430 sensor node.

**Overlap:** Modeling temporal MCU demand, converter operating-point efficiency, startup behavior and the interactions between supply and executable firmware is established, including hardware validation.

**Limit:** An equilibrium efficiency lookup table is not itself validation of fast converter control-loop settling losses. Its illustrated endpoint is sensor-node behavior and current-trace agreement, rather than calibrated ranking decisions among equivalent computational kernels. This distinction is a possible study boundary, not evidence that nobody has studied the latter.

### 3. León Ávila et al., Comprehensive electrical models for a wireless sensor network device, Heliyon 2024

**Access:** Publisher abstract and search-indexed primary full-text passages, including §2.3 and the LTspice model discussion, inspected; direct full-paper retrieval failed. [Publisher](https://www.sciencedirect.com/science/article/pii/S2405844024164468), [PMC full-text location](https://pmc.ncbi.nlm.nih.gov/articles/PMC11625280/), [institutional PDF](https://repository.unitbv.ro/server/api/core/bitstreams/b4fc37af-cb45-494d-b64e-d93c876e7793/content), [DOI](https://doi.org/10.1016/j.heliyon.2024.e40415).

**Evidence:** The abstract describes duty-cycle circuit models of MCU, sensors, radio and supply, evaluated with LTspice and a physical mote. The indexed model description uses pulse current sources with specified rise/fall times. It simplifies the MCU to sleeping/running and assigns run consumption to associated sensor/radio activity.

**Overlap:** A physically checked, duty-cycle-aware SPICE model of an MCU-based system is already available.

**Limit:** The accessible model description does not distinguish instruction-level kernel alternatives. Because the full paper was not retrieved, this audit does not assert that every possible compiler or ranking experiment is absent from it. Obtain and inspect the complete paper before making a categorical exclusion.

### 4. Grumer et al., Compiler-based Software Power Peak Elimination on Smart Card Systems, 2007

**Access:** Full nine-page proceedings paper inspected. [Publisher and DOI](https://drops.dagstuhl.de/entities/document/10.4230/DagSemProc.07041.5), [publisher PDF](https://drops.dagstuhl.de/storage/16dagstuhl-seminar-proceedings/dsp-vol07041/DagSemProc.07041.5/DagSemProc.07041.5.pdf).

**Evidence:** §3 uses GCC-generated MIPS32 code, a cycle-accurate simulator and instruction energy analysis. §4.1 implements packing and instruction scheduling using circuit-state overhead. §4.2/Table 1 compares cycles, energy and power-profile statistics across compiler options. §5 evaluates changes in mean power, total energy and standard deviation.

**Overlap:** Selecting compiler transformations to change the temporal power profile is established, even for power-constrained embedded systems.

**Limit:** This is not an STM32 regulator experiment; power-profile flattening and stability are central endpoints. Instruction-transition costs are not automatically regulator dissipation. It therefore supplies a necessary compiler/power-profile precedent without directly settling source-energy ranking prediction.

### 5. Šimunić, Benini and De Micheli, DAC 1999

*Cycle-Accurate Simulation of Energy Consumption in Embedded Systems.* **Full conference-hosted paper inspected.** [PDF](https://www.cecs.uci.edu/~papers/compendium94-03/papers/1999/dac99/pdffiles/48_3.pdf), [DOI](https://doi.org/10.1145/309847.310090).

§3.4 adds a current-dependent DC–DC efficiency lookup to ARM cycle-accurate simulation; §§4–5 compare SmartBadge hardware measurements and explore hardware/software alternatives. Thus, processor simulation plus upstream conversion accounting is decades old. The converter representation is an operating-point lookup, not a detailed transient control-loop model; the inspected evaluation does not establish our proposed fixed-setting kernel-ranking benchmark.

### 6. Choi, Chang and Kim, DAC 2005

*DC–DC Converter-Aware Power Management for Battery-Operated Embedded Systems.* **Full conference-hosted paper inspected.** [PDF](https://www.cecs.uci.edu/~papers/dac05/papers/2005/dac05/pdffiles/p895.pdf), [DOI](https://doi.org/10.1145/1065579.1065814).

§§2–4 integrate converter losses into voltage/frequency and converter-configuration choices. Numerical evaluation shows why optimizing the load alone can choose differently from optimizing battery energy. This precedes any general claim of converter-aware software energy optimization. It changes operating settings and uses converter-parameter simulations; it does not establish physical near-tie rankings between equivalent binaries at fixed nominal settings.

### 7. Shrivastava and Calhoun, JLPEA 2013

*A DC-DC Converter Efficiency Model for System Level Analysis in Ultra Low Power Applications.* **Publisher-indexed primary sections inspected; direct page retrieval failed.** [Publisher](https://www.mdpi.com/2079-9268/3/3/215), [DOI](https://doi.org/10.3390/jlpea3030215).

§2 models load/voltage-dependent efficiency, settling and capacitor charging/discharging overhead. §3/Figure 6 combines measured subthreshold MCU energy with a converter model fitted to converter measurements: the load-energy optimum differs from the modeled source-energy optimum across voltage. Therefore, even the observation that including the supply changes an energy-optimal choice is established. The comparison varies voltage and does not independently measure the proposed fixed-setting implementation ranking. Its 2012 conference version is the same research lineage, not an independent replication.

### 8. Kokert, Reindl and Rupitsch, Sensors 2021

*Behavioral Modeling of DC/DC Converters in Self-Powered Sensor Systems with Modelica.* **Full publisher PDF inspected.** [PDF](https://mdpi-res.com/d_attachment/sensors/sensors-21-04599/article_deploy/sensors-21-04599-v2.pdf?version=1625537268), [DOI](https://doi.org/10.3390/s21134599).

§§4–5 include loss-dependent efficiency, startup/shutdown state and feedback. However, §1.2 explicitly describes averaged steady-state behavior, and §5.8 says the PI controller primarily prevents an algebraic loop. §§6–7 demonstrate a simulated solar-converter-battery setup; §9 leaves real-system simulation and MCU duty cycling to future work. This is prior art for stateful supply-system modeling, **not** physical validation of fast firmware-induced recovery losses.

## Previously unresolved LDO papers

### ISCAS 2022: full text now found

*LDO Regulator Optimized on Power Efficiency and Load Transient Response with Voltage Damper and Body Loop Feedback.* [Publisher](https://ieeexplore.ieee.org/document/9937778/), [conference-hosted full PDF](https://confcats-event-sessions.s3.amazonaws.com/iscas22/papers/1726.pdf), [DOI](https://doi.org/10.1109/ISCAS48785.2022.9937778).

**Access:** Full four-page conference paper inspected. §II models the load using a current source and capacitor. §IV describes a fabricated 180 nm LDO, 1.8 V input/1.6 V output, and an electronic load controlled through an external BJT/function generator. Figure 8 measures voltage response for a 200 µA–100 mA load step with 300 ns rise/fall time. Table I compares transient deviation and a figure of merit involving quiescent current.

**Resolution:** The prior note's abstract-only limitation is resolved for this paper. It demonstrates measured circuit transients, not firmware-induced integrated source-energy differences, bit-exact kernel rankings or compiler selection. A smaller undershoot/FOM is not a demonstrated reduction in per-kernel energy.

### Mazumdar et al., ISQED 2015: only partly resolved

*A digitally-controlled power-aware low-dropout regulator to reduce standby current drain in ultra-low-power MCU.* [DOI](https://doi.org/10.1109/ISQED.2015.7085406), [official conference program](https://www.isqed.org/English/Archives/2015/Technical_Sessions/accepted.html), [author laboratory publication list](https://engineering.virginia.edu/labs-groups/high-performance-low-power-lab/publications).

**Access:** Primary conference and author records verify the work. The IEEE endpoint did not expose a usable abstract or full text in this run. A new primary lead is Mazumdar's 2015 dissertation, *Breaking the Power Delivery Walls using Digitally-Controlled Integrated Regulation*. Its [university archive abstract](https://libraetd.lib.virginia.edu/public_view/5138jf18j) describes a digitally adaptive LDO using system power-mode information to regulate quiescent-current loss, with a 4.44 ps figure of merit. Full dissertation retrieval failed.

**Resolution:** This independently supports the broader precedent of MCU-power-mode-aware LDO design. It does not independently verify the specific conference-paper claim about reduced sleep-to-active recovery energy, nor prove that paper excludes kernel-selection experiments. The exact full-text check remains open; third-party mirrored abstracts are not used as the evidentiary basis here.

## What a credible comparison must distinguish

The following is our proposed evaluation, not a finding attributed to these papers:

1. **Cycle-only model:** calibrated runtime-to-energy proxy.
2. **Published event model:** confirm its measurement boundary and operating conditions before reuse.
3. **Memoryless supply baseline:** measured/validated load-dependent conversion efficiency, quiescent consumption and explicit startup/shutdown charges. An average-efficiency constant is too weak a baseline.
4. **Stateful supply model:** add the hypothesized transient/storage dynamics, fit using separate calibration experiments, then test without refitting on withheld burst spacing, duration, supply configurations and implementations.

Measure both MCU-pin and upstream source energy over equivalent work and consistent start/end rail states. Report the energy penalty of selecting each proxy's winner, physically resolved pairwise ordering and unresolved ties. Compare models 3 and 4 to determine whether the supposed transient mechanism contributes beyond known steady conversion effects. A failure of cycles alone does not establish supply causation.

The steady-efficiency baseline must operate on time-resolved load demand: applying efficiency only to the program's average current is insufficient when the efficiency curve is nonlinear. For the stateful comparison, hold nominal voltage/frequency and initial rail state fixed; reserve both workload and supply conditions for evaluation. Evaluate more than one kernel before claiming broad software relevance. These are experimental recommendations, not claims of an unpublished method.

## Search log and limitations

Queries used included `microcontroller software energy voltage regulator transient compiler energy optimization current profile`; `"software" "regulator efficiency" "compiler"`; `"regulator-aware" software energy`; `"microcontroller" "transient" "energy model" regulator`; `"battery" "current profile" "compiler" optimization energy`; `"Compiler-based Software Power Peak Elimination" pdf`; `"Fused" "Closed-loop Performance" "regulator"`; `"Energy-aware HW/SW Co-modeling" "converter"`; and exact titles/DOIs for the two unresolved LDO papers. Followed primary author, conference, publisher, institutional-repository and source-code links. Unrelated energy-grid results and secondary mirrors were excluded as substantive evidence.

The follow-up also searched converter-aware embedded power management, converter settling/energy overhead, ARM cycle-accurate converter models and exact titles above. Southampton copies failed retrieval; author copies resolved both Fused papers. Heliyon and JLPEA evidence includes indexed primary sections with direct-access failures. The Virginia dissertation full text and ISQED paper remain unresolved. Citation-forward searching and a comprehensive bibliographic-database review were not completed; this record must not be described as exhaustive.

**Working wording:** “We evaluate the transferability of cycle and event-based implementation choices to measured source energy under controlled burst and supply conditions, and test whether a calibrated stateful supply model improves choices beyond a load-dependent steady-efficiency baseline.” Treat this as a proposed contribution until the physical pilot and remaining literature checks justify stronger wording.

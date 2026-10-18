# Adversarial follow-up: supply-aware software implementation selection

Checked 18 October 2026. This note follows [NARROW_GAP_LITERATURE_CHECK.md](./NARROW_GAP_LITERATURE_CHECK.md), focusing on the Fused/ENSsys lineage, supply-aware software optimization and the strongest newly located counterexamples. It records a targeted search, not an exhaustive bibliographic review.

## Assessment

**The research question remains experimentally meaningful, but a broad novelty claim is weaker after this search.** Older work already compares near-tied compiler outputs using models that include conversion losses. Newer work compares software load strategies in physically evaluated, stateful supply simulations. Neither “small cycle differences can produce different energy choices” nor “supply state changes which software behavior is preferable” is an adequate new contribution.

**I did not locate a direct demonstration of the exact proposed incremental-value test:** whether regulator-history modeling improves selection among equivalent fixed-nominal-voltage/frequency kernels beyond a time-resolved, load-dependent steady conversion baseline, with physical source-energy differences resolved and evaluated out of sample. This is a bounded negative search result. Combining that entire checklist into one sentence does not by itself make an important or original contribution.

The defensible next step is a small physical feasibility study. If a strong memoryless model already makes the same decisions within measurement uncertainty, adding SPICE and a new platform is weak justification for a paper. If history changes correct implementation choices under realistic conditions, the contribution can be the demonstrated decision consequence and its reproducible boundary.

| Validation dimension | Finding from this audit |
|---|---|
| Meaningful and falsifiable question | Yes: compare implementation-choice error with and without regulator history. Either outcome is possible. |
| New physical effect or general modeling idea | No: existing work covers supply dynamics, conversion losses, temporal demand and software optimization. |
| Exact incremental-value evaluation already located | No direct match in the inspected evidence; this is a search result with access and coverage limits. |
| Sufficient novelty for a paper | Conditional: additional decision value or a useful, independently tested bound must be demonstrated. Platform substitution and a longer evaluation checklist are insufficient. |
| Supported by our current experiment | No: model totals and the existing equivalence problem do not establish physical source-energy rankings or transient causation. See [RESEARCH_GAP.md](./RESEARCH_GAP.md). |

**Recommendation:** keep the candidate as a provisional empirical gap. Do not describe it as a validated discovery, the first stateful model, or an established regulator-loss mechanism in our FIR results.

## Strongest newly located counterexample: Šimunić, Benini and De Micheli, ISLPED 1999

*Energy-Efficient Design of Battery-Powered Embedded Systems*, pp. 212–217. **Full six-page conference-hosted PDF inspected:** [paper](https://www.cecs.uci.edu/~papers/compendium94-03/papers/1999/islped99/pdffiles/08_4.pdf), [author publication record](https://si2.epfl.ch/demichel/publications/archive/conferences.html).

§2 includes processor, memories, interconnect and DC–DC conversion energy. §3/Table 2 compares ARM compiler settings for the same MPEG decoder. Against the balance baseline, “disable all” changes execution time by −0.26% and modeled energy by +0.65%; cross-jump gives −0.21% and +0.69%. Thus small time gaps and contradictory energy ordering in a converter-inclusive embedded model were already reported. These are simulation comparisons; the Dhrystone hardware validation in §2 does not physically resolve those sub-percent compiler differences.

§5 separately adds a battery-capacity model using recent current history over a specified time window. Its endpoint is battery capacity/lifetime, not simply electrical joules crossing the battery terminals. This is not a detailed regulator control-loop recovery model, nor proof that the compiler ordering differences were caused by conversion or battery history. The paper is nevertheless substantially closer prior art than the previously cited DAC 1999 modeling paper alone.

## Later software-optimization lineage: Šimunić et al., ISSS 2000

*Source Code Optimization and Profiling of Energy Consumption in Embedded Systems.* [Author-hosted paper](https://si2.epfl.ch/demichel/publications/archive/2000/ISSSconf00pg193.pdf), [author publication record](https://si2.epfl.ch/demichel/publications/archive/conferences.html).

**Access:** Author-hosted PDF retrieved but its browser text extraction returned zero lines; publisher-indexed author-PDF text supplies Table 4 and the conclusion. Accordingly this is a targeted table/section check, not a full-text exclusion.

Table 4 reports multiple MP3 implementations with separate battery, CPU, flash, RAM, DC–DC and interconnect energy columns. This reinforces the precedent for guiding software implementation changes using upstream-aware system energy accounting. It does not establish fast-transient causation or an uncertainty-qualified held-out ranking evaluation. This is related work from the same research lineage, not an independent experimental replication.

## Forward lineage: Brunner et al., Simba, IPSN 2024

*Simba: A Unified Framework to Explore and Facilitate the Design of Battery-Free Systems.* DOI [10.1109/IPSN61024.2024.00016](https://doi.org/10.1109/IPSN61024.2024.00016). **Full 13-page author PDF inspected:** [paper](https://www.carloalbertoboano.com/documents/brunner24simba.pdf).

§3 models capacitor state and interactions among harvester, converter and load, including nonlinear efficiency and quiescent currents. §4.3.2 explicitly compares alternative load implementations: exhausting residual energy after transmission (BURN), repeated sensing/transmission (LOOP), and voluntary power-off (SHUTOFF). Their relative effectiveness changes with application and supply conditions. Modified LOOP firmware is physically evaluated; SHUTOFF is simulation-only. This is strong prior art for supply-dependent software-policy selection.

The alternatives intentionally change sampling/reboot behavior and delivered work. They are not bit-exact implementations of a fixed computational job compared by measured upstream joules. §6 identifies instruction-level load modeling and executable-code congruity as possible extensions; the demonstrated loads aggregate task duration/current. The inspection did not find a baseline ablation isolating fast regulator history from time-resolved steady conversion efficiency, or the proposed kernel-ranking regret endpoint.

## Stronger baseline: Brunner et al., MASS 2024

*Modelling and Comparing Converter Architectures and Energy Harvesting ICs for Battery-Free Systems.* DOI [10.1109/MASS62177.2024.00057](https://doi.org/10.1109/MASS62177.2024.00057). **Full seven-page author PDF inspected:** [paper](https://www.carloalbertoboano.com/documents/brunner24converters.pdf), [university record](https://tugraz.elsevierpure.com/en/publications/modelling-and-comparing-converter-architectures-and-energy-harves/).

§II models cold-start, undervoltage, charging and overvoltage states. §§II.C–D experimentally characterize efficiency/quiescent current and evaluate charging, discharging and startup behavior. Models include three harvesting ICs, a step-down converter and an LDO. The standalone DC–DC/LDO representation uses operating-point efficiency lookup tables, rather than a detailed fast control-loop transient model. §§IV–V compare supply architectures and IC choices, including a TPS7A02 LDO.

This makes constant average efficiency or missing startup/quiescent consumption an inadequate comparator. A serious baseline should use measured, time-resolved operating points and known mode transitions. The evaluation is about supply-component choice and node operation, not compiler-equivalent kernel ranking. Failure to model its difficult cold-start cases is explicitly acknowledged, showing why “stateful” is not a guarantee of physical accuracy.

## Earlier compiler/supply connection: Ransford, Sorber and Fu, HotPower 2008

*Getting Things Done on Computational RFIDs with Energy-Aware Checkpointing and Voltage-Aware Scheduling.* **Full USENIX-hosted text inspected:** [paper](https://www.usenix.org/legacy/event/hotpower08/tech/full_papers/ransford/ransford_html/index.html).

The paper proposes voltage-aware program reordering that maintains semantics, along with energy-aware checkpointing. Its motivations include capacitor-voltage changes across instructions and instruction-specific minimum operating voltages; its measurements include instruction energy on an MSP430 WISP. This precedes a broad claim that supply state has never informed semantically equivalent instruction organization. However, its setting has a varying capacitor-fed rail, and parts of the approach are explicitly preliminary. It does not establish the proposed fixed-nominal-rail comparison of regulator-history and steady-conversion models.

## Additional adversarial checks

### Instruction-driven regulation and history-informed prediction

**Jia et al., DAC 2016, _Exploration of Associative Power Management with Instruction Governed Operation for Ultra-low Power Design_.** [Author PDF](https://www.eecs.northwestern.edu/~rjoseph/publications/associative-power-management-dac-2016.pdf), [DOI](https://doi.org/10.1145/2897937.2898021). The primary PDF was available, but its extracted text is character-encoded; indexed primary §§3.3–4 were readable. They model regulator conversion and voltage-transition losses, propose compiler substitutions, and evaluate gate-level benchmarks. Thus instruction-sensitive regulation and compiler/regulator co-design are prior art. The rail deliberately changes between voltage levels: this is not the fixed-nominal-rail ablation proposed here. No quantitative benefit is transferred to STM32.

**Kawaguchi and Yachi, IEICE 2014/2015.** Publisher abstracts inspected; full texts remain inaccessible. The [2014 efficiency paper](https://globals.ieice.org/en_transactions/communications/10.1587/transcom.E97.B.408/_p) uses performance counters and regression to adapt power-supply configuration. The [2015 transient-response paper](https://globals.ieice.org/en_transactions/communications/10.1587/transcom.E98.B.2382/_p) uses past counter samples in a moving-average prediction of CPU demand and circuit simulations of feed-forward supply control. These contradict a broad claim that counter history has never been connected to supply dynamics. They address server supply control, not the proposed equivalent-MCU implementation selection. Abstracts cannot exclude every evaluation in those papers.

### Voltage-dependent program energy: Ahmed et al., LCTES 2019 / TECS 2020

_The Betrayal of Constant Power × Time_ and its journal extension, _Demystifying Energy Consumption Dynamics in Transiently-powered Computers_. [2019 author PDF](https://mottola.neslab.it/wp-content/uploads/2023/06/ahmed19betrayal.pdf), [2020 author PDF](https://mottola.neslab.it/wp-content/uploads/2023/06/ahmed20epic.pdf), [journal DOI](https://doi.org/10.1145/3391893). The extension's primary full text was inspected at §§3–5 and Table 1; the conference version was checked through indexed primary passages.

EPIC predicts code energy using empirically characterized voltage-dependent behavior and a voltage trace or capacitor model. The paper evaluates prediction against measurements and demonstrates consequences for checkpointing and program-development decisions. It is strong prior art for showing that richer supply-dependent models improve software decisions. Its capacitor-fed MSP430 setting has changing rail voltage and clock behavior; it does not establish the proposed incremental benefit from fast regulator history over a validated steady-conversion baseline at fixed nominal settings. These are versions of one research lineage.

**Related compiler follow-up:** [Li and Wang, ECOOP 2023](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2023.16). Primary full-text §§2.1–2.2 were inspected. It preserves program semantics while moving eligible computations ahead of time to match intermittent supply, and evaluates transformed programs with MSPSim using an empirical energy model referencing Ahmed et al. This is an additional overlap with supply-aware equivalent-program transformation; the inspected model description does not isolate regulator-history losses.

### Experimental benchmarking: E-Cube 2024 and Shepherd Nova 2025

[E-Cube, GoodIT 2024](https://www.carloalbertoboano.com/documents/schuss24ecube.pdf) provides an automated facility for comparing battery-free solutions; [its official competition](https://iti-ecube.tugraz.at/wiki/index.php/Main_Page) specifies a common computational task under intermittent energy. Paper introduction and official protocol inspected. This narrows any broad claim that controlled equivalent-task benchmarking is new.

[Shepherd Nova, MobiSys 2025](https://nes-lab.org/wordpress/wp-content/uploads/2025/09/geissdoerfer25shepherdnova.pdf), DOI [10.1145/3711875.3729146](https://doi.org/10.1145/3711875.3729146), provides real-firmware experiments with virtual supply/harvester/storage models and synchronized power/GPIO observations. Primary §§3–4 and 6 were inspected. §6 compares emulated and real converter-based/less sensor setups and studies repeatability. This establishes relevant experiment infrastructure, not the proposed fixed-job selection ablation. Its 10 µs virtual-source updates must not be assumed to reproduce arbitrary faster regulator dynamics.

### Direct circuit mechanism: Kirshenboim, Cervera and Peretz, TPEL 2017

_Improving Loading and Unloading Transient Response of a Voltage Regulator Module Using a Load-Side Auxiliary Gyrator Circuit_, DOI [10.1109/TPEL.2016.2564698](https://doi.org/10.1109/TPEL.2016.2564698). **Indexed primary author-PDF introduction and §III/Figures 4–5 inspected; direct retrieval failed:** [author PDF](https://pemic.org/publications/jour022.pdf). The paper contrasts constant and repetitive dynamic loads and analyzes current stress and efficiency during recovery. This supports the physical plausibility of additional dynamic conversion loss in that switching-converter setting; it also establishes that this mechanism itself is known. It neither demonstrates our software-choice effect nor measures the STM32 internal LDO. Its related [2015 conference manuscript](https://pemic.org/publications/conf041.pdf) is a separate version, not independent corroboration of the journal experiment.

## What remains to validate

The central distinction should be **demonstrated additional decision value**, not simply that earlier papers omitted one chosen combination of platform, kernel and metrics. A credible contribution would:

1. Resolve equivalent-work semantics before comparing energy.
2. Measure upstream and MCU-pin energy over consistent rail states, including recovery/recharge, and separate unresolved differences from real ordering changes.
3. Compare a strong time-resolved operating-point baseline against a separately calibrated history model. Known startup charges and coarse mode transitions should be included where applicable; reserve “history benefit” for what the stronger model adds.
4. Evaluate prediction on implementations, workloads and supply conditions withheld from fitting, reporting selection penalty as well as absolute prediction error.
5. Identify conditions where the simpler model suffices. A null result is useful characterization; it is not evidence for the originally proposed mechanism.

These are proposed experimental criteria, not claims that this protocol or its individual metrics are new.

The contribution should be expressed as a falsifiable claim: **under specified realistic operating conditions, incorporating calibrated regulator history reduces the source-energy penalty of choosing an equivalent implementation, beyond a validated operating-point model.** Predefine a practically relevant improvement before collecting the evaluation data. A lower waveform error alone does not establish a better software choice; a tiny rank change within uncertainty is unresolved.

Two experiment modes must be separated. First, feed both supply models the *same measured MCU-pin demand trace* to test whether regulator history adds explanatory value; this is a diagnostic comparison with measured inputs. Second, use only independently calibrated event/trace predictions and known settings to choose unseen software variants, without their measured evaluation traces. Only the latter supports a claim of prospective implementation selection. Otherwise a model can appear useful by receiving the measurements it is supposed to predict.

The baseline can include known startup charges and mode transitions even though those contain some coarse state. The incremental test concerns the **additional regulator dynamics**, not the label “stateful.” Hold starting rail state fixed within paired comparisons, include recovery or correct stored energy, and keep GPIO, clock, memory placement and completed work comparable. For a fixed-voltage LDO, voltage droop alone does not imply additional source charge: test the current/energy residual rather than assuming it. These are our causal-design deductions, consistent with the accounting in [PHYSICAL_EFFECTS_LITERATURE.md](./PHYSICAL_EFFECTS_LITERATURE.md).

## Search and access log

Search families included exact titles and citation-forward leads from Fused and Wong ENSsys 2020; `"Fused" "Closed-loop" microcontroller simulation Sliper citations`; `"Energy-aware HW/SW Co-modeling" cited`; `microcontroller supply aware instruction scheduling regulator transient energy optimization`; `"compiler" "converter" "efficiency" energy batteryless`; `"microcontroller" "regulator" "instruction" "transient" energy model`; `"source energy" "compiler" regulator`; `"instruction scheduling" "DC-DC" energy`; and exact titles for Simba and the older Šimunić lineage.

Secondary citation lists supplied discovery leads only. Primary author, university, conference and USENIX texts support the substantive claims above. Lure (Performance Evaluation 2024, DOI [10.1016/j.peva.2024.102440](https://doi.org/10.1016/j.peva.2024.102440)) and SIREN (*Realistic Simulation for Tiny Batteryless Sensors*, [NSF-hosted author paper](https://par.nsf.gov/servlets/purl/10043907)) were screened as adjacent network/intermittent simulators, without a categorical full-text exclusion. Commercial power-electronics software also named SIMBA was excluded to avoid name confusion. The 2001 journal extension of the Šimunić work was identified, but no fully verified primary full-text comparison was completed for that extension. No comprehensive Scopus/Web of Science citation export or exhaustive 2025–2026 exclusion was performed.

Additional search families covered battery-aware compilation and recovery-aware scheduling; software transformations and converter efficiency; dynamic-load versus steady converter efficiency; history-based performance-counter demand prediction; the EPIC lineage and its compiler follow-ups; and exact-title forward leads from Simba, MASS 2024 and E-Cube, including 2025/2026 queries. E-Cube led to the 2025 Shepherd Nova paper. Irrelevant power-grid results, unsourced gap-generation pages, and a commercial simulator also named SIMBA were excluded. Search-index timestamps were not treated as publication dates. Repeated PDF retrieval failures were recorded as access limits, not as evidence that a paper lacked the proposed experiment. No complete machine-exported citation graph or reproducible all-database screening set was obtained; this is an expanded targeted audit, not a systematic review.

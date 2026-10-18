# Prior art for new simulation-only energy research questions

Checked 19 October 2026 (the session began on 18 October). Targeted primary-source investigation, not a systematic review or proof that an idea is unpublished. Read alongside [the bounded negative result](./BOUNDED_STUDY_FINDINGS.md), [the gap assessment](./RESEARCH_GAP.md) and [the supply audit](./DEEP_SUPPLY_PRIOR_ART.md). This note proposes investigations; it does not establish a new contribution.

## Recommendation

**Shortlist an independent measured-data replication and generalization study, conditional on a small feasibility audit.** WORTEX offers a particularly practical public dataset. It changes the question from making an uncalibrated circuit more elaborate to testing the reliability of empirical energy bounds under explicitly separated code distributions. This is offline analysis of previously measured hardware data, not physical validation of our FIR simulator.

Keep robust coefficient analysis as an infrastructure diagnostic. Keep input-sensitive ELMO simulation as a conditional experiment with strong limits on its interpretation. Deprioritize temporal-resolution work until calibrated, complete, synchronized traces are available. None of these ideas earns novelty merely by including FIR, Thumbulator, uncertainty, or a particular held-out split.

## 1. Empirical energy-bound reliability under code-distribution shift

### Closest work and what it already answers

[WORTEX, WCET 2024](https://drops.dagstuhl.de/storage/01oasics/oasics-vol121-wcet2024/OASIcs.WCET.2024.1/OASIcs.WCET.2024.1.pdf) trains quantile linear regression, gradient boosting and an MLP to estimate basic-block time/energy. Its BB evaluation uses an 80/20 training-and-validation/test division. It also **already evaluates whole programs**: four Mälardalen benchmarks analyzed through Heptane/IPET, independently of the AnghaBench extraction corpus. Therefore “existing models have never been tested on unseen programs” is false. Section 6 further diagnoses rare-instruction effects through explanations and a separate experiment augmenting training with test data. That diagnostic must not be mistaken for an untouched evaluation.

Measurements retain the maximum of 100 executions of a 50-fold duplicated block, under deliberately pessimistic cache/pipeline placement. These are observed measurement maxima under the stated setup, not exhaustive bounds over every operand value or physical device state. [WORTEX §§4–6](https://drops.dagstuhl.de/storage/01oasics/oasics-vol121-wcet2024/OASIcs.WCET.2024.1/OASIcs.WCET.2024.1.pdf)

### Accessible evidence

The [author-deposited dataset](https://zenodo.org/records/11066623) contains about 30,000 isolated MSP430FR5969 BB measurements at 1 MHz. Published files include CSV energy/time values and a 2.2 MB instruction-JSON archive, within a 5.7 MB total download. JSON keys preserve the original AnghaBench C source name; CSV entries link to file/block identifiers. Thus source-group splitting is supported by documented metadata. This is **not** a collection of equivalent implementations, and it is **not** an input-labelled waveform dataset. The same record links the model notebook; that Colab link returned a sign-in page during this audit, so runnable notebook access remains unverified. [Dataset description and files](https://zenodo.org/records/11066623)

### Remaining falsifiable question — proposed, not a literature claim

> At a fixed target overrun rate, how much do energy-bound violation rates and bound inflation change when code sharing is excluded by source identity and instruction-template similarity, compared with the original BB split? Can an explicitly calibrated fallback preserve useful empirical coverage on unsupported blocks without rejecting nearly everything?

A useful contribution would quantify the difference between nominal calibration, close-code interpolation and structurally separated evaluation; explain failures; and release reproducible splits and a conservative fallback policy. It must add evidence beyond “cross-validation can be optimistic.” A strong null result—similar reliability across challenging splits—would also answer the question, although its publication value is uncertain.

### Proposed test and failure gates

Reproduce original QLR/GB/MLP baselines and compare fixed safety factors, time-proportional energy and instruction-count models. Freeze code-only source-group and structural-template splits, with independent calibration data. Compare violations, bound inflation and retained fraction jointly. Match/report block length and rare-instruction support; repeat by source/cluster rather than treating correlated BBs as independent programs.

A conformal wrapper is established general methodology, including abstention and shift extensions; its exchangeability assumptions do not automatically hold across our proposed splits. Applying it alone is not a new contribution. [Angelopoulos and Bates](https://arxiv.org/abs/2107.07511)

Stop if grouped splits lack enough groups, only expose trivial length extrapolation, or no fallback improves on a fixed safety factor. Released maxima cannot establish repeat-level uncertainty, unseen-operand behavior or certified WCEC. Unrelated BBs cannot support equivalent-implementation ranking. A whole-program safety result additionally needs CFG and feasible-path evidence.

## 2. Event-weight uncertainty: diagnostic, weak standalone candidate

[Nikov et al.](https://arxiv.org/html/2301.12806) already combine STM32F0 measurements with Thumbulator event counts and configuration-specific NNLS models. Their 230 workloads comprise BEEBS and CNN variants; ten-fold validation precedes final fitting on all data. The paper explicitly observes that correlated read counts can absorb costs into coefficients. Treating each coefficient as an independently measured causal instruction cost is therefore unjustified. The university lists the [measured dataset](https://research-information.bris.ac.uk/en/datasets/stm32f0discovery-cortexm0-energy-model-data/) as available from July 2022, DOI 10.5523/bris.v5vp60ddmvu02rukwb5vtguy9; its payload endpoint timed out here, so row structure and local usability remain unverified.

**Proposed question:** can uncertainty sets calibrated without evaluation cases yield useful bounded-regret or abstaining decisions among equivalent implementations? For counts cA/cB and coefficient set W, checking whether max over w in W of w·(cA−cB) is negative is elementary robust optimization, not novelty. Compare cycles, published point model, fixed-gap abstention and Pareto count dominance. Require held-out measured regret and useful retained fraction. Arbitrary coefficient ranges, all-identical decisions, total abstention or missing equivalent measured variants defeat the contribution. Our harness can generate counts/equivalence evidence, not validate physical coefficient uncertainty using its own simulated labels.

## 3. Input-sensitive ELMO simulation: feasible but conditional

[Pallister et al.](https://arxiv.org/abs/1505.03374) already study operand-dependent energy and probabilistic worst-case modeling. Their [author paper](https://research-information.bris.ac.uk/files/114577897/Jeremy_Morse_Data_Dependent_Energy_Modeling_for_Worst_Case_Energy_Consuption_Analysis.pdf) compares random inputs, genetic search and handcrafted sparse, constant, strided and restricted-bit-width families. Thus random calibration missing unusual input energy is an established motivation.

[ELMO's official repository](https://github.com/sca-research/ELMO) supplies modified Thumbulator code, public coefficient sets and operand/context-sensitive traces. Its CPU-core scope and memory-extension caveat matter: the README warns that the extension borrows a coefficient and must not be used quantitatively. [The original USENIX paper](https://www.usenix.org/conference/usenixsecurity17/technical-sessions/presentation/mccann) establishes close Cortex-M leakage-modeling prior art.

**Proposed question:** under frozen published models, do equivalent FIR choices learned on one signal family survive predeclared amplitude/sparsity/correlation shifts, and do switching features improve model-relative regret over event counts? Reuse correctness checks; compare cycles, event models and simple Hamming-weight/distance summaries. Alternative coefficient sets are alternative model worlds, not hardware replications. Unsupported instructions, dominant memory sensitivity, or gains only with arbitrary extension weights are stop conditions. This can establish conditional model behavior; it cannot establish actual STM32 total-energy rankings or physically calibrated OOD reliability. Lower priority than measured-data replication.

## 4. Temporal resolution: defer pending suitable traces

**Proposed question:** when do explicit averaging windows, phase offsets and marker errors change implementation choices? Compare point subsampling, anti-aliased averaging and boundary misalignment. Aligned averaging across complete windows preserves their integral by construction; missing waveform detail does not automatically imply missing total energy.

Sampling-frequency effects already have direct prior art: [Saborido et al., 2015 preprint](https://doi.org/10.7287/peerj.preprints.1219v2). Direct primary full-text retrieval failed with 403, so this remains an unresolved full-text check. Do not transfer a recommended frequency across platforms.

Public leakage datasets need calibration scrutiny: [Google's power-traces](https://github.com/google/power-traces) explicitly describes blind AES datasets with differing countermeasures and requests maintainer contact for details. This does not establish calibrated whole-job joules or equivalent variants. Defer until complete synchronized raw traces are verified. The present bounded negative result is reproducible infrastructure; relabeling it does not make an independent replication of a published physical result.

## Search and access limits

Searches covered WORTEX follow-ups, conformal/WCEC/processor-energy prediction, operand-dependent models, event uncertainty, ELMO, datasets and sampling effects. No direct WCEC conformal application was located; this is not absence evidence. Primary WORTEX text/dataset metadata, Cortex-M0 model HTML and ELMO repository were inspected. WORTEX payload links are publicly listed; this agent did not download them. Colab returned sign-in, Bristol payload timed out and Saborido full text returned 403. Venue/arXiv dates, not crawl ages, establish chronology. No exhaustive citation graph or 2026 exclusion was performed.

**Coordinator follow-up:** the CSV and instruction archive subsequently downloaded
successfully and matched the record's published MD5 checksums. The local schema
audit found 30,085 records and replication questions about `nb_samples` and
`energy_per_inst`; see [the brainstorm](./RESEARCH_QUESTION_BRAINSTORM.md) for
the exact observations. This updates the payload-access status above. No energy
model was trained or evaluated in this research turn.

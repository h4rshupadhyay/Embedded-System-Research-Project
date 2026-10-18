# Literature audit: execution time versus energy ordering

Audit date: 18 October 2026. Scope: direct precedents for the original claim in `RESEARCH_GAP.md` that previous research only aggregated heterogeneous benchmarks and left equivalent implementations of one kernel untested. This note combines an independent background literature search with a second pass over the project's model provenance and newer papers. This is a focused primary-source search, not a systematic review or proof of absence. PDF page numbers below count from the first PDF page unless specified.

## Assessment

**The broad gap is contradicted by prior work.** Equivalent-program comparisons, FIR energy studies, Cortex-M0 compiler experiments, and cases where the faster implementation is not the energy winner already exist. A narrower study of **pairwise ranking reliability conditional on small cycle gaps**, with independent measurement and uncertainty analysis on a fixed MCU, remains a candidate contribution; this audit did not establish that it is unprecedented.

The distinctions matter: unequal percentage improvements in time and energy do not by themselves demonstrate an ordering reversal; an energy difference at equal time demonstrates a tie-breaking issue, rather than a strict reversal; and a compiler-generated variant is still an implementation of the same computation. These are analytical distinctions used in this audit.

## Closest primary sources

### 1. Pallister, Hollis and Bennett: equivalent benchmark/compiler configurations, including Cortex-M0 and FIR

James Pallister, Simon J. Hollis and Jeremy Bennett, **Identifying Compiler Options to Minimize Energy Consumption for Embedded Platforms**. Published online 2013; *The Computer Journal* 58(1), 95–109 (2015). [Publisher / DOI 10.1093/comjnl/bxt129](https://academic.oup.com/comjnl/article/58/1/95/495993); [author preprint, full text](https://arxiv.org/pdf/1303.6485).

**Evidence:** Preprint Table 1, p. 2, lists STM32F0DISCOVERY, Cortex-M0, 48 MHz. Table 2, p. 5, includes 2D FIR. Section 5/Figure 2, pp. 6–7, compares individual benchmarks across optimization levels, rather than only aggregated benchmark results. Section 7.1/Figures 5–6, p. 8, examines individual compiler options for Blowfish/Cortex-M0 and FDCT/Cortex-M3. Section 7.2/Figure 7, pp. 8–9, reports vectorization lowering FIR energy without changing execution time on Cortex-A8. Energy was physically measured (Section 2, p. 3).

**Overlap and limit:** This directly defeats the premise that within-kernel comparisons were absent, and supplies a same-time/different-energy example. It does not establish an uncertainty-qualified, small-cycle-gap reversal rate for Q15 FIR on STM32F051. The Cortex-A8 example should not be presented as a Cortex-M0 result.

### 2. Pallister, Eder and Hollis: directly measured slower but lower-energy implementations

James Pallister, Kerstin Eder and Simon J. Hollis, **Optimizing the flash-RAM energy trade-off in deeply embedded systems**. Preprint 2014; CGO 2015, 115–124. [arXiv record and related publication DOI](https://arxiv.org/abs/1406.0403); [full text](https://arxiv.org/pdf/1406.0403); [DOI 10.1109/CGO.2015.7054192](https://doi.org/10.1109/CGO.2015.7054192).

**Evidence:** Section 6, pp. 6–7, evaluates transformed versions of the same programs using physical energy measurements on STM32VLDISCOVERY. Across compiler levels, average energy falls 7.7% while average time rises 19.5%. Figure 5, p. 7, displays per-benchmark comparisons; Figure 6, p. 8, displays energy/time trade-off spaces for integer matrix multiplication and FDCT. Section 7, p. 9, gives FDCT factors of 0.825 for energy and 1.33 for time. Section 8 explains that basic-block relocation preserves execution flow.

**Overlap and limit:** This is direct precedent for a slower, lower-energy version of the same computation. It changes code placement between Flash and RAM on Cortex-M3; it is not a study of almost equal-cycle source-level FIR variants on Cortex-M0. FIR appears in its suite, but Section 7 says its active-region energy saving was insignificant, so do not assert a demonstrated FIR reversal from this source.

### 3. Georgiou, Blackmore, Xavier-de-Souza and Eder: validated equivalent Cortex-M0 variants and energy as a tie-breaker

Kyriakos Georgiou, Craig Blackmore, Samuel Xavier-de-Souza and Kerstin Eder, **Less is More: Exploiting the Standard Compiler Optimization Levels for Better Performance and Energy Consumption**. SCOPES 2018. [Institutional publication record / DOI 10.1145/3207719.3207727](https://research-information.bris.ac.uk/en/publications/less-is-more-exploiting-the-standard-compiler-optimization-levels/); [full author preprint](https://arxiv.org/pdf/1802.09845).

**Evidence:** Section 2, pp. 5–6, measures each generated executable using a MAGEEC board and pyenergy; all tested executables passed BEEBS output validation. Section 3, p. 6, selects the best execution-time configuration per benchmark and explicitly uses energy as the second selection criterion when performance gains tie. Figure 2, p. 7, includes `fir` and `fir2dim`, on Cortex-M0/LLVM 3.8. Figure 3, p. 8, plots multiple compiler configurations of individual programs. The discussion on p. 9 reports close correspondence between time and energy improvements.

**Overlap and limit:** Equivalent implementations, per-kernel measurements, FIR, Cortex-M0, and energy-aware tie-breaking already overlap. The checked text does not report strict pairwise reversal probabilities as a function of cycle gap or establish bit-exact equivalence over all inputs. Compiler validation is evidence of tested correctness, not formal equivalence.

### 4. Casas-Sanchez and colleagues: FIR assembly versus C energy comparisons

M. Casas-Sanchez, J. Rizo-Morente, Chris J. Bleakley and Juan Gonzalez-Hernandez, **Effect of Compiler Optimizations on DSP Processor Power and Energy Consumption**. DCIS, 2007. [UCD primary repository record](https://hdl.handle.net/10197/7098); [full deposited paper](https://researchrepository.ucd.ie/server/api/core/bitstreams/019eebce-d2ed-4e39-a32d-0c2eb6f709c0/content).

**Evidence:** Section II, PDF p. 3, describes direct current measurements on TI TMS320VC5510 at 1.6 V/24 MHz and DSPStone FIR benchmarks. Section III.C/Figure 4, PDF p. 6, compares measured energy for seven optimized assembly routines and equivalent compiled C, including FIR single/dual MAC versions. The authors attribute FIR/FFT differences partly to circular and bit-reverse addressing. Section IV.A, same page, explicitly discusses functionally equivalent source transformations. Figure 5's array/pointer comparison is for matrix and matrix-vector multiplication, **not FIR**.

**Overlap and limit:** Source/assembly implementation comparisons for a fixed DSP task are longstanding. The paper reports energy tracking large cycle reductions despite current differences, not an explicit close-cycle FIR reversal. It uses a different DSP architecture and does not provide our desired conditional error-rate analysis.

### 5. Gheorghita, Corporaal and Basten: fastest compiled code can fail to minimize energy

Stefan Valentin Gheorghita, Henk Corporaal and Twan Basten, **Iterative compilation for energy reduction**. *Journal of Embedded Computing* 1(4), 509–520 (2005). [Publisher / DOI 10.3233/EMC-2005-00050](https://journals.sagepub.com/doi/abs/10.3233/EMC-2005-00050); [authors' institutional record](https://research.tue.nl/en/publications/iterative-compilation-for-energy-reduction/).

**Verified at abstract level:** The publisher and authors' institution explicitly state that the best compiled code for performance is not always best for energy, after studying loop transformations and iterative compilation.

**Overlap and limit:** This is a direct prior-art warning against claiming the general observation as new. The publisher PDF endpoint redirected to an abstract page during this audit, so the exact processor, benchmark pairs, numerical differences, and equivalence checks were not verified from its full text. Do not attribute an exact near-tie FIR example to this paper without retrieving it.

### 6. Brandolese, Fornaciari, Salice and Sciuto: source-transformation energy models precede this project

Carlo Brandolese, William Fornaciari, Fabio Salice and Donatella Sciuto, **Analysis and Modeling of Energy Reducing Source Code Transformations**. DATE 2004, Designers' Forum, 306–311. [Conference-hosted full paper](https://past.date-conference.com/proceedings-archive/2004/DATE04/DF_FILES/10D_3.PDF).

**Evidence:** Sections 2–4, PDF pp. 1–5, treat source transformations including loop unrolling and fusion. Section 3.2, p. 3, models contributions of the processor/cache, buses and main memory using dynamic instruction and cache-miss quantities. The work studies how transformation parameters and target technology affect energy reductions.

**Overlap and limit:** A feature-based energy model for choosing between source variants is not a new class of contribution. This paper does not by itself establish an equivalent FIR near-tie rank-reversal analysis on Cortex-M0.

### 7. Georgiou and colleagues / Nikov and colleagues: the existing STM32F051 model family

Kyriakos Georgiou, Zbigniew Chamski, Kris Nikov and Kerstin Eder, **A Comprehensive and Accurate Energy Model for Arm's Cortex-M0 Processor**, 2021 preprint. [Full text](https://arxiv.org/html/2104.01055v2). Related publication: Kris Nikov, Kyriakos Georgiou, Zbigniew Chamski, Kerstin Eder and Jose Nunez-Yanez, **Accurate Energy Modelling on the Cortex-M0 Processor for Profiling and Static Analysis**, ICECS 2022, deposited 2023. [Full text](https://arxiv.org/html/2301.12806v1); [DOI](https://doi.org/10.1109/ICECS202256217.2022.9971086).

**Evidence and overlap:** The related publications describe the STM32F051/Thumbulator modeling infrastructure already used here. The ICECS paper's §§2.2–2.5 includes differently configured CNN layers and cross-validation; characterizing prior work solely as unrelated benchmark aggregation is misleading. Its §2.4 reports 1.55% timing MAPE with prefetch enabled and one wait state. An average timing error is not a pairwise error bound, but it makes independent validation of sub-0.1% cycle claims essential. No conditional ranking-risk curve was identified in the inspected sections. These related publications are one research lineage, not independent replications.

### 8. Wegener and colleagues: exact provenance of this repository's coefficients

Simon Wegener, Kris K. Nikov, Jose Nunez-Yanez and Kerstin Eder, **EnergyAnalyzer: Using Static WCET Analysis Techniques to Estimate the Energy Consumption of Embedded Applications**, 2023. [Full text](https://arxiv.org/html/2305.14968v2).

**Evidence:** §4.1 gives the six Cortex-M0 coefficients used in `run_experiments.py`, to the repository's rounding, in the same event order; it reports 2.8% model MAPE. This explicitly establishes that the present sweep reuses a published model. §5 distinguishes agreement with that model from validation against hardware.

**Implication:** The code does not train a new energy model or independently verify its accuracy. The exact mapping of these coefficients to the repository's claimed 48 MHz/prefetch/wait-state setting still needs source verification: the configuration-specific tables in source 7 contain different weights. Model MAPE is neither a confidence interval nor a guarantee that individual pair rankings are wrong or right. The observed approximately 1–2% modeled energy differences therefore need pairwise physical validation; comparing their magnitude with MAPE alone cannot settle them.

### 9. Kelefouras and Djemame: loop-variant modeling of time and energy

Vasilios Kelefouras and Karim Djemame, **A methodology correlating code optimizations with data memory accesses, execution time and energy consumption**, *Journal of Supercomputing* 75, 6710–6745 (2019). [Institutional record](https://eprints.whiterose.ac.uk/id/eprint/149053/); [accepted manuscript](https://eprints.whiterose.ac.uk/id/eprint/149053/1/journal-supercomputing.pdf); [DOI](https://doi.org/10.1007/s11227-019-02880-z).

**Evidence and overlap:** The abstract and §§1–3 model loop transformations, memory accesses, arithmetic instructions, time and power across optimization sets and input sizes. The stated evaluation includes Cortex-A9, Intel i7 and architectural simulations. This overlaps the general proposal of using instruction/memory features to compare alternative loop implementations. The inspected material does not establish our exact fixed-MCU, uncertainty-qualified cycle-gap study; the entire 33-page manuscript was not exhaustively screened for every experimental pair.

### 10. Ni and colleagues: energy-directed compiler search remains active

Youcong Ni, Xin Du, Liyan Song, Ruliang Xiao, Peng Ye and Jianwen Wang, **A Two-Stage LLVM Option Sequence Optimization Method to Minimize Energy Consumption**, *Swarm and Evolutionary Computation* 88, 101591 (2024). [Publisher abstract and section excerpts](https://www.sciencedirect.com/science/article/abs/pii/S2210650224001299); [DOI](https://doi.org/10.1016/j.swevo.2024.101591).

**Evidence and limit:** The abstract and introduction optimize compiler-option sequences for energy across eight embedded programs, using execution on hardware to evaluate candidates. This is recent overlap with choosing lower-energy compilations of the same program. Accessible excerpts do not establish an exact near-tie rank-reversal analysis; the complete experimental text was not available in this pass.

### 11. Lai and colleagues: explicit time–energy multiobjective optimization in 2026

Yuanjie Lai, Shuke Qiao, Youcong Ni, Xin Du, Ruliang Xiao and Dingbang Fang, **Interaction-aware multi-objective optimization method for LLVM compiler option sequences**, *Performance Evaluation* 171, 102543 (March 2026). [Publisher](https://www.sciencedirect.com/science/article/pii/S0166531626000039); [accessible section excerpts](https://www.sciencedirect.com/science/article/abs/pii/S0166531626000039); [DOI](https://doi.org/10.1016/j.peva.2026.102543).

**Evidence and limit:** The abstract and §§2.1–2.2 explicitly optimize execution time and energy for alternative LLVM sequences and describe Pareto selection. §2.1 names an STM32F4-based energy evaluation system. This confirms contemporary overlap with the general two-objective question. The excerpts do not settle the exact cycle-gap/uncertainty claim, and their timing and energy measurement arrangement needs full-method inspection before reuse or reanalysis. The publisher links a data repository; this audit did not inspect its contents.

### 12. Recent cross-architecture MCU profiling: screened lead, limited access

**Workload-Aware Performance Profiling of IoT Microcontrollers: A Cross-Architecture Benchmark Across Compression, Cryptography and Signal Processing**, *Applied Sciences* 16(19), 9478 (2026). [Publisher / DOI](https://www.mdpi.com/2076-3417/16/19/9478).

**Verified only in publisher-indexed excerpts:** §3.5 describes paired time/energy integration for repeated batches and ten captures per board/profile group. Direct full-page retrieval returned HTTP 429. This is a recent measurement-method lead, not evidence that equivalent FIR near-tie rankings were already studied. Author metadata and complete experimental overlap were not independently verified, so this entry is deliberately not used to establish novelty or its absence.

### TeamPlay D4.5 access limitation

The [European Commission project results page](https://cordis.europa.eu/project/id/779882/results) confirms a deliverable titled *Report on Energy Usage Analysis and on Prototype*. The [authors' DATE 2023 project paper](https://www.lexuor.net/publications/TeamPlay_DATE23.pdf), reference 7, identifies D4.5 (2020). The [GitLab document location](https://gitlab.inria.fr/TeamPlay_Public/TeamPlay_Public_Deliverables/-/blob/master/D4.5.pdf) returned a bot challenge and the Commission's download link exposed only a preparation page. D4.5 itself was not read. It cannot honestly be characterized as containing only aggregated correlations, nor excluded as possible closer prior art. Published model/tool papers above provide verified related evidence, but do not substitute for inspecting the deliverable.

## Candidate narrowed gap and what would establish it

Proposed wording, explicitly an inference from this review:

> Prior studies have measured energy and execution time across equivalent compiler-generated and DSP implementations, and have demonstrated that minimum execution time need not imply minimum energy. We investigate the reliability of choosing Q15 FIR implementations by cycle count on one fixed STM32F051 configuration. For independently measured, output-validated variants, we estimate pairwise energy-order disagreement and the energy penalty of cycle-based selection as functions of relative cycle gap, while separating strict reversals, timing ties, and measurement-indeterminate pairs. We test whether an instruction-feature model improves these decisions on held-out implementations and workloads. This combination is a candidate empirical contribution whose novelty remains subject to further literature review.

The contribution needs independent measured energy; a deterministic weighted instruction-count model can demonstrate its own predicted rankings but cannot validate physical reversals. Comparisons must be made within identical workloads and hardware configurations. Record voltage, frequency, Flash wait states, prefetch, placement, temperature conditions, compiler version, timing method, measurement interval and repetition scheme. Test correctness before ranking. Keep training and holdout groups separate by implementation/workload so repeated versions do not leak across evaluation. Report uncertainty and selection regret as well as pairwise agreement. These are proposed experimental requirements, not claims of having been performed.

For a faster variant A, define r = t_B/t_A > 1. Then E_A/E_B = (P_A/P_B)/r, so A wins in energy iff P_A/P_B < r. This is an elementary consequence of E = average power × time, not a novel theoretical result. A finite empirical power ratio cannot establish a universal safe cycle threshold.

## Search coverage and limits

Search families used in this independent pass:

- `Pallister Hollis Bennett 2013 compiler flags energy execution time correlation`
- `"energy" "execution time" "rank" compiler embedded processors FIR`
- `"energy" "time" "Cortex-M0" compiler optimization FIR`
- `"FIR" "energy" "execution time" implementation microcontroller rank`
- `"compiler optimizations" "energy" "Chakrapani" 2001`
- `"time" "energy" "rank reversal" software compiler`
- `"FIR" "energy" "loop unrolling" processor`
- `"execution time" "energy consumption" "near" compiler Cortex`
- `"Iterative compilation for energy reduction" Gheorghita Corporaal Basten pdf`
- `"energy" "rank preservation" software execution`
- `"energy" "near-tie" compiler`

Additional second-pass searches included `"energy consumption" "cycle gap" software`, `"energy" "ranking accuracy" compiler`, `"energy" "Kendall" "compiler"`, `"execution time" "energy consumption" "Spearman" "embedded"`, `"TeamPlay" "D4.5.pdf"`, exact titles of sources 7–12, and the exact model coefficients. Papers were searched by titles, abstracts, related-work references and publisher/institutional records, rather than relying solely on the phrase "rank reversal".

Primary full texts were inspected for sources 1–4, 6–8; selected sections of source 9 were inspected. Source 5 remained abstract-level, sources 10–11 were screened through publisher abstracts/excerpts, and source 12 through indexed publisher excerpts. D4.5 remained inaccessible. No subscription-library or comprehensive citation-index search was performed. No formal deduplicated screening count or systematic-review completeness claim is made. Search-engine indexing is incomplete, terminology varies, inaccessible papers may contain closer results, and non-English/uncatalogued work may be missed. **No search result supports the assertion that no paper exists.**

Before using a first-of-its-kind claim in a submission, retrieve the unresolved full texts and D4.5, follow forward citations from sources 1–3 and 7–9 in a scholarly citation index, and compare the exact proposed metrics and experimental controls against the closest papers. This is a specific remaining verification step, not evidence of an established empty gap.

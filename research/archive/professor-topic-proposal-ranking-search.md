# Research proposal for professor discussion

**Recommended topic:** Correctness-Checked Search for Execution-Time and Estimated-Energy Ranking Failures on Cortex-M0

**Research date:** 19 October 2026

**Requirements:** Original college research leading to a paper; publication optional; simulator only. The student has stated that time should not determine topic selection. This is a proposed study, not a report of completed experiments or a guarantee of novelty.

## Recommendation and rationale

Choose a targeted counterexample-search study, using streaming Q15 FIR as the main experimental family. A small second family, fixed-point matrix-vector multiplication, can subsequently test whether the search strategy transfers beyond FIR.

The existing draft asks whether three chosen implementations have identical time and estimated-energy rankings. The proposed study changes the task: **develop and evaluate a search procedure that deliberately looks for correctness-checked implementation pairs where choosing the faster one increases estimated energy, and explain the causes using simulator events and assembly.**

The potential original contribution is a focused discovery method, a reproducible corpus of explained examples, and evidence about discovery effectiveness and transfer. A larger parameter grid, a new title, existing sensitivity mathematics or simply using a simulator would not supply that contribution.

The targeted primary-source review did not identify an exact duplicate of this combined study. It did identify substantial related work, described below. Present the topic as a specific novelty hypothesis to investigate; do not claim first publication, a newly invented FIR algorithm or a newly invented robust-optimization theory.

## The pitch

> Execution time is commonly used to select embedded implementations because it is easy to obtain. Existing research studies time–energy relationships and searches for energy-efficient code, but a high overall correlation does not by itself establish that a particular implementation choice is safe. We propose a correctness-checked search that targets failures of time-based selection on Cortex-M0. Starting with equivalent streaming Q15 FIR implementations, it will generate natural implementation alternatives, validate their compiled outputs, and search for pairs where the faster implementation has higher model-estimated energy. Each example will include the source, binaries, counters and an explanation of the trade-off. We will compare the proposed search against random exploration, enumeration and ordinary energy minimization under equal evaluation budgets. Conclusions will concern estimated energy under stated simulator/model assumptions.

## Research questions

1. **Discovery:** Can targeted search find natural, correctness-checked time–estimated-energy rank reversals more effectively than simple search baselines?
2. **Explanation:** Which instruction, branch, memory and streaming-state trade-offs account for the examples?
3. **Transfer:** Do discovered patterns recur on withheld tap/block sizes and, subsequently, a second DSP kernel or other correctly supported processor configurations?
4. **Stability:** Which examples are specific to one model/configuration, and which survive explicitly stated coefficient stress tests or proper reruns under other supported settings?

RQ1 must be answered empirically. There is no assumption that targeted search will outperform the baselines or that reversals will necessarily exist in the chosen implementation family.

## Closest primary work and the proposed distinction

| Prior work | Established contribution relevant here | What the proposal would add |
|---|---|---|
| [Pallister, Hollis and Bennett, *Identifying Compiler Options to Minimise Energy Consumption for Embedded Platforms*](https://arxiv.org/html/1303.6485), 2013 preprint | Examines time/energy relationships under compiler settings, including within fixed benchmarks and on Cortex-M0; includes 2D FIR. | A method evaluated specifically for finding and explaining failures of time-based implementation selection. The broad time–energy question is already established. |
| [Schulte et al., *Post-compiler Software Optimization for Reducing Energy*](https://eschulte.github.io/data/asplos265-schulte.pdf), ASPLOS 2014 | Searches program variants retaining behavior on tests while optimizing nonfunctional properties, using predictive energy models, held-out testing and physical validation. | A targeted selection-failure objective and reusable embedded witness corpus. Generating test-correct energy-related variants is inherited methodology, not new by itself. |
| [Georgiou et al., *Less is More*](https://arxiv.org/abs/1802.09845), SCOPES 2018 | Investigates compiler-pass subsequences for performance and energy on Cortex-M0/M3. | Deliberate discovery and explanation of pairwise proxy failures rather than only finding better optimization choices. |
| [Nikov et al., *Accurate Energy Modelling on the Cortex-M0 Processor for Profiling and Static Analysis*](https://arxiv.org/html/2301.12806v1), 2023 | Supplies configuration-dependent Cortex-M0 event models and modified-simulator infrastructure. | A new use/evaluation of that foundation. The energy model and simulator are reused resources. |
| [Wegener et al., *EnergyAnalyzer*](https://arxiv.org/html/2305.14968v2), WCET 2023 | Event-based static energy analysis, including the exact six coefficients used in the supplied draft. | Search for implementation-selection failures and their explanatory artifacts. The model itself is not a contribution of this project. |
| [Aragón Jurado et al., *Automatic software tailoring for Green Internet of Things*](https://rodin.uca.es/xmlui/handle/10498/35368), 2025 | Optimizes LLVM transformation sequences while accounting for uncertainty. | Supports narrowing the claim away from generic uncertainty-aware energy optimization toward targeted proxy-failure discovery. |

This table establishes distinctions from the examined papers, not an exhaustive absence claim. A final literature section should also check energy-aware mutation/metamorphic testing and quantitative energy-verification tools before claiming broad novelty for automated energy testing or counterexample generation.

## Proposed method

### 1. Define a strict computation contract

Specify input and coefficient domains, accumulator width, scaling, rounding/narrowing, overflow restrictions and initial history. Every compared variant must implement the same stream-to-stream function and equivalent logical final state. Include all recurring history maintenance in the complete-stream measurements; keep a separate convolution-only interval for explanation.

Keep numerical precision fixed. Precision reduction, dropped outputs or approximate filtering would answer a different question.

### 2. Generate natural implementation alternatives

Use a documented transformation family rather than unconstrained random assembly mutations:

- Linear block history versus a true ring buffer.
- Per-tap wrap handling versus splitting a ring traversal into linear segments.
- Index traversal versus pointer traversal.
- Unroll factors and remainder loops.
- Accumulator organizations only where the arithmetic contract permits them.
- Coefficient placement in flash or SRAM only if linker placement and model/simulator support are verified.

Arm's production FIR documentation already describes block state and its avoidance of circular addressing; these techniques are established. Their role here is to provide realistic candidate implementations and resource trade-offs. [Arm CMSIS-DSP FIR documentation](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html).

Exclude dummy arithmetic, deliberate delays and padding inserted solely to obtain a reversal. Do not create apparent energy improvements by omitting validation or state work from one candidate's accounting interval.

### 3. Check correctness before interpreting performance

Compare actual ARM outputs against an independent reference on boundary, random and structured inputs. Check block-partition consistency: concatenated outputs for one stream should agree across different block divisions. Check retained logical history, memory bounds and permitted arithmetic behavior.

For selected minimized examples, use bounded formal equivalence checks if tractable. CBMC supports assertions, memory-safety checks and bounded program analysis; proof claims must state the input domain, fixed workload bounds and successful unwinding checks. These checks do not verify compiler correctness or simulator timing, so target-output checks remain necessary. [Official CBMC tutorial](https://diffblue.github.io/cbmc/cprover-manual/md_cbmc-tutorial.html).

### 4. Target ranking disagreement

For candidates A and B under the same workload/configuration, define a strict reversal by:

`(cycles(A) − cycles(B)) * (estimated_energy(A) − estimated_energy(B)) < 0`.

Ties are reported separately. The search uses disagreement as its target rather than simply minimizing energy.

Develop a policy that uses previously observed transformation effects on counters and cycles to prioritize the next candidate. Mixed event trade-offs and small cycle differences are useful hypotheses for guidance; small cycle differences are not a necessary condition for reversal. Event dominance can explain why particular observed pairs cannot reverse under positive weights, but obtaining counters already consumes a simulation: do not claim that post-run pair pruning itself saves simulator evaluations.

Start with a fixed published model and matching simulator assumptions. Distinguish candidate generation, search objective and search policy so that each can be evaluated independently.

### 5. Minimize and explain each example

Reduce the transformation sequence or workload while preserving correctness and the strict reversal. Avoid a claim of globally minimal examples; a locally reduced reproducer is sufficient if reduction criteria are documented.

Save source, flags, compiler version, linker map, binary hashes, disassembly, simulator patch/version, model coefficients, counting boundaries and raw counters. Explain the cycle and modeled-energy differences through the compiled code. Deduplicate compiled kernel implementations without losing relevant placement or state-layout distinctions.

## Evaluation that could demonstrate a meaningful contribution

Compare the proposed policy against:

1. Uniform random candidate selection.
2. Deterministic enumeration over the same candidate family.
3. Ordinary energy-minimization search using the same generation machinery.
4. An ablation using the disagreement target without event-based guidance.

Equalize compile/simulation evaluations, candidate validity rules and available search information; also report total wall time including correctness-check overhead. A complete enumeration supplies ground truth for a small bounded subspace. In larger spaces compare budgeted prefixes and repeated randomized trials.

Report evaluations to the first distinct example, discovery rate, number and diversity of mechanisms, correctness rejection rate, example size and persistence on withheld workloads. Trials finding no example must remain in the analysis as budget-censored failures; do not average only successful runs. Fix held-out conditions before tuning the search policy. A second kernel tests transfer; additional inputs with unchanged traces do not establish performance diversity.

The scientific value would be evidence that targeted guidance discovers failures more efficiently or finds mechanisms missed by simpler search, together with a useful explained corpus. If guidance has no advantage, report it. A tool that produces only a larger score on the same objective used to select its outputs is insufficient evidence of practical benefit.

## Feasibility and current uncertainties

The study can be implemented with software: ARM GCC, the modified STM32F0 Thumbulator, analysis scripts and optionally a bounded model checker. No newly collected power measurements are required for the model-level question. The existing source repository, patch and raw results have not been supplied, so end-to-end reproduction is not yet verified. A clean upstream simulator build also exposed a host-linking compatibility issue, recorded in the earlier assessment.

Verify the simulator's actual timing modes before committing to a prefetch/wait-state sweep. A source-level declaration of a flash setting is not proof that the ISS models it. Use a different setting's coefficients only with appropriate matching traces/timing; do not interpret arbitrary weight perturbations as a different real processor configuration.

The [Bristol energy-model dataset record](https://research-information.bris.ac.uk/en/datasets/stm32f0discovery-cortexm0-energy-model-data) was checked as a possible source for a data-calibrated uncertainty study. Its landing page was accessible, but advertised data/readme downloads returned HTTP errors during this assessment. Paired measurement data suitable for independently validating equivalent implementation choices was not inspected. Consequently that dataset is **not a dependency** of the recommended project.

## Pilot checkpoint before a definitive novelty claim

Begin with a small pilot of natural variants, a tail and a non-tail workload, one pinned toolchain and one verified model/configuration. Validate actual outputs and remove machine-code duplicates.

Proceed with the targeted-discovery claim when the pilot shows natural strict reversals and a sufficiently varied candidate space. Then test whether guidance improves discovery against the baselines. A pilot need not establish final method superiority, but it should demonstrate that the phenomenon is available to study.

If no reversals appear, inspect event dominance, compiler-collapsed variants and accounting correctness before expanding the search. A finite complete subspace can support a bounded invariance result. A failed heuristic search proves neither impossibility nor a novel general law. Do not promise the professor that a reversal or improvement has already been found.

## Expected contribution statement

> We propose and evaluate a correctness-checked search method targeting execution-time/estimated-energy ranking failures in embedded DSP implementations. The study contributes an explicit search objective and event-based guidance, an independently validated corpus of reproducible model-level examples, and an empirical comparison against random exploration, enumeration and ordinary energy minimization, with streaming Q15 FIR as the principal case study.

This is intended contribution wording for a successful completed study. At proposal time, describe these as objectives, not achievements. Here “independently validated” means independent functional reference and reproduction of the recorded simulator/model results, not independent validation of physical energy consumption.

## Answers to likely professor questions

**What is new compared with your current draft?** A developed and evaluated discovery method with explanatory artifacts, replacing a passive three-implementation ranking comparison.

**Isn't program autotuning already established?** Yes. That is why ordinary energy-minimizing search is an explicit baseline. The narrower candidate novelty is deliberate discovery of failures of the time proxy and the usefulness of its guidance/explanations on embedded kernels.

**Why does this matter?** It tests a common implementation-selection shortcut and produces inspectable cases or bounded evidence about when it works. The corpus could help assess model-based selection tools and future energy models.

**Can it be done without hardware?** Yes for estimated-energy conclusions. Physical ranking claims would require independent power measurements.

**What if everything agrees?** Report the bounded result and its structural explanation. Reconsider the discovery-focused framing if the pilot supplies no meaningful search problem.

**Can you guarantee it is original?** No exhaustive priority guarantee is justified. The primary-source review supports a specific candidate gap; the professor should assess that gap against institutional originality expectations, and the pilot must establish usefulness.

## Research provenance

The proposal combines targeted primary-source literature checks with a background-agent critical audit and direct checks of upstream references and dataset access. The searched themes included compiler energy optimization, behavior-preserving variant search, time–energy proxy failures, energy counterexamples, uncertainty-aware optimization and Cortex-M0 models. This was not a systematic review. No new kernel experiments were performed during topic selection.

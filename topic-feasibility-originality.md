# Feasibility and originality of the Q15 FIR time–energy ranking study

Assessment date: 19 October 2026.

Confirmed project requirements: a college research project producing a paper with an original contribution; publication is **not required**. Available platform: **simulator only**. The recommendation below is calibrated to these constraints; comments on publication describe an optional higher bar.

Input: the supplied manuscript, beginning “Execution time is often used in place of energy…”. The workspace contained no experiment source code, simulator patch, binaries, logs or result tables. Experimental counts and outcomes below are therefore **claims in the draft**, not independently reproduced findings. Literature facts are linked to primary sources; proposed changes and publication assessments are our judgments.

## 1. Decision

**Continue the topic as a simulator-based college research project. Add an explanation and robustness analysis of the rankings to strengthen the original contribution.**

| Question | Assessment |
|---|---|
| Can this experiment be implemented? | Yes. The design is small and uses existing compiler, simulator and modeling methods. Rebuilding the complete experiment still needs the missing artifacts. |
| Is it suitable for a student project? | Yes, especially as a reproducible experimental-methodology project with explicit numerical semantics and limitations. |
| Is the broad question original? | No. Execution time as an energy proxy, including on Cortex-M0, is established research. |
| Is this exact experiment an identified duplicate? | No exact duplicate was identified in the targeted search. This does not establish priority. |
| Is the current contribution substantial? | Modest: a narrowly scoped case study of three particular implementations under one simulator/model setting. |
| Is the present draft ready for a research paper? | In our judgment, it needs stronger positioning, reproducibility and analysis. A workshop or replication contribution may be plausible depending on venue; a strong full paper would need a clearer additional finding. Acceptance cannot be inferred from topic alone. |

The draft already makes several sound choices: it distinguishes estimated from measured energy, reports the equivalence correction, retains the zero-reversal result and acknowledges the changed build environment. Preserve these qualifications.

### Recommendation for the confirmed college-project scope

Keep the FIR topic. Hardware measurement is outside the available scope and is not a prerequisite for answering a clearly model-based research question. Avoid framing the work as validation of physical energy consumption.

Add one manageable contribution: explain and stress-test the observed ranking agreement. First classify implementation pairs by whether one reduces every modeled event or whether they trade events against each other. For mixed-sign pairs, calculate how much the weights must change before the estimated-energy order changes. If there are no mixed-sign pairs, report that structural explanation and deliberately evaluate a small number of equivalent variants that create meaningful event trade-offs. Preserve all results, including continued agreement.

The proposed question is: **How robust is execution-time-based selection among equivalent Q15 FIR implementations to changes in the assumed Cortex-M0 energy costs?** Keep the existing 135-configuration grid as the baseline. Validate ARM outputs and add a few non-multiple-of-four tap counts before broadening the study further.

The basic dominance and sensitivity mathematics is established reasoning, not a newly invented theorem. A plausible original college-project contribution is the specific reproducible application, event-level explanation and robustness characterization. This application remains a candidate contribution until a focused related-work check and the experiments support it. Confirm that this level of originality satisfies the supervisor's rubric.

Suggested title: *Execution-Time and Estimated-Energy Ranking Robustness for Equivalent Q15 FIR Implementations on Cortex-M0*.

## 2. Closest prior work and the actual originality boundary

| Primary work | Overlap with this topic | Remaining distinction |
|---|---|---|
| Pallister, Hollis and Bennett, *Identifying Compiler Options to Minimise Energy Consumption for Embedded Platforms* (2013 preprint; subsequently published) | Hardware time/energy comparisons across five embedded platforms and ten benchmarks, including Cortex-M0 and 2D FIR. Section 5 reports particularly close time–energy behavior on M0. Compiler settings are varied within each benchmark. | Your comparison varies manually written Q15 FIR styles and explicitly tests within-condition ranks. This is narrower than the existing question, rather than a newly discovered problem. [Paper, Tables 1–2 and §§4–6](https://arxiv.org/html/1303.6485). |
| Georgiou et al., *Less is More: Exploiting the Standard Compiler Optimization Levels for Better Performance* (2018) | Hardware time/energy experiments on Cortex-M0/M3, 71 BEEBS programs including `fir`, LLVM optimization subsequences and executable self-tests. Time and energy improvements closely track each other on these targets. | Alternative versions of a fixed computation and correctness checks are already established. Your specific manual implementations, Q15 contract and ranking analysis provide the narrower distinction. [Author paper, §§2–3](https://arxiv.org/pdf/1802.09845). |
| Georgiou et al., *A Comprehensive and Accurate Energy Model for Arm’s Cortex-M0 Processor* (2021) | Existing modified Thumbulator, six-event energy modeling and processor-configuration dependence. | Reusing the platform/model is valid methodology, but cannot be claimed as a new modeling contribution. [Author paper](https://arxiv.org/abs/2104.01055). |
| Wegener et al., *EnergyAnalyzer* (2023) | Publishes the exact six energy coefficients used in the draft, to the displayed rounding, in §4.1. | The new contribution must come from the experiment, analysis or reproducibility artifact. [Author paper](https://arxiv.org/html/2305.14968v2#S4.SS1). |
| Arm CMSIS-DSP | Established Q15 FIR implementations and documented numerical contracts. | Indexing, pointer traversal and unrolling are familiar techniques. A production-library baseline would make the evaluation more useful, after reconciling semantics. [Arm documentation](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html). |

An additional relevant counterexample is Pallister, Eder and Hollis, *Optimizing the flash–RAM energy trade-off in deeply embedded systems* (2014): moving selected code to RAM can reduce measured energy while increasing time. This motivates controlled memory-placement experiments, although it does not duplicate this FIR study. [Author paper](https://arxiv.org/abs/1406.0403).

**Revise the present gap paragraph.** It suggests that earlier benchmark studies mixed differences between algorithms with compiler effects. Pallister also compares compiler choices within each fixed benchmark. The defensible distinction is the controlled comparison of manually authored implementation styles and their selection rankings.

A supportable contribution statement is:

> We provide a reproducible case study of execution-time and model-estimated-energy ranking agreement among three equivalent Q15 FIR implementation styles on a specified STM32F051 simulation setup.

Do not claim that this establishes universal validity of execution time as an energy proxy or that equivalent-implementation energy comparison is itself new.

## 3. Technical feasibility and issues to resolve

### A. The energy model is traceable, but its applicability must be documented

The missing reference [2] can be filled with **Wegener, Nikov, Nunez-Yanez and Eder, *EnergyAnalyzer: Using Static WCET Analysis Techniques to Estimate the Energy Consumption of Embedded Applications*, 2023**, §4.1. Its equation matches all six draft coefficients. That version reports 2.8% MAPE against physical measurements. Its separate sub-1% analysis results concern static estimates versus model estimates, not hardware accuracy. [Paper](https://arxiv.org/html/2305.14968v2).

Document the frequency, supply assumptions, prefetch mode, flash wait states and intended energy boundary associated with the chosen equation. The related 2023 modeling paper supplies distinct coefficients for different frequency/prefetch/wait-state combinations; its Table 2 is not the exact equation used here. Map counters by event meaning, not by counter number, because numbering differs between papers. [Nikov et al., §§2.4–2.5](https://arxiv.org/html/2301.12806v1).

Regression coefficients are joint fitted weights, not necessarily isolated physical costs of individual operations. Consequently, the background sentence implying a fixed physical cost for each event should be qualified. The modeling authors themselves discuss how regression attributes costs among counters. [Nikov et al., §2.5](https://arxiv.org/html/2301.12806v1#S2.SS5).

### B. Perfect ranking agreement needs an explanation

The absence of cycle count from the energy formula does **not** establish independent evidence: cycles and energy may depend on overlapping instruction and memory events.

For each within-condition pair, let `d = counters(A) − counters(B)` and let `w` be the six positive weights. Then:

`estimated_energy(A) − estimated_energy(B) = w · d`.

If A is faster and every component of `d` is non-positive, its estimated energy cannot exceed B's under **any non-negative weights**. In that case agreement is structurally guaranteed by event dominance. If `d` has mixed signs, weighting can matter. These are algebraic consequences of the stated model, not findings about your unavailable counter data.

Add an event-difference table for all 135 pairs. Count pairs that are dominated, mixed-sign or tied. Explain whether agreement comes from fewer instructions, fewer branches, fewer memory accesses or an actual trade-off. This would make the null result more informative.

A feasible sensitivity analysis for mixed-sign pairs is to compute the coefficient change needed to reach a tie. For an independently bounded relative perturbation `|w'_i − w_i| ≤ epsilon*w_i`, a pair with `w·d < 0` retains its ordering if:

`w·d + epsilon * sum(w_i * |d_i|) < 0`.

This is a proposed robustness calculation. Arbitrary coefficient perturbations are stress tests, not calibrated physical uncertainty; model MAPE must not be substituted for `epsilon`.

### C. Sub-1% gaps cannot establish hardware ordering

The manuscript reports minimum cycle and estimated-energy gaps of 0.44% and 0.53%. Those are valid model-level differences if the counters and arithmetic are correct. They do not establish that physical hardware would preserve the order.

The published 2.8% MAPE is an aggregate model-performance measure, **not** a per-case error bound, confidence interval or proof that every sub-2.8% difference is meaningless. Correlated errors can preserve a close ranking; implementation-specific errors can reverse it. Close cases need hardware validation or an explicit unresolved-hardware-ranking qualification. [Model accuracy source](https://arxiv.org/html/2305.14968v2#S4.SS1).

### D. Verify the compiled target, not only host C

The claimed 569 host tests are useful finite test evidence. They are not a proof for all inputs and do not verify the actual ARM binaries.

For every measured ARM configuration, extract the output buffer or a sufficiently strong validation result and compare against an independent reference. Keep validation outside the timed/energy-counted region. Also inspect optimized assembly to confirm the FIR computation remains present and outputs are observable to prevent dead-code elimination.

Specify input domain, history layout, signed shift, narrowing and overflow behavior. A 64-bit final reference sum alone does not prove all 32-bit **intermediate partial sums** are in range. Use a conservative bound such as `max_abs_input * sum(abs(coefficients)) ≤ INT32_MAX`, or check partial sums in the executed accumulation orders. GCC documents its signed conversion and shift conventions, but host-only agreement still does not replace target testing. [GCC integer behavior](https://gcc.gnu.org/onlinedocs/gcc/Integers-implementation.html).

Arm's standard Q15 FIR uses 64-bit accumulation and saturates the output; the fast variant uses a 32-bit accumulator and also saturates. Your draft describes narrowing without saturation. A CMSIS baseline needs a shared numerical contract or a restricted domain where outputs agree; full-range Q15 equivalence cannot be assumed. [Arm FIR documentation](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html).

### E. Improve the experimental coverage without inflating it unnecessarily

- **Implementation names:** the prose describes CIRCULAR as a backward pointer walk through linear history. That does not establish a ring buffer. Inspect the code; rename it POINTER if no wraparound state exists.
- **Unrolled tails:** all measured tap counts, 8/16/32, are divisible by four. Host tests may exercise the tail for correctness, but the timing experiment does not. Add representative non-multiples of four.
- **Counting boundaries:** identify exactly where counters start/stop. Separate kernel work from startup, input initialization, validation and termination; use the same boundaries for all variants.
- **Input data:** extra random inputs improve correctness coverage, but may add no performance information when control flow and addresses do not change. An event-class model does not capture operand switching just because more input values are tried.
- **Streaming scope:** if claiming applicability to real streaming FIR, include equivalent state/history maintenance costs across blocks, or explicitly limit the claim to the convolution kernel.
- **Build artifacts:** retain ELF files, disassembly, linker maps, raw counters, flags and tool versions. Different source styles may compile into identical inner loops.

These are recommendations derived from the draft design; code inspection is needed to determine which are existing defects.

### F. Reproducibility has a concrete setup risk

The upstream repository was checked directly. `teamplay-D4.5` is currently a **tag**, at full commit `c55ea1b1926b792d7aabb7e3495b55a7b69ef134`, rather than a branch. Correct the manuscript's wording. [Pinned upstream source](https://github.com/PicoPET/thumbulator-stm32f0x/tree/c55ea1b1926b792d7aabb7e3495b55a7b69ef134).

A clean checkout of that tag was built with `make board` using Ubuntu GCC 11.4.0. Compilation reached the link stage and failed with multiple definitions of `gprReadHooks` and `gprWriteHooks`. This is a directly observed local build result for **unmodified upstream**, not a failure of your unavailable patched project. It demonstrates the need to supply the patch and a pinned host build environment. The upstream Makefile's board target sets the STM32 SRAM base. [Makefile](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/Makefile).

No FIR experiment was rerun. The reported 135 completions, equivalence results and zero reversals remain unverified here.

## 4. What zero reversals supports

Keep the result even if it remains zero. The sound conclusion is that, for this finite experiment under this model, the observed rankings coincide.

The 135 configurations are a factorial grid, not 135 independent hardware replications. Each condition has only three implementations and three pairwise comparisons, which share implementations. Conditions also share source and toolchain. Do not derive a population probability of reversal by treating these comparisons as independent random trials.

Report ties and the exact Kendall statistic variant. Include implementation-selection agreement and **energy regret**: `(estimated energy of fastest choice − minimum estimated energy) / minimum estimated energy`. Regret is zero in the reported experiment, but is useful when extending it. Report percentage-gap denominators explicitly.

The old two reversals should remain unconfirmed because code and environment both changed. Attributing their disappearance to one factor requires a controlled code-version × environment comparison with recoverable artifacts.

## 5. Recommended next study

An appropriate strengthened question is:

> Under which implementation and processor-configuration conditions does choosing the fastest equivalent FIR implementation also minimize estimated energy, and how robust are those decisions to model uncertainty?

This is a proposed direction whose exact novelty needs a further focused search once its scope is fixed.

**If only simulation is available:** first reproduce the existing grid and verify target outputs; analyze event dominance and coefficient thresholds; add tail cases; then compare a small number of supported prefetch/wait-state settings with matching energy models and timing support. Do not simply swap coefficients while retaining counters/cycles for a different hardware setting. A title reflecting the scope would be *Robustness of Execution-Time-Based Selection for Q15 FIR Implementations under Cortex-M0 Energy Models*.

**If measurement equipment is available:** validate representative cases and the closest predicted pairs on the STM32F051 at fixed documented voltage, frequency and flash configuration. Use a clearly delimited kernel interval, enough repeated work to resolve short kernels, quantified harness overhead and repeated physical measurements. Report paired differences and uncertainty, including systematic measurement limits. A board alone supports timing checks; a power/current measurement setup is additionally required for independent energy validation. Hardware integration of sampled power over execution time is an established method. [Pallister et al., §1 and hardware appendix](https://arxiv.org/html/1303.6485).

Do not expand kernels, compilers and boards simultaneously. Resolve correctness and model applicability first, then select the extension that directly tests the revised question. Finding a reversal is not a success criterion: an explained and robust agreement result can also be useful.

## 6. Immediate priorities

1. Recover the complete experiment repository, simulator patch and raw results; pin both host and ARM toolchains.
2. Add the exact model citation and its configuration provenance; correct the gap paragraph and simulator tag wording.
3. Validate the compiled ARM outputs and counting boundaries.
4. Calculate event dominance, mixed-sign trade-offs and ranking sensitivity before running a much larger grid.
5. Choose a bounded simulation study or a hardware-validation extension according to available equipment and the intended venue.

## 7. Search scope and limits

The targeted primary-source search covered time–energy proxy validity, compiler choices, equivalent embedded implementations, FIR, Cortex-M0/STM32F0 energy models, Thumbulator, flash–RAM placement and CMSIS-DSP. Sources included author-hosted preprints, Arm/GCC documentation, university records and upstream source code. Searches and source checks were performed on 19 October 2026.

This is a feasibility and originality assessment, not a systematic literature review or a plagiarism check. No exact duplicate was identified among the sources examined; unpublished work, inaccessible papers and differently described studies may exist. The originality verdict is therefore **incremental contribution with a viable path to stronger evidence**, not certified uniqueness.

## 8. Concrete extensions for the simulator-only college project

These are proposed experiments, not predicted outcomes. Select one main question and a supporting analysis rather than treating every option as compulsory.

| Extension | New research question | Work to perform | Useful output | Relative effort |
|---|---|---|---|---|
| Ranking robustness | How sensitive is a time-based implementation choice to the event weights? | Reuse raw counters; classify event dominance; calculate tie thresholds for mixed-sign pairs; run declared perturbation scenarios. | Per-pair stability margins and an explanation of agreement or reversals. | Lowest after reproducing baseline |
| Complete streaming FIR | Does including history maintenance change implementation selection as block size and RAM budget vary? | Compare linear-state indexed, pointer and unrolled forms with a genuine ring buffer, all processing the same continuous signal and maintaining equivalent state. Count state copying and wrap handling. | Cycles/sample, estimated energy/sample, RAM and code-size trade-offs; regions where each implementation is preferable. | Moderate; recommended practical extension |
| Processor-configuration dependence | Does the within-configuration time–energy agreement persist across supported prefetch/wait-state settings? | Verify ISS timing support; run each supported setting and use its matching published model. Compare ranks within each setting, then compare choices across settings separately. | A configuration-by-workload map of selection stability. | Moderate to high; simulator support must be established first |
| Compiler portability | Does an implementation recommendation survive a compiler change? | Rebuild a controlled subset under two pinned compiler versions; validate target outputs; compare disassembly, event deltas and winners. | A reproducible account of when source-level recommendations depend on code generation. | Moderate; optional follow-up |

### Why complete streaming FIR is worth adding

Arm documents a block-state layout that avoids circular addressing at the cost of a larger state buffer, and updates state after processing each block. This is an established implementation technique, not a new FIR algorithm. The proposed experiment asks a narrower question about complete modeled resource costs and selection boundaries under the chosen Cortex-M0 setup. [Arm FIR documentation](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html).

For example, a ring implementation may perform fewer history copies but more wrap-management instructions. A block-based implementation may use more RAM while amortizing state maintenance over more outputs. Those are hypotheses to test. The present draft's pointer walk, as described, does not establish that a genuine ring buffer was evaluated.

### Recommended combined scope

Use **complete streaming FIR as the main practical extension and ranking robustness as the supporting analysis**. Retain the current experiment as a kernel-only baseline so that adding state costs has an interpretable before/after comparison.

An initial extension grid could be:

- Four implementations: indexed linear state, pointer linear state, four-way unrolled linear state and a genuine ring buffer.
- Five tap counts: 7, 8, 15, 16 and 32, covering several unrolled-tail lengths.
- Four block sizes: 1, 8, 32 and 128, including low-latency and batched operation.
- Three optimization levels: `-O2`, `-O3` and `-Os`, with the original five-level experiment retained separately.

This is 240 proposed configurations, before any optional platform-setting factor. Use the same long input sequence and coefficient set for equivalent variants at each tap count. Process multiple blocks; check that partitioning the same stream differently preserves the concatenated output. Check values, final retained history and bounds with an independent reference. If ring and linear layouts differ internally, compare their logical histories rather than raw state-array bytes.

Measure convolution-only and complete processing intervals separately. Record cycles/output sample, estimated nJ/output sample, RAM use and flash/code size. Show which implementation minimizes each metric and identify trade-offs rather than assuming a single universal winner. Normalize across block sizes by processed samples; raw energy per block is not comparable when block sizes differ.

For the robustness analysis, compare a fastest-choice baseline, the minimum-energy choice under the nominal model, and a rule that identifies whether a single choice stays best throughout a declared coefficient range. If none does, report the unresolved candidate set. Evaluate model-based regret when making a forced choice. Do not label a stress-test range as a physical confidence interval or infer reversal probabilities from arbitrary random weights.

Published Cortex-M0 models already vary with prefetch, wait states and frequency. Configuration variation is therefore an existing modeling capability; your candidate contribution is its effect on selecting these equivalent FIR implementations. Only add this factor after confirming that the selected ISS version represents the required settings and that counters and timing correspond to the chosen model. [Nikov et al., Table 2](https://arxiv.org/html/2301.12806v1#S2.SS5).

### Originality guardrails

Uncertainty-aware software-energy optimization is not broadly new: a 2025 study explicitly handles uncertainty when optimizing LLVM transformation sequences for embedded devices. It differs from the proposed event-weight and FIR-selection analysis, but must be considered in related work. [Aragón Jurado et al., *Automatic software tailoring for Green Internet of Things*, author university record](https://rodin.uca.es/xmlui/handle/10498/35368).

Likewise, ring buffers, loop unrolling and Pareto trade-offs are established concepts. A defensible college-project contribution would be the controlled experiment, its complete-stream selection map, event-level explanation and reproducible robustness analysis. A targeted search has not established that this exact combined study is already published; it has also not certified its uniqueness.

If all rankings still agree, report whether that follows from event dominance and how state costs affect absolute savings. If the compiler generates identical code for different source variants, document and deduplicate them in interpretation. Avoid adding redundant runs solely to increase the configuration count.

Suggested combined-study title: *Execution-Time and Estimated-Energy Trade-offs in Streaming Q15 FIR Implementations on Cortex-M0*.

### Work sequence and deliverables

1. Reproduce the supplied baseline with the missing patch, scripts and raw data, and validate the ARM outputs.
2. Establish one numerical and streaming-state contract; implement and validate the genuine ring variant and fair state maintenance for all variants.
3. Pilot a small set of workloads to verify counting boundaries, retained computation, RAM fit and nonredundant compiled implementations.
4. Run the declared extension grid and preserve ELF files, maps, disassembly and counters.
5. Produce the selection/trade-off plots and pairwise event/sensitivity analysis.
6. Write the paper around the observed findings, with related work distinguishing inherited techniques from the specific contribution.

The intended deliverables are a reproducible simulator experiment, bit-exact target validation, raw result tables, resource-trade-off plots, robustness calculations and a bounded research paper. No hardware-energy claim is required.

## 9. Sharper candidate contribution: explainable implementation selection

The user's requirement is substantive novelty. A larger benchmark grid alone is insufficient. A more specific candidate is a **tool for selecting equivalent FIR implementations under declared energy-weight uncertainty**, with a checkable explanation of each recommendation.

Proposed question: *Can event-counter differences identify when the fastest equivalent FIR implementation is a robust energy choice, and construct an alternative model when that choice fails?*

The tool would consume validated per-implementation counters, cycle counts, nominal positive energy weights and explicitly stated bounds on those weights. It would return:

1. The fastest implementation and nominal minimum-energy implementation.
2. Whether the fastest stays an energy minimum throughout the declared uncertainty set, distinguishing unique winners from ties.
3. A stability threshold for that decision when applicable.
4. If the choice fails, an explicit admissible coefficient vector and competing implementation that demonstrate the failure under the model.
5. Optionally, an implementation minimizing worst-case absolute model-based regret among candidates meeting stated cycle/RAM limits.

For a uniform relative weight box below 100% uncertainty, pairwise event differences permit exact worst-case comparisons using elementary linear optimization. This is established mathematical reasoning; the radius or minimax formulation must not be presented as newly invented theory. The candidate contribution is the integration, implementation-selection explanations, witness generation and evaluation for equivalent FIR code.

Evaluation should compare fastest-only selection, nominal-energy selection and the proposed robust selection/ambiguity rule. Record disagreement cases, stability thresholds, witness validity, ambiguity rate, computation overhead and worst-case regret under the declared model set. Include genuine ring/linear-state and unrolling variants to investigate meaningful event trade-offs. Validate outputs before treating any performance observation as comparable. A model-specific witness demonstrates possible estimated-energy reversal; it is not evidence that real hardware has that energy behavior.

Start with a small pilot. If all realistic implementations are event-dominated, a sophisticated selector may add little value: report the structural finding and reconsider scope instead of manufacturing reversals using useless instructions or unjustified coefficients. Coefficient boxes must be labeled stress-test assumptions unless calibrated from suitable data. Model fitting error cannot directly determine independent per-coefficient bounds.

### Closest work and novelty status

- *Automatic software tailoring for Green Internet of Things* already optimizes LLVM transformation sequences with uncertainty, using physical experiments. Thus uncertainty-aware energy optimization itself is not the gap. [Author-university record](https://rodin.uca.es/xmlui/handle/10498/35368).
- Sieh et al., *Combining Automated Measurement-Based Cost Modeling with Static Worst-Case Execution-Time and Energy-Consumption Analyses* (2019), discuss Γ-robustness for uncertain benchmark measurements in the future-work/vision section on model fitting. That is related to, but distinct from, the proposed fixed-model implementation-selection explanations and counterexample weights. [Author paper, §V.E](https://www4.cs.fau.de/Publications/2019/sieh_19_esl.pdf).

The focused search did not identify an exact duplicate of this FIR selection tool. That observation does not establish first publication. Treat it as a candidate original application/methodology contribution for a college paper, pending a closest-work comparison and a pilot demonstrating useful nontrivial cases. If the requirement is a new optimization theory or a fundamentally new FIR algorithm, this proposal does not yet meet that stronger requirement.

Working title: *Explaining and Checking Energy-Efficient FIR Implementation Choices under Model Uncertainty*.

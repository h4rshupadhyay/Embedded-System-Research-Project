# Clarity revision: outline and editorial checks

20 October 2026. Branch: `research/fir-clarity-rewrite`.
Starting commit: `cf53328`. This editorial revision uses the installed
`research-paper-writing` skill from
[Master-cai/Research-Paper-Writing-Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills).

## Story and section outline

Thesis: exact FIR implementation comparisons depend on arithmetic information,
state representation, and the information visible to the compiler. Controlled
comparisons expose these effects in a finite Cortex-M0 model case study.

1. Introduction and related work: motivate the comparison problem and state
   the empirical contribution without implying a new algorithm.
2. Exact contract: explain legality, native partials, and the comparisons
   that isolate width, sharing, and representation.
3. Experimental design: define costs, distinguish retrospective from frozen
   prospective evidence, and state the panel and intervention questions.
4. Original results: show the ranking reversal, separate sharing from
   transposition, and interpret event sensitivity.
5. Compiler and fresh-panel results: explain the intervention and the two new
   wide-array counterexamples, including adverse and unavailable results.
6. Discussion and conclusion: explain the lesson, external-validity limits,
   and exactly what saved-evidence portability establishes.

## Revision constraints

- Preserve numerical table cells, mathematical contracts, authors,
  coefficient/input identities, raw measurements, and declared unavailability.
- Use readable headline precision; retain exact arithmetic in tables/artifacts.
- Tie 24/32 explicitly to two fresh wide 48-tap arrays.
- Preserve limits on physical energy, algorithmic novelty, optimality and
  general implementation selection.
- Move internal workflow labels and literature-access history out of the
  narrative. Internal checks are not external peer review.
- Preserve the evidence archive and its manifest as historical snapshots;
  this revision does not regenerate measurements or replace the packaged paper.

## Paragraph roles and reverse outline

The published manuscript omits drafting labels. The roles below identify
the purpose of each paragraph group in the revised text; the accompanying
topic-sentence outline records the paragraph-by-paragraph check.

| Section | Paragraph roles and logical progression |
|---|---|
| Abstract | Opening/challenge: equal range knowledge; evidence: original and two-array reversals; adverse evidence: sharing loses; mechanism: literal-one intervention; limitation: model-specific empirical contribution. |
| 1 | Opening: arithmetic fairness; challenge: representation confounds sharing; design: original four cells; design/chronology: prospective panel; contribution/limitation: three controlled empirical findings. |
| 2 | Background: width-aware DSP; background: FIR and physical-energy generation; controlled contrast: Hcub sharing; scope: established analysis and specialization tools. |
| 3.1 | Contract: inputs and outputs; semantics: one floor/saturation; legality: exact intervals and prefix certificates. |
| 3.2 | Design/legality: native partials; scope: fixed nonoptimal split; design: suffix recurrence; interpretation: what each contrast holds fixed. |
| 4.1 | Setup: target, compilers and measured region; definition: event/cycle model; definition: energy model; limitation: regression error and decimal precision. |
| 4.2 | Chronology: retrospective correction versus prospective work; criterion: all-four claim; evidence: different correctness checks. |
| 4.3 | Analysis: oriented event differences; design: RAM coefficient scaling; interpretation/limitation: exact algebra on an arbitrary interval. |
| 4.4 | Design: three arithmetic regimes; design: direct partitions; controls: six forms; workload: amplitudes and regions; accounting: condition versus identity; criterion: reversal predicate; secondary questions: all-form/compiler-selectable/clamp reports. |
| 4.5 | Intervention: literal one inside the callee; evidence/criterion: anchored controls, correctness and three success conditions. |
| 5.1 | Evidence: native partials improve every cell; mechanism: fewer operations can still cost more through RAM; interpretation: fixed versus selectable compiler. |
| 5.2 | Evidence: sharing trades arithmetic for transfers; interpretation: comparator changes effect size; resources: separate memory diagnostics. |
| 5.3 | Analysis: consistent partial benefit versus mixed Hcub benefit; boundary: only GCC15/block1 survives the selected stress against both controls. |
| 6.1 | Evidence: compiler traffic gap; mechanism: preparation for another output; accounting: checked paths reconcile RAM; limitation: additive decomposition is not a deletion counterfactual. |
| 6.2 | Evidence: anchored specialization reductions; outcome: signed compiler gap reverses; mechanism: identified preparation disappears; attribution/limitation: the whole specialization changes more than rotation. |
| 7.1 | Evidence: both wide arrays supply reversals; missing evidence: native library cases; example: nontransposed versus all-form minima; accounting: disjoint winners; interpretation: compiler-selectable decisions. |
| 7.2 | Evidence: direct partitions improve wide arithmetic; adverse evidence: sharing loses throughout both wide arrays. |
| 7.3 | Workload evidence: block/amplitude/region contrasts; coverage: source clamp counts; resources: linked image and live stack. |
| 8.1 | Interpretation: baseline choice and sharing are separate; mechanism: compiler-visible knowledge; scope: auditable empirical contribution. |
| 8.2 | Internal validity: finite candidates and layered checks; external validity: two wide arrays at one length; model limits: multiplier/configuration and no board measurements; adoption limits: distinct memory metrics. |
| 8.3 | Reproducibility: historical saved-evidence portability; limitation: rebuild, authenticity and physical validation remain separate. |
| 9 | Evidence/takeaway: three controlled findings; limitation/future work: wider arrays/lengths and physical validation. |
| Appendices | Diagnostic definitions and complete resource rows; evidence locations and explicit distinction between internal checks and external peer review. |

## Claim-evidence map

All statuses concern the stated finite model study. They do not imply
physical validation or an exhaustive optimization search.

| Major revised claim | Evidence | Status |
|---|---|---|
| Native partial sums meet the exact contract on all legal int16 inputs. | §3 intervals, prefix bounds, widening-before-add code; original arithmetic certificates. | Supported for the specified source arithmetic. |
| Partial direct reverses two original Hcub decisions. | §5.1, unchanged original cost and percentage tables; original saved result inventory. | Supported. |
| Partial direct is six-event-dominant over wide direct in all four original cells. | `../analysis/analysis.json`, four `partial_direct32x2`/`spec_direct` pairs and `event_dominance`. | Supported; resource/physical dominance excluded. |
| Two fresh wide arrays supply 24/32 fixed-compiler reversals. | §7.1; `../panel-summary.json`, `fixed_compiler_cells` and `compiler_pattern`. | Supported; existential extension, not prevalence. |
| Hcub loses to ordinary transposition in all 32 fresh wide conditions. | §7.2 unchanged range table and per-condition `hcub_vs_ordinary_percent` in `../panel-summary.json`. | Supported within the model; small margins are not physical certainty. |
| The full panel remains incomplete. | Eight native fast-CMSIS/block64 performance identities; two corresponding correctness identities. | Supported; missing cases excluded from win/loss counts. |
| Only original GCC15/block1 stays below both stronger controls over the arbitrary RAM stress. | §5.3 unchanged affine table and the 12 exact pairs in `../analysis/analysis.json`. | Supported for fixed events and the stated interval only. |
| Added SP-relative transfers account for about 85.02% of the original direct compiler cost increase. | §6.1 unchanged additive table; compiler-explanation accounting and separate path/value inspection. | Supported as additive accounting, not exclusive compiler causation. |
| Literal-one specialization lowers GCC15 modeled cost by 31.44% and reverses the direct compiler ranking. | §6.2 unchanged four-row intervention table; `../intervention-results.json`. | Supported for the matched block1 pair. |
| Identified preparation for another output disappears. | `../intervention-review.md`, actual general/specialized assembly inspection. | Supported by documented internal manual review; the whole saving has broader causes. |
| Costs require the stated multiplier/configuration assumptions. | Nikov model [5], verified official Arm DDI 0432C §§1.4.1/3.3 [11]. | Supported; one-cycle and 32-cycle multiplier options distinguished. |
| The archived snapshot passes saved-evidence relocation checks. | `../artifact-check.json`: seven successful commands, no target execution/integration skips. | Supported for the historical package; not a verification of newly edited paper bytes. |

## Five-dimension adversarial review

| Dimension | Reviewer question and answer | Disposition |
|---|---|---|
| Contribution | What is new? The controlled empirical boundary and matched compiled-code evidence. Width analysis, transposition, sharing, sensitivity and specialization are established. | Pass for the bounded claim; algorithmic novelty deliberately unclaimed. |
| Contribution | Does a predictable narrower accumulator improvement alone make a sufficient broad contribution? No. The paper's strongest evidence is the ranking change, negative sharing result and compiler intervention together. | Scope made explicit; stronger novelty requires further research. |
| Clarity | Can a reader identify the problem and controls without knowing the project's workflow? The opening defines the arithmetic and representation confounds; §3 and Figure 1 map each controlled contrast. | Pass after replacing workflow labels and strengthening topic sentences. |
| Clarity | Are “condition” and “identity” defined before the 32/288 counts? Yes, §4.4 distinguishes fixed workload/build conditions from implementations. | Pass. |
| Clarity | Are drafting labels and source-access logs left in the paper? No; paragraph roles and access limitations are in this companion. | Pass. |
| Experimental strength | Is improvement consistent against every strong control? No. Corrected direct and ordinary transposition change winners; sharing loses on both new wide arrays. | Pass: adverse outcomes retained. |
| Experimental strength | Do exact decimals or model MAPE establish physical pairwise accuracy? No. Prose is rounded for interpretation; §4.1/§8.2 retain model limitations. | Needs new experiment for physical claims; those claims excluded. |
| Evaluation completeness | Does 24/32 establish broad filter coverage? No: two new wide arrays, one tap length, paired deterministic conditions. | Needs new experiments for generality; abstract/discussion explicitly bounded. |
| Evaluation completeness | Are all baseline paths resolved? No: native fast-CMSIS/block64 remains unavailable under the frozen aliasing admission policy. | Missing evidence remains explicit, without counting a loss. |
| Evaluation completeness | Were direct cuts, schedules and Hcub seed optimized exhaustively? No. They are frozen controls. | Pass as finite study; no optimality or general selector claim. |
| Method soundness | Is arithmetic exactness being inferred from finite output agreement alone? No. Full-domain certificates, safe evaluation and distinct implementation checks remain. | Pass for the stated proof/check hierarchy. |
| Method soundness | Does specialization isolate only rotation removal? No. It changes copy/loop/control/register organization too. | Pass after retaining total-intervention attribution. |
| Method soundness | Are internal agent checks described as external peer review? No. Appendix B now distinguishes them explicitly. | Pass. |

The unresolved questions about physical accuracy, coverage and exhaustive
optimality cannot be removed by editing. The revision narrows claims rather
than implying that those experiments have happened.

## Editorial provenance and removed bookkeeping

- The installed skill's section guides informed the abstract, introduction,
  related work, methods, experiments and conclusion. Its ML-style templates
  were adapted to this empirical DSP study without manufacturing a novel
  method or hiding the baseline correction.
- The earlier source-access log remains in the prior branch's manuscript and
  the primary-source assessment. Fresh full-PDF retrieval of De Coster was
  unsuccessful; prior inspection/indexed primary excerpts do not establish
  unseen capabilities or an exhaustive priority search. The new text makes
  no stronger exclusion claim. The institutional SPIRAL PDF also timed out;
  the existing author-uploaded reference was retained.
- The old U1–U5 workflow labels, detailed archived-file inventory and repeated
  internal acceptance wording were removed from the narrative. The original
  records remain intact in the archive, progress log and prior branch.
- One official Arm timing reference was added after checking its instruction
  table and configurable multiplier documentation. Existing reference IDs
  1–10 are unchanged; Arm is reference 11.
- Appendices now precede references. Float placement respects LaTeX limits
  to prevent a crowded table page; the final bibliography is balanced across
  columns. Numerical table content and figure data are unchanged.

## Validation record

Final preservation checks, rendered-page review and source/output hashes are
recorded in `render-log.md` after the final render.

## Topic-sentence reverse outline

Each entry is the opening sentence of a prose paragraph. The roles above
map these sentences to the thesis and supporting evidence. Tables, figures,
equations and code are excluded from this prose outline.


### Abstract

1. Exact FIR comparisons depend on the arithmetic-range information supplied to each implementation.

### 1. Introduction

1. An exact FIR comparison should give each implementation access to the same arithmetic-range information.
2. Product sharing introduces a second distinction.
3. We examine these distinctions on a pinned Cortex-M0 simulator using a configuration-specific CPU energy model.
4. A prospectively frozen panel tests whether the baseline effect extends to fresh coefficient arrays.
5. The contribution is a controlled empirical account of three effects: arithmetic correction changes the direct/Hcub comparison; sharing loses to ordinary transposition on both fresh wide arrays; and fixed-block knowledge changes the direct compiler ranking.

### 2. Closest prior work

1. Range-aware DSP code generation is established.
2. FIR generation and energy-oriented implementation selection also precede this study.
3. Hcub provides established product-sharing graphs, rather than an executable energy objective.
4. The cost analysis and specialization use established tools.

### 3. Exact contract and controlled representations


### 3.1 Numeric semantics

1. All filters have 48 frozen signed-int16 coefficients, ordered so that $h[0]$ multiplies the newest sample.
2. Exactly one final quantization and saturation is permitted.
3. For each coefficient, exact independent-input product endpoints are $l_k=\min(-32768h_k,32767h_k)$ and $u_k=\max(-32768h_k,32767h_k)$.

### 3.2 The original arithmetic correction

1. The correction uses native partial sums without changing the direct history layout or coefficient order.
2. This split was fixed for the arithmetic-control experiment.
3. Ordinary transposition computes the current sum from $h[0]x+z_0^{old}$ and updates $z_i$ from $h[i+1]x+z_{i+1}^{old}$, ending with the last product.
4. The controls isolate different effects (Figure 1).

### 4. Measurement, chronology and prospective questions


### 4.1 Target and event models

1. The target is Cortex-M0 Thumb at `-O2`, separate compilation and no LTO.
2. Let $N_I$ include all instructions, $N_M$ native multiplication instructions, $B$ taken branches, $R$ and $W$ SRAM reads/writes, $F$ Flash data reads and $N_{BL}$ branch-with-link instructions.
3. Nikov et al.'s [5] 20 MHz, prefetch-off, zero-wait weights give modeled CPU energy in nJ:.
4. The reported 2.80% mean absolute percentage error (MAPE) describes aggregate validation of that model, not uncertainty in our pairwise margins.

### 4.2 Correctness checks and study chronology

1. The arithmetic correction is a retrospective control.
2. The original comparison uses a saved 257-sample `adc_raw` stream with zero initial history.
3. Correctness admission combines checks that address different failure modes.

### 4.3 Saved-event analysis

1. We use saved events to identify the work saved or added by each comparison.
2. A predeclared sensitivity check scales both RAM weights by $\lambda$ while holding the other four weights and all events fixed.
3. We examine the arbitrary interval $[0.5,2]$ to locate algebraic ranking boundaries.

### 4.4 Frozen synthetic panel

1. The fresh panel contains three synthetic 48-tap arrays chosen to span distinct arithmetic regimes: one full sum fits int32 and two require widening.
2. Two rules determine the wide designs' direct partitions.
3. Each array has six implementations.
4. Two paired inputs test amplitude, and two measured regions test stream conditions.
5. A condition fixes the array, compiler, block size, input amplitude and region; a performance identity additionally fixes the implementation.
6. The primary question is whether a stronger direct comparator reverses an old-control Hcub advantage.
7. Additional comparisons distinguish implementation choices from that reversal predicate.

### 4.5 Matched block-knowledge intervention

1. The intervention tests whether callee-visible block knowledge changes the original direct compiler comparison.
2. Historical comparability requires the general controls to reproduce the saved loadable binaries and events exactly.

### 5. Original comparison and event analysis


### 5.1 Width correction changes two decisions

1. Native partials lower modeled CPU energy by 23.44% to 41.98% relative to wide direct across the four original cells.
2. For GCC10/block64, partial direct executes 129,481 instructions and 2,827 MULs; Hcub executes only 116,139 instructions and 257 MULs.
3. Fixed versus selectable compiler decisions also differ.

### 5.2 Sharing saves arithmetic but adds RAM traffic

1. Within the same transposed equations, Hcub costs more at GCC10/block1 and less in the other three nominal cells.
2. The comparator changes the apparent size of the benefit.
3. Memory diagnostics expose a separate tradeoff.

### 5.3 Sensitivity to RAM weights

1. RAM reweighting separates a consistent arithmetic benefit from conditional sharing benefits.
2. Only GCC15/block1 keeps Hcub below both stronger controls throughout [0.5,2] (Figure 2).

### 6. Compiler account and intervention


### 6.1 Explaining the original block1 binaries

1. The original block1 compiler difference is largely a stack-traffic difference.
2. The binaries prepare differently for another output.
3. Checked paths reconcile the additional RAM traffic exactly.
4. Each extra transfer contributes an instruction and a RAM event.

### 6.2 Fixed-block specialization reverses the compiler ranking

1. Specialization lowers modeled cost by 8.86% for GCC10 and 31.44% for GCC15. Both general controls reproduce the historical loadable binaries and all ten counter fields exactly.
2. The signed compiler gap changes from about +70,470 to −11,857 nJ.
3. Emitted-code inspection also confirms removal of the identified preparation.
4. The full saving belongs to the block-knowledge intervention.

### 7. Results on the fresh synthetic panel


### 7.1 Stronger direct controls reverse Hcub comparisons

1. Both fresh wide arrays reproduce the baseline effect.
2. The full three-array panel remains incomplete.
3. For Wide2800/GCC10/block64/ADC/post-startup, Hcub costs 661.31 nJ/output, versus 904.01 for $D_{old}$ and 515.47 for $D_{new}$.
4. Across 40 complete fixed-compiler conditions, ordinary transposition wins 16, first direct alone eight, balanced direct alone four, Hcub four, and first/balanced direct tie in eight.
5. Allowing each form to choose its compiler changes the decision.

### 7.2 Sharing loses on both fresh wide arrays

1. Every admitted certified direct comparison improves on its wide counterpart, including the native-fit design.
2. Hcub costs 0.12% to 7.66% more than ordinary transposition in **all 32** fresh wide conditions.

### 7.3 Workload boundaries and admitted resources

1. Block64 lowers cost/output in all 136 known within-form block pairs, by 31.554538% to 55.482311%; eight pairs are unknown.
2. The source quantizer reaches neither clamp threshold on ADC inputs or the native full-range input.
3. All admitted executables respect the original memory limits.

### 8. Discussion and limits


### 8.1 What the comparisons establish

1. The central lesson is that the baseline and the comparison being isolated can change the interpretation of a nominal winner.
2. Compiler knowledge supplies a second mechanism.
3. These findings support an empirical case study using established techniques.

### 8.2 Internal and external validity

1. The evaluated implementations form a finite candidate set.
2. The fresh panel has limited design breadth: three synthetic arrays at one length, including only two widening-required arrays.
3. The results depend on the pinned simulator and cost configuration.
4. Memory costs remain separate from modeled energy.

### 8.3 Evidence portability and reproduction levels

1. Saved-evidence portability is distinct from a fresh target rebuild.
2. Rebuilding requires separately acquired pinned GCC10/GCC15, simulator and CMSIS/Hcub dependencies; executable toolchains are excluded from the archive.

### 9. Conclusion

1. Equalizing arithmetic-range information changes exact FIR implementation comparisons in this Cortex-M0 model case study.
2. The practical lesson is to examine arithmetic treatment, state representation and compiler-visible bounds together when interpreting an implementation comparison.

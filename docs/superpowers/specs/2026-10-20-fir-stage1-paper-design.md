# Stage 1 empirical FIR paper: scientific decision and artifact contract

20 October 2026. Decision owner: the explicitly requested Sol 6.1 reasoning
agent. Requested settings were accepted; independent backend routing telemetry
is unavailable. This document specifies writing and derived analysis of frozen
evidence, not a new target experiment. Stage 2 begins only after Stage 1 is
complete and accepted. Final paper artifacts belong in `research/fir-paper/`.

## Central question and hypothesis

The original question was whether established constant-product sharing improves
complete exact FIR execution after state width, register pressure and state
traffic are included. The correction asks whether the observed advantage survives
when direct arithmetic receives comparable range specialization. The paper must
retain this question rather than replace it with a theorem about elementary
integer bounds.

**Retrospective robustness assessment H_R:**

> For each of the four fixed compiler/block configurations—GCC 10.3.1 and
> GCC 15.2.Rel1, each with block sizes 1 and 64—demand-Hcub transposition retains
> lower complete-stream modeled CPU energy than direct accumulation when the
> direct comparator is replaced by the certified two-int32-partial implementation,
> for the frozen full-int16 `speech_minphase48` filter and saved 257-sample,
> zero-history input stream.

This is a falsifiable claim about four named executions. It is formulated after
their results were available. It is neither a preregistered prediction nor a
population statistical hypothesis, and no p-value or confirmation language is
appropriate. Describe its evaluation as a retrospective assessment. It supplies
an explicit standard for judging whether the earlier implementation decision
survives the missing control; it does not turn the existing data into held-out
validation.

There is an actual prior advantage to assess: Hcub beats both the earlier wide
specialized direct implementation (`spec_direct`) and the strongest historical
nontransposed energy comparator (`cmsis64_unroll`) in all four configurations.
Using unrounded saved totals, Hcub's energy relative to `spec_direct` is
−29.9145%, −38.9515%, −41.8582%, −45.0146%; relative to `cmsis64_unroll` it is
−29.6491%, −33.2602%, −33.7784%, −32.9372%, in GCC10/block1,
GCC10/block64, GCC15/block1, GCC15/block64 order. Thus H_R tests robustness of
a real observed four-case decision, rather than inventing an unspecified
universal claim solely to refute it. The wide specialized direct control is
the clean arithmetic-width comparison; CMSIS supplies the strongest earlier
nontransposed alternative. Name both roles instead of conflating them.

**Admission and decision rule:** first require each selected row's frozen
identity, numeric contract, compiler/block/input identity and inherited
correctness admission. An inadmissible or absent row makes the assessment
unavailable; it does not reject H_R. For admitted rows define
`r(c,b) = 100 * (E_Hcub(c,b) / E_partial(c,b) - 1)` from exact decimal
whole-stream modeled energies. H_R survives this finite-case assessment only
if `r(c,b) < 0` in every one of the four named cells. A tie does not meet
strict superiority. Any nonnegative cell rejects H_R. Report the four margins
and number of surviving cells regardless of the aggregate verdict. This is an
engineering dominance rule, not a significance threshold or uncertainty model.

**Decision: reject H_R.** The relative costs are +4.330785%, +5.002907%,
−24.056759%, −5.229188%. Two of four cells retain Hcub's lower modeled
energy. Corrected direct wins both GCC10 cells; Hcub wins both GCC15 cells.
Estimated-cycle winners agree. Do not write merely that “sharing sometimes
helps”: the substantive result is failure of the earlier all-four decision
under one controlled arithmetic correction, with a compiler-specific boundary
and an inspectable partial account of one compiler difference.

The compiler interaction is nontrivial empirical evidence because the same
numeric correction and exact source contract do not have a compiler-independent
effect on the winning form. Both direct binaries still use native partials and
the same final wide reduction. Arithmetic folklore predicts safety and reduced
width, but cannot derive their particular instruction mix, stack traffic,
whole-stream margins or the observed split. This establishes a useful local
case, not a new range-analysis technique or field-level optimization method.

## Evidence, chronology and strongest permissible claims

The manuscript must separate three phases explicitly. First, the original
`fir-sharing-probe/PROTOCOL.md` specified an exploratory sharing probe before
evaluating its generated kernels. Its review correction withdrew the scalar
state-traffic estimate's lower-bound status after grouped transfers were noticed;
no candidates were excluded by that estimate. Second, the subsequently fixed
`2026-10-20-fir-baseline-check.md` plan added precisely the missing partial-direct
control, with four performance rows and separate correctness tests. It was
motivated by inspection of earlier evidence, rather than an independent
confirmation study. Third, the two-block1-binary explanation and this H_R
assessment are post hoc analyses of the admitted rows. All occurred on the
recorded date; avoid implying elapsed independent study phases from date labels.

The bounds are 418,709,504 and 1,957,265,408 for fixed groups `[0,2)` and
`[2,48)`, while the full conservative bound is 2,375,974,912. Prefix/product
safety follows by triangle inequality. Convert both completed partials to
int64 before addition and apply one `sat_int16(floor(sum/32768))` quantizer.
Actual positive/negative aligned windows exceed int32. Finite output agreement
is separate evidence from this full-domain argument. The partial-direct control
is stronger than the previous control, not an optimal implementation or
exhaustive partition search.

For the two existing block1 direct binaries, manual call/path/value-flow review
supports extra direct-SP traffic of 13,878 reads and 19,275 writes, accounting
for all added RAM events and 59,909.909673 of the 70,469.699925 nJ modeled
energy increase (85.0151%). Retain the 10,559.790252 nJ residual and +10,667
instructions/+131 branches. Explain execution counts, not static sites alone:
257 calls execute 9/9 loads/stores per call with GCC10 and 63/84 with GCC15.
Show a sample slot's definition, use and rotation before the output-loop exit.
These are proved stack-resident history-sample lifetimes; “register-allocation
spills,” a responsible compiler pass, a compiler defect and the predicted saving
from deleting the accesses remain unsupported.

The complete stream includes calls, copying, convolution, quantization/store,
history movement and the final short call. Initialization/checking/printing
are outside. Models assume Cortex-M0 Thumb, `-O2`, no LTO, single-cycle MUL,
zero wait states, 20 MHz and prefetch off. Simulator ticks are not physical
cycles; event-weighted CPU energy is not measured board energy. The model
paper's 2.80% MAPE is not this study's pairwise uncertainty interval. The
selectable-compiler comparison yields only 3.967359%/2.302880% Hcub modeled
savings for blocks 1/64, respectively, and must be kept distinct from fixed
GCC15's 24.056759%/5.229188%. No physical winner follows.

## Manuscript and artifact design

Deliver `research/fir-paper/manuscript.md` plus an anonymous conventional PDF,
auditable `results.json`, `tables.md`, `source-manifest.json`, figures and
reproduction instructions. Main prose target is 4,000–5,500 words, excluding
references, table cells, captions, appendices and code. Word count is a size
check, not permission to pad the paper. A suitable title is *Does an Exact FIR
Sharing Advantage Survive a Stronger Direct Baseline? A Cortex-M0 Model Case
Study*.

Use connected manuscript argument with these conventional sections:

1. Abstract (~200 words): question, retrospective H_R assessment, two-of-four
   rejection, compiler split, partial explanation and model/single-case scope.
2. Introduction (~550): original decision problem, why comparison fairness
   matters, actual prior four-case advantage, exact H_R and contribution limits.
3. Closest work (~450): bit-true generation, FIR locality, embedded FIR/energy
   generation and Hcub graph objectives. Explicitly state established overlap.
4. Numeric contract and implementations (~650): equations, ranges, one final
   quantizer, candidate roles and distinct state layouts. Include the short
   partial/widen/reduce listing and candidate-definition table.
5. Method and chronology (~600): selected filter/workload, compiler/model/ROI,
   correctness/admission obligations, three evidence phases, H_R decision rule.
6. Results (~650): all 20 principal rows (five forms × four configurations) in
   compact tables or main-plus-appendix; explicit H_R table with prior/new
   margins and verdict. Discuss ordinary transposition as incremental-sharing
   control and compiler-selectable alternatives separately.
7. Generated-code explanation (~650): aggregate delta, execution-frequency
   proof, one assembly/value-flow example, explained-versus-residual table,
   limits of attribution. All evidence concerns only two block1 direct binaries.
8. Discussion/validity (~600): arithmetic validity versus finite-stream costs,
   filter selection and post hoc assessment, zero history and startup, compiler
   sensitivity, model/physical distinction, nonoptimal comparator, modest novelty.
9. Conclusion (~150): H_R rejected with the actual two-by-two outcome and
   what evidence can support, without an unsupported general selection rule.

Figure 1 should show Hcub relative energy with each prior comparator explicitly
labeled, then corrected direct, in four compiler/block cells; a zero line makes
the two reversals visible. Figure 2 can show GCC15-minus-GCC10 block1 direct
energy as attributed transfers plus residual, with the total denominator named.
Use standard static scientific plotting, deterministic labels/values and PDF
or SVG plus PNG as needed. No decorative plots or inferential error bars.

Appendices should contain the full range argument and signed examples, long
manifests, exact commands/archive restoration, data/table generation, selected
binary/source identities, full resource table, and explicit evidence status.
Frame bytes are compiler-reported `probe_process` frames, not peak stack; code
bytes are selected symbols plus coefficients, not total image size. Historical
12/24 bank statistics may be mentioned only with their old candidate set and
never as a revised fair-control bank result.

Use real primary references, especially De Coster et al. (1998), *Code Generation
for Compiled Bit-True Simulation of DSP Applications*, author-accessible
manuscript at https://cecs.uci.edu/~papers/compendium94-03/papers/1998/isss98/pdffiles/1_2.pdf;
Gačić, Püschel and Moura (2003), *Fast Automatic Software Implementations of FIR
Filters*, https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf; D'Alberto et al.
(2007), *Performance/Energy Optimization of DSP Transforms on the XScale
Processor*, https://users.ece.cmu.edu/~franzf/papers/hipeac07.pdf; Voronenko and
Püschel (2007), *Multiplierless Multiple Constant Multiplication*,
https://spiral.ece.cmu.edu/pubs/synth.pdf; and Nikov et al., *Accurate Energy
Modelling on the Cortex-M0 Processor for Profiling and Static Analysis*,
https://arxiv.org/html/2301.12806v1. Verify bibliographic details and source
passages before final citation. Inherited literature inspection is documented
in `explanation-check/claims.md`; this decision worker has not freshly read
those sources and does not upgrade access provenance. Official MathWorks
precision documentation and Doppler narrow-partial/wide-reduction documentation
may support context, with their documentation status/different semantics clear.
An access-limited source should never support a detailed equivalence claim.

## Minimal derived-analysis seam: exact Luna implementation contract

Implement `research/fir-paper/build_results.py --output-dir DIR` with optional
`--repo-root PATH` defaulting to this project root. Use Python standard library
for data/report generation. No compiler, simulator or target subprocess. The
public operation reads frozen inputs, validates them, selects rows, calculates
named metrics and writes `results.json`, `tables.md`, `source-manifest.json`.
Atomic output replacement after all validation prevents a failed input from
silently replacing valid paper reports. Figures/rendering can consume these
outputs separately. Keep internal helpers simple; no generic schema framework.

Freeze these byte identities in the implementation, with actionable mismatch
errors (paths are relative to repo root):

| Input | SHA256 |
|---|---|
| `research/fir-baseline/selection-design.json` | `bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f` |
| `research/fir-sharing-probe/results.json` | `57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa` |
| `research/fir-sharing-probe/partial-direct/results.json` | `eb53d3e556a6f8444742856b8c45a7d3236f443fed6cc0312010b2840095dc4f` |
| `research/fir-sharing-probe/independent-check/verification.json` | `e8ce76157aee913d05f16219117a5f3b0ed4aa1a08423a9acf8282095ab326c7` |
| `research/fir-sharing-probe/compiler-explanation/accounting.json` | `f39dc297271e4d706196690884a91b7eaedb414661230bd6e678a2bfc593aad2` |
| `research/fir-sharing-probe/explanation-check/verification.json` | `64e975a82a978254596e6aa2b16753527cf9bd9d78887a90777f74f337c26003` |

Parse JSON floats with `Decimal`; reconstruct canonical modeled energy from
the pinned six-decimal weights times integer event counts. Compare serialized
source/summary energy to this value with absolute tolerance <=0.000001 nJ,
solely to admit historical float serialization artifacts; this is not physical
or measurement uncertainty. Calculations use canonical whole-stream totals,
never rounded per-output display values. Historical/partial results supply raw events
and admitted verification supplies selected-symbol bytes/frame diagnostics.
Cross-check corresponding totals across sources; validate fixed filter,
maximum=32768, samples=257, exactly one row for each of five named variants
(`cmsis64_unroll`, `spec_direct`, `partial_direct32x2`, `trans_const`,
`trans_hcub_demand`) × two compilers × two blocks. Other historical variants
may exist; do not treat them as missing or include them silently. Select partial
rows from the peer array in the independent verification report. Confirm 257
verified outputs, history and guards in source result rows, four admitted peer
rows, and accounting's two binary identities against partial-direct rows.
Do not require literal complete-status strings: frozen automated results still
say assembly/manual review is pending. The subsequent `join-review.md` and
`explanation-check/final-decision.md` supply manual acceptance; preserve this
chronology rather than editing frozen status fields or treating them as failures.
The tool's checks reuse admitted summaries; it does not replace raw-evidence
admission or manual semantic review.

Public pure helper signatures are `build_report(documents: dict[str, dict]) ->
dict` and `assess_hypothesis(margins: Sequence[Decimal]) -> dict`. Document keys
are exactly `design`, `sharing`, `partial`, `verified`, `accounting`,
`explanation`. The assessment requires four finite Decimal margins in
gcc10/b1, gcc10/b64, gcc15/b1, gcc15/b64 order, returns
`{"status": "retained" | "rejected", "passes": [bool, bool, bool, bool]}`,
and raises `ValueError` for absent/nonfinite/wrong-count margins. Pure semantic
helpers never claim byte-identity admission; the CLI enforces hashes first.

The report top-level schema is `schema_version` (integer 1), `scope` (filter,
maximum, samples, row_order), `rows` (20 selected row objects), `comparisons`
(four ordered objects with compiler, block, and denominator-named percentages),
`hypothesis` (id, text, rule, status, passes), `selectable_compiler` (two block
objects), `explanation` (total, attributed, residual, attributed_fraction_percent),
and `limitations` (list of scope strings). `source-manifest.json` separately
contains the six repo-relative source paths and frozen SHA256 values. Additional
fields are allowed only if documented and no principal quantity is omitted.
Row objects use original field names where practical (`compiler`, `block`,
`variant`, `samples`, the eight event names, `arm_zero_ws_cycles`,
`estimated_cpu_energy_nj`, `cycles_per_output`, `energy_nj_per_output`,
`state_allocation_bytes`, `probe_process_stack_bytes`,
`kernel_and_coefficient_symbol_bytes`) and include source path and binary hash.
Comparison percentage keys must spell out both numerator and denominator,
for example `hcub_vs_partial_energy_percent`; negative means Hcub costs less.

Output must include: source hashes; exact selected row identifiers, events,
whole-stream energy/cycles, derived per-output values and diagnostic provenance;
three Hcub-relative comparator vectors; partial-versus-wide direct reduction;
ordinary-transposed-versus-partial and Hcub-versus-ordinary deltas; compiler
selectable minima; H_R text/rule/status and four cell outcomes; accepted
explanation totals/attribution/residual and denominator. Decimal quantities may
serialize as decimal strings; document representation. Display tables round to
two decimals while results retain sufficient exact precision. No wall-clock
timestamp or absolute directory should make identical inputs nondeterministic.

Minimum tests first, retained as actual red/green evidence:

1. Frozen successful CLI produces exactly 20 selected rows, prior all-four
   Hcub superiority, rejected H_R with [false,false,true,true], rounded margins
   [+4.33,+5.00,−24.06,−5.23], and exact explanation residual.
2. Copied fixture with changed frozen source bytes/identity rejects and leaves
   existing output sentinel intact. Cover both a modified identity field and
   a modified numeric total; byte freeze is the appropriate first rejection.
3. Direct pure selection/validation helper tests reject missing/duplicate
   requested row, incompatible samples/filter/range and conflicting cross-source
   totals. These semantic tests bypass the outer byte-freeze deliberately so
   the actual validation rules are exercised; do not add a public bypass flag.
4. A pure H_R evaluation helper verifies all-negative accepts, one positive
   rejects and an exact equality fails strict superiority. Missing rows are
   unavailable/error, never an apparent hypothesis rejection.
5. Independent Decimal expected-value assertions check at least one historical
   percentage, corrected percentage, selectable-compiler percentage and the
   attribution fraction, so self-consistent wrong denominators are caught.
6. Running valid generation twice yields byte-identical outputs.

Luna owns only mechanical implementation of this contract, tests, deterministic
plots and PDF rendering. It must not alter research hypotheses, invent results,
rewrite historical evidence or choose causal language. The reasoning owner
authors and defends the manuscript after the generated outputs are reviewed.

## Completion gate

Stage 1 is complete only when the substantive manuscript and anonymous PDF are
readable, every quantitative claim maps to generated or explicitly inherited
evidence, H_R is visibly evaluated/rejected, chronology and attribution limits
are honest, and the reproduction CLI/tests run successfully. Render every PDF
page and inspect layout, tables, equations, figure labels and bibliography.
Record actual checks and any remaining artifact access limitations. These
conditions are completion criteria, not predictions of publication or a grade.

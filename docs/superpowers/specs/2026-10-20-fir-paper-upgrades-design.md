# FIR paper upgrades: scientific gates and execution contract

20 October 2026. User authorized all five upgrades and a novelty/pursuit gate
for each, preserving the existing Sol 6.1 scientific/Luna 6 mechanical workflow.
Start: `8be6f32`, existing dedicated `research/fir-independent-check` branch.
The concrete prior proposal is `research/fir-paper-improvement-plan.md`.

## Goal and scope

Improve the empirical paper's claim, explanatory value, prospective boundary
evidence and independent reproducibility. The finished result is an updated
anonymous IEEEtran manuscript/TeX/PDF, auditable new analyses and experiments,
and a documented raw-evidence package. Publication/grade and field novelty
cannot be promised. FIR only, simulator only; no new optimizer or hardware claim.

The user has approved execution of this concrete upgrade program. Routine
reversible implementation choices and scientific gates do not need repeated
permission. Preserve the current dedicated branch and its pinned ignored tools;
no main edits, merge, push or external publication. Commit local checkpoints.

## Scientific authority and gate semantics

`research/fir-upgrade-gates.md`, owned by the Sol 6.1 research agent, supplies
the primary-source gate and exact scientific implementation contract. Its IDs
follow the saved improvement plan: U1 framing, U2 saved-event reanalysis,
U3 prospective boundary panel, U4 artifact portability, U5 mechanism intervention.

Each records proposed claim, closest-work overlap/access, incremental evidence,
falsifier, paper value and GO/NO-GO/GO-AS-SUPPORTING-WORK. Writing/reproducibility
need not be inventions to support a credible paper. U3/U5 require a specific
unanswered local question, equal arithmetic information, finite budget and
outcome-independent reporting. A no-go is a recorded decision, never a silently
omitted upgrade. Reassess claims against actual results at integration.

## Binding constraints

- Sol 6.1 (`gpt-6.1-sol`, high) owns scientific decisions, manuscript and reviews.
  Luna 6 (`gpt-6-luna`, low) implements explicit mechanical contracts with actual
  RED/GREEN evidence. Requested settings are recorded; routing telemetry unknown.
- Use clean task contexts, explicit ownership, no recursive delegation. One
  implementation task at a time; a research/review agent may run independently.
- Six frozen inputs in `research/fir-paper/source-manifest.json`, historical
  runners/protocols/results and old raw evidence remain byte-identical.
- New code/results live under `research/fir-upgrades/`; generated caches under
  its ignored `build/`. Do not invoke historical full-matrix CLIs.
- Full signed-int16 domain, exact integer products/sums, widening before any
  overflowing addition, one `clip_int16(floor(sum/32768))`. No intermediate wrap,
  rounding, dropping or saturation. Separate full-domain proof from finite tests.
- Both pinned GCC10/GCC15, Cortex-M0 Thumb, `-O2`, no LTO, original measurement
  marker correction, Arm-table zero-wait estimate, single-cycle MUL and published
  20 MHz/prefetch-OFF/zero-wait model. Raw ticks are diagnostics only.
- Existing inspected filters/results are development evidence. New panel is a
  controlled synthetic boundary experiment, not an application population.
- Scientific protocol/design/inputs/candidate rules are committed before new
  performance costs are observed. Retain failures, exclusions, ties and nulls.
- Tests exercise public numeric/admission behavior with independent expectations.
  No tests of prose wording or source substrings in lieu of behavior.

## U2: saved-event analysis

`analyze.py --output-dir DIR` admits the existing paper report through its six
frozen inputs without changing it. Use Decimal and exact whole-stream totals.
Twelve pairs: partial-minus-wide, Hcub-minus-ordinary and Hcub-minus-partial,
each GCC10/1, GCC10/64, GCC15/1, GCC15/64. Produce event vector
`(nonmul,mul,taken_branches,ram_reads,ram_writes,flash_reads)`, component energy,
total/cycle/resource differences, event-wise dominance, nominal percentages,
and RAM-coefficient affine stress `A+B*lambda` for lambda >=0, region [0.5,2].
Report exact tie/all-tie/no-nonnegative-tie cases and strict winner at .5/1/2;
stress is arbitrary model sensitivity, never calibrated physical uncertainty.
The gate appendix pins literal expected values and public helpers/tests.
Production outputs: `research/fir-upgrades/analysis/analysis.json` and
`analysis.md`; tests may use temporary output directories. Reject attempts to
overwrite the original paper directory. Preserve old output on invalid input.

## U3: controlled prospective panel

Pinned NumPy 1.26.4/SciPy 1.15.3. Three new nonsymmetric 48-tap minimum-phase
arrays: firwin95/fs16000/scaleTrue -> homomorphic half=True/n_fft32768 ->
gain normalization to the gate's target L1 -> np.rint/int64 -> int16 proof.
Recipes: native_lp1800 (1800,Hamming,50000), wide_lp2800 (2800,Hamming,100000),
wide_lp4600 (4600,Blackman,110000). Full native fit or legal overflow witnesses,
every group/product/prefix, suffix and graph intermediate must be certified.
No replacements after compiled costs. Preserve Hcub raw output/notices/invocation.

The gate fixes seeds/stimuli and first-legal/range-balanced cuts. At most six
forms/design: wide specialized direct, certified direct, ordinary transposed,
demand Hcub, standard unrolled CMSIS, plus balanced direct for wide designs or
admitted fast unrolled CMSIS for the native control. Deduplicate equal cuts.
All receive the same full-int16 contract; no folding baseline needed because
the declared family is nonsymmetric. No claim of optimal direct partitioning.

Compilers 2 x blocks {1,64} x stimuli {ADC,full-range} x regimes {startup,
post-startup}; cap 288 measured conditions. Startup:257 measured from zero.
Post-startup:64 unmeasured prefix+1025 measured, total1089; warm boundary block64
aligned, measured final tail1. Same reference includes the complete prefix.
Initialization/warmup/printing excluded; recurring stream/state/call/tail costs
included. RAM8KiB must accommodate buffers/state and documented stack reserve.

`panel.py prepare` writes literal designs/inputs/certificates, Hcub graphs and
`panel-protocol.json`/SHA256 before measurement; commit them. `measure` writes
new raw artifacts and results only, with exact compile commands/source/binary/
log hashes, state/guard/output admission and resource diagnostics. `verify`
reconstructs saved raw evidence independently of serialized cost summaries.
Use legacy pure helpers with explicit new paths; never mutate old source files.
Summaries distinguish input condition, filter, compiler and stream regime;
report fixed-compiler and selectable-compiler questions separately. A new
reversal uses the nontransposed set, not ordinary transposition: let
D_old=min(wide_direct64,CMSIS64_unroll[,eligible CMSISfast_native]) and
D_new=min(D_old,cert_direct_first,cert_direct_balanced). Reversal means
Hcub<D_old and Hcub>=D_new. The primary extension requires at least one cell
of the two genuinely wide-required fresh designs; no such cell falsifies it.
Ordinary transposition remains the incremental-sharing control and the all-form
winner is secondary. No reversal is a valid result. Short/long contrasts are
finite workload-regime comparisons, not isolated causal startup estimates.

## U4: portable evidence

Build a deterministic archive of the finite central evidence slice. Include the
24 historical rows required by the unchanged independent checker, four partial
rows, their 462 raw/dependency files (~3.3MB), explanation evidence and necessary
frozen sources/reports/certificates. Extend with admitted new experimental raw
evidence at final integration. No toolchain binaries or unrelated private files.
Manifest every contained regular file with relative path/size/hash; no traversal,
symlinks or special files. Hash/tamper/missing-file checks fail explicitly.

Fresh-copy verification must execute table generation, the unchanged baseline
checker (24+4), and explanation checker (2 rows/29 evidence hashes), without
the original checkout's ignored paths or target tools. Preserve existing outputs
by using separate report directories. Document additional requirements for new
target execution separately. Record actual passed/skipped levels honestly.

## U5: one narrow intervention

Only original partial-direct block1, two compilers, original257 samples. Rebuild
general and specialized copies (four measured conditions) with identical ABI,
header/wrapper/input/flags/linker/markers. In the specialized function body
replace runtime block-size uses by literal1 and preserve the parameter via
`(void)b`. Declared API precondition is b=1. No other source transformation.
General controls must reproduce original binary/event identities or trigger a
comparability investigation before causal interpretation. Independently check
outputs/history/guards, inspect actual assembly and reconcile event differences.
Do not call all saving removed-rotation saving or diagnose a compiler pass.
No new implementation-winner claim, flag search, waveform or representation.

## Paper integration and completion

Sol authors a stage copy under `research/fir-upgrades/paper/manuscript.md`, with
new TeX/PDF and local figures beside it. Original `fir-paper/manuscript.*` stay
byte-identical; navigation points to the revised paper and identifies the first
version. This resolves the gate's explicit stage-copy requirement.
Sol authors connected prose around three informative contrasts and new outcomes.
Retain retrospective H_R disclosure/decision/table once, exact denominator/model
limits, negative outcomes, source access and chronology. Add representation/
lifetime diagram, incremental sharing/event-cost table, sensitivity boundaries,
prospective panel and matched intervention results plus clear artifact levels.
Preserve IEEEtran, anonymous authors and editable source. Review new quantitative
claims against admitted outputs; real render/tests and every-page PNG QA are
mandatory. A fresh Sol review covers science, implementation/admission and
artifact completeness before final local commit. No new field-novelty claim
without the per-upgrade gate's specific evidence.

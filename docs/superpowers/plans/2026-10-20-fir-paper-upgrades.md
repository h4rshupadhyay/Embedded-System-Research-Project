# FIR Paper Upgrades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development task-by-task. Resume `research/fir-upgrades/PROGRESS.md`; do not repeat completed work. User has chosen Sol scientific/Luna mechanical execution.

**Goal:** Complete five novelty-gated empirical-paper upgrades and an independently reviewable IEEE artifact.
**Architecture:** Scientific gates freeze bounded contracts; new analysis and measurements remain separate from historical evidence. Mechanical tasks use RED/GREEN, then scientific review and final paper integration.
**Tech Stack:** Python/Decimal/unittest/pytest, NumPy1.26.4/SciPy1.15.3, host GCC/UBSan, pinned Arm GCC/ISS, Pandoc/Tectonic/Matplotlib/Poppler.
**Spec:** `docs/superpowers/specs/2026-10-20-fir-paper-upgrades-design.md`.

## Global Constraints

- Sol6.1 high scientific decisions/authoring/review; Luna6 low explicit mechanical implementation; clean owned contexts, no recursive delegation.
- Preserve six frozen inputs and historical source/results/raw bytes. New experiment code/data under `research/fir-upgrades/`, caches in ignored `build/`.
- Exact full-int16 arithmetic, widening before reduction and one final floor/saturation; proof separate from finite equality.
- Pinned GCC10/GCC15, Cortex-M0 Thumb,-O2,noLTO, original ROI accounting and model; no hardware claims.
- Commit fresh protocol/coefficients/inputs before target costs. At most288 panel and4 intervention measured conditions; no favorable-result replacements.
- Actual RED/GREEN for new numeric/admission behavior; scientific prose and visual layout get human-style review.
- Dedicated existing research branch; local commits only. User authorized execution, including bounded gates, without repeated permission questions.

## Review Focus

1. A mutually consistent wrong summary must still fail against raw events/frozen identity.
2. Equal/zero affine slopes and exact ties must not become apparent strict winners.
3. Warmup is excluded only from timing; reference/history include it and final tail costs remain.
4. Missing artifacts, path escape and integration skips cannot masquerade as reproducibility.
5. New synthetic filters or specialized b=1 contracts cannot silently acquire population/API/physical generality.

### Task 1: Scientific gates and frozen contract

**Files:** `research/fir-upgrade-gates.md`, spec, this plan, upgrade checkpoint.
**Interfaces:** produces primary-source per-upgrade decisions and the scientific appendix consumed by all tasks.
- [x] Sol evaluates five novelty/value gates and exact implementation contracts; root checks scope/arithmetic/target feasibility.
- [x] Record go/no-go/supporting decisions, source access and outcome-independent stopping rules. Commit docs locally before implementation; prose has no fake TDD.

### Task 2: Saved-event analysis through TDD

**Files:** new `research/fir-upgrades/analyze.py`, `test_analyze.py`, `analysis/analysis.json`, `analysis/analysis.md`, `tdd-log.md`.
**Interfaces:** consumes frozen paper report/scientific U2 contract; produces canonical Decimal12-pair analysis for manuscript/plots.
- [x] Read scientific gate's U2 appendix first. Write one independent expected-value/admission test, run to observed RED, implement minimum, run GREEN; repeat for affine ties/domain, identity/tamper and output preservation/determinism.
- [x] Public seam `analyze_report(report:dict)->dict`, `affine_boundary(a:Decimal,b:Decimal)->dict`; CLI `python3 research/fir-upgrades/analyze.py --output-dir DIR` validates frozen originals and outputs data/Markdown only after validation.
- [x] Check literal four incremental percentages and RAM affine constants, event-vector reconstruction and .5/1/2 strict outcomes. Semantic test permits isolated copied reports; production CLI has no identity bypass.
- [x] Run `python3 -m unittest discover -s research/fir-upgrades -p test_analyze.py -v` (all pass), run production CLI with `--output-dir research/fir-upgrades/analysis`, inspect outputs; commit owned files. Fresh Sol task review before downstream use.

### Task 3: Portable central raw-evidence package

**Files:** new `research/fir-upgrades/artifacts.py`, `test_artifacts.py`, `evidence.tar.gz`, `evidence-manifest.json`, `artifact-check.json`, `README.md`.
**Interfaces:** consumes historical JSON artifact maps/dependency/evidence manifests; produces portable checked archive and fresh-copy reports. No dependency on mutable new panel results yet.
- [x] Public `collect_files(repo:Path)->list[Path]`, `pack(repo:Path,output:Path)->dict`, `unpack_verified(archive:Path,destination:Path)->dict`; CLI subcommands `pack`/`check` document exact arguments.
- [x] `collect_files` returns sorted repository-relative paths. `pack` takes an output directory and writes `evidence.tar.gz` plus external `evidence-manifest.json`; embed the file manifest in the archive, excluding its own digest. CLI: `artifacts.py pack --repo-root ROOT --output-dir DIR`; `artifacts.py check --archive FILE --destination EMPTY_DIR --output-dir DIR`. Hashing is consistency checking, not proof of authenticity. Preserve prior outputs on missing-source/validation failure; tests use copies, never mutate originals.
- [x] RED/GREEN semantic tests: deterministic small archive, changed/missing bytes rejected, duplicate/escaping/link/special members rejected without writing outside destination. Use real temporary files, no mock-only assertions.
- [x] Pack existing finite raw slice plus explanation inputs; hash each regular path. Execute fresh-copy standard-library numerical export, unchanged historical+peer checker and explanation checker, writing reports in fresh-copy build only.
- [x] Expected actual admission: historical24, peer4, explanation2 with29 evidence hashes, no raw-check skips and exact exported original paper numbers. Record commands/file counts/digests, standalone-vs-target dependencies. Run scoped suite and commit; fresh reviewer independently exercises fresh-copy package.
- [x] Reports under `.superpowers/sdd/` are transient ignored files: write the task report there but never force-add or commit it. Stage only the named research deliverables. The package's checks must invoke copied scripts rooted in the fresh tree, with explicit copied roots and no source-checkout fallback.

### Task 4: Panel preparation and safe generated kernels

**Files:** new `research/fir-upgrades/panel.py`, `test_panel.py`, `panel-design.json`, `panel-protocol.json`, `panel-protocol.sha256`, `vendor/` graph outputs/manifest, `panel-tdd-log.md`.
**Interfaces:** consumes scientific U3 appendix, frozen original helpers/tool identities; produces literal admitted protocol and source generation, no new performance costs yet.
- [x] Shared case identity is `(filter,variant,compiler,block,stimulus,regime)`, with stimulus `adc/full`, regime `startup/post_startup`. Protocol rows carry `warmup_samples`, `measured_samples`, `total_samples`: `(0,257,257)` or `(64,1025,1089)`. Correctness verifies `total_samples`; cost normalization uses `measured_samples`. This schema is consumed unchanged by Task5.
- [x] Public `prepare_panel(output:Path)->dict`, `generate_kernel(h:list[int],variant:str,block:int,groups:list[tuple[int,int]])->tuple[str,str]`; exact names/definitions pinned by scientific appendix; use explicit paths for any legacy helper binding.
- [x] RED/GREEN independent tests: three recipe identities/L1/exact intervals, first/balanced legal cuts, real overflow witnesses, unsafe group rejection, coefficient order, single final quantizer, host arbitrary-precision agreement/retained state/guards under UBSan with sign windows/extrema/negative floor and mixed blocks.
- [x] Preserve original Hcub source/output notices; independently reconstruct graph algebra/exact divisions and certify all intermediates, state suffixes and wide reductions. Compiler/simulator paths are read-only prerequisites.
- [x] Host UBSan/mixed-block tests cover newly generated direct/transposed C. Unmodified CMSIS scalar library eligibility/source checks plus the declared two-compiler/two-block target correctness gate cover library forms; do not introduce an unreviewed host intrinsic replacement. Record this division of evidence.
- [x] Run scoped `test_panel.py` host suite, `panel.py prepare`, inspect scientific parameters/inputs/candidates, confirm zero target measurements. Commit protocol/hash/literal arrays and sources; Sol scientific review must pass before Task5.

### Task 5: Execute and independently admit bounded panel

**Files:** `panel.py`, new `panel_verify.py`, `test_panel_verify.py`, `panel-results.json`, `panel-summary.json`, `panel-summary.md`, raw `build/panel/`, verification log.
**Interfaces:** consumes committed Task4 protocol; outputs raw admitted rows/derived summaries used by final manuscript. Task3 package later incorporates these artifacts.
- [x] Preserve Task4 identity fields and sample triplets. Each admitted row records `outputs_verified=total_samples`; complete O:/H:/G:/M: traces include warmup outputs. Reference clamp-condition counts describe the source quantizer thresholds, not inferred per-kernel executed branch counts (CMSIS may lower saturation differently).
- [x] RED/GREEN tests of raw-event re-derivation, absent/duplicate configuration rejection, tampered firmware/input/ROI/warmup/guards/state and wrong serialized costs. Independent decoder/reference helpers may be reused read-only; no summary-only admission.
- [x] CLI `panel.py measure` rejects changed protocol/hash and records exact commands/paths/sources/binaries/events/resources. Short257 from zero; long64 warmup+1025measured. New ROI excludes prefix but all outputs/state checked; no historical paths overwritten.
- [x] Execute declared matrix once, at most288 rows including failures/exclusions. `panel_verify.py` independently audits every saved row and emits all estimands, fixed/selectable compiler comparisons and unfavorable outcomes. Check RAM reserve and instruction subset.
- [x] Run targeted suites/verification and inspect actual assembly for each new arithmetic form (not every repeated workload). Commit sources, results, evidence manifest and scientific outcome; fresh Sol task review.

### Task 6: Bounded block1 mechanism intervention

**Files:** new `research/fir-upgrades/intervention.py`, `test_intervention.py`, `intervention-results.json`, `intervention.md`, raw `build/intervention/`.
**Interfaces:** consumes scientific U5 contract and original partial kernel/wrapper; produces four matched rows, admission and bounded assembly interpretation.
- [x] RED/GREEN actual host behavior: b=1 specialized clone matches arbitrary-precision output/history/guards on signed windows, negative floor, zeros and long one-sample calls under UBSan. Document b=1 precondition without falsely preserving general-b semantics.
- [x] Clone original source and replace body uses of runtime b by literal1 with `(void)b`; retain ABI and all other sources/flags. Rebuild general/specialized with both compilers, original257input; four measured rows only.
- [x] General controls reproduce frozen binaries/events or stop comparability interpretation and diagnose. Independently audit all new raw outputs/events and compare code/frame/traffic. Sol reviews emitted code for intended loop/rotation change and any confound; preserve null results, no pass-cause or winner claim.
- [x] Run scoped tests/admission, record exact evidence and commit; scientific review before prose integration.

### Task 7: Updated paper, figures, artifact and final review

**Files:** new `research/fir-upgrades/paper/manuscript.md`, plot helper/assets, TeX/PDF/README/render-log, upgrade README/checkpoint; project navigation and proposal; upgraded evidence bundle/manifests. Original `research/fir-paper/manuscript.*` remain byte-identical.
**Interfaces:** consumes admitted Tasks2/3/5/6 and per-upgrade gate outcomes. No new experiment choice.
- [ ] Sol authors result-first revision: three contrasts, concise H_R chronology, incremental effects, arbitrary-cost sensitivity, controlled prospective outcomes, matched intervention and honest novelty/value verdicts. Add representation/lifetime diagram and justified tables/plots; no tests of prose wording.
- [ ] Luna renders figures and real IEEEtran PDF with existing tools; inspect every page PNG. Validate primary references/access and quantitative claims against admitted outputs; preserve editable Markdown/TeX.
- [ ] Extend evidence package with admitted new raw slice and portable verifiers; fresh reviewer runs original24+4+2 and new-panel/intervention verification from clean unpacked tree without original ignored paths. State rebuild dependencies honestly.
- [ ] Run relevant suites, production exports/raw verification, frozen-hash/link checks and every-page QA. Fresh Sol whole-change science/spec/code/artifact review; bounded fixes through RED/GREEN, final re-review, local completion commit and clean status.

## Resume contract

Read upgrade checkpoint and gate before dispatch. Scientific work remains Sol;
mechanical tasks receive this plan's extracted task brief plus exact scientific
appendix and report path. Reuse workers for bounded corrections. Record every
completion/check/commit and scientific ruling in checkpoint and plan-scoped
ledger. No completion claim based solely on a worker's report.

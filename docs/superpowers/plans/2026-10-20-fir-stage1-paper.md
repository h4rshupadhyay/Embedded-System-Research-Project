# FIR Stage 1 Paper Implementation Plan

> **For agentic workers:** Execute the user's authorized Sol 6.1/Luna 6 workflow. Resume from `research/fir-paper/PROGRESS.md`; completed tasks are not dispatched again. Use red/green TDD for new numerical tooling and human-style scientific review for the manuscript.

**Goal:** Finish a substantial, reproducible empirical paper with a defended,
falsifiable hypothesis, its actual verdict, and a readable PDF.

**Architecture:** Frozen experiment evidence feeds a small deterministic paper
exporter. A Sol 6.1 reasoning agent defines scientific claims and writes the
paper. Luna 6 executes explicit extraction, implementation and rendering tasks.
A fresh Sol 6.1 agent reviews scientific claims and numerical/tooling correctness.

**Tech Stack:** Python standard library, existing Matplotlib, IEEEtran/Pandoc/Tectonic for PDF,
existing frozen JSON/assembly evidence. No new target measurements.

**Spec:** `docs/superpowers/specs/2026-10-20-fir-stage1-paper-design.md`.

## Global constraints

- Stage 1 uses the completed outline and evidence, preserving exact coefficients,
  257 samples, full-int16 contract, GCC10/GCC15, blocks 1/64, `-O2`, no LTO.
- The central hypothesis is a retrospective finite-case robustness assessment:
  the prior Hcub modeled-energy advantage persists against equally specialized
  direct arithmetic in every one of the four fixed configurations.
- Test strict superiority in each configuration; equality is not superiority.
  Report every margin and the rejected all-four hypothesis. No p-values or
  population inference from deterministic repeated builds.
- Preserve chronology: exploratory sharing probe; subsequent fixed fairness
  check; post hoc assembly explanation; present manuscript formulation.
- Arithmetic safety, finite output checks, model predictions and physical claims
  are distinct. State the residual and unknown compiler pass.
- Sol 6.1 (`gpt-6.1-sol`, high) handles scientific decisions, authoring and review.
  Luna 6 (`gpt-6-luna`, low) receives complete mechanical task contracts.
  Record requested settings; runtime routing is unverified unless exposed.
- Each child gets a clean context and owned files. Maximum three active children with disjoint ownership;
  no recursive delegation. Reuse a worker for bounded corrections.
- User authorized executing stage 1 and then stage 2. Complete stage 1 first;
  stage 2's first task is the formulation/closest-work gate, not an assumed
  successful optimizer. Keep its work and claims separate.
- Author names, affiliation and course-specific formatting remain anonymous
  unless supplied. Default: IEEEtran conference two-column paper.

## Review focus

1. A hindsight hypothesis must not be described as preregistered or confirmed on
   unseen cases. Explain why robustness of the actual earlier advantage matters.
2. Compare original and corrected controls with the same compiler/block; name
   each percentage denominator and separate selectable-compiler comparisons.
3. Changed input identities, missing/duplicate rows and inconsistent numeric
   totals must fail export instead of silently entering tables.
4. Additional SP transfers explain 85.0151% of the GCC15-minus-GCC10 modeled
   energy increase, not an 85% optimization saving or a compiler-pass diagnosis.
5. Code tests establish exporter behavior. Scientific judgment and PDF legibility
   require separate review; word counts and section presence are not proof of
   research substance.

## Task 1: Scientific design and evidence inventory

- [x] Sol 6.1 chooses the exact hypothesis, rationale, chronology and verdict.
- [x] Luna 6 records the ten consumed source hashes in `source-manifest.json`.
- [x] Sol 6.1 writes the design with exact numerical-tool interfaces/tests.
- [x] Coordinator records implementation contracts and durable progress.

## Task 2: Derived results through TDD

**Files:** `research/fir-paper/build_results.py`, `test_build_results.py`,
`results.json`, `tables.md`, `tdd-log.md`.

**Public seam:** frozen result inputs to auditable paper tables and the finite
hypothesis verdict, using the design's exact interface. Default production input
paths are in the repo; a supplied fixture root permits isolated rejection tests.

- [x] One test -> observed RED -> minimal implementation -> observed GREEN per
  behavior. Use independently known literals; do not mirror the implementation.
  See `tdd-log.md` for the disclosed initial sequencing error and correction;
  this completion does not claim the initial full draft was test-first.
- [x] Check four earlier advantages and four corrected margins/verdict; reject
  changed identities, missing/duplicate configurations and inconsistent totals;
  equality fails strict superiority.
- [x] Generate actual production tables/results and inspect exact denominators.
- [x] Sol 6.1 reviews the numerical task against its contract.

## Task 3: Substantive manuscript and figures

**Files:** `manuscript.md`, `figures/`, `references.md` if needed.

- [x] Sol 6.1 writes a self-contained paper: abstract; problem and defended
  hypothesis; related work; arithmetic proof and implementations; reproducible
  protocol; complete results; code explanation; threats; conclusion; references
  and concise artifact appendix. Target 4,000-5,500 main-prose words as guidance,
  not a quality gate. Avoid padding or work-log narrative.
- [x] Include baseline-correction and SP-cost figures generated from saved data;
  tables must agree with the audited exporter. Add representative assembly.
- [x] Cite primary sources precisely; distinguish actual source access and scope.
  No invented novelty, bibliographic metadata or validation results.

## Task 4: PDF, independent review and completion

**Files:** `render_paper.py`, `manuscript.pdf`, `README.md`, `review.md`.

- [x] Luna 6 renders the finalized manuscript with readable fonts, equations,
  tables, figures, citations and page numbers; retain source and build command.
- [x] Render PDF pages to PNG and inspect every page for clipping, blank pages,
  missing glyphs, table overflow and figure legibility. Fix and repeat affected
  checks as needed. Keep intermediate renders ignored.
- [x] Fresh Sol 6.1 reviews scientific argument, hypothesis strength/chronology,
  evidence, references and derived numbers. Handle important findings and record
  their disposition. Final PDF must reflect reviewed text.
- [x] Run appropriate suites, production export, identity/link checks, and PDF
  extraction/visual checks. Record exact results, commit stage 1 locally and
  update project navigation/status.
- [x] Mark stage 1 complete only when substantive review and artifact QA pass.
  Then resume the separately bounded stage 2 formulation gate.

## Resume contract

Read `research/fir-paper/PROGRESS.md`, this plan and the spec. Inspect Git status
and existing artifacts. Resume the first incomplete task; a running child is
messaged rather than duplicated. Preserve recorded RED/GREEN evidence. Changes
to the hypothesis or evidence contract require a Sol 6.1 decision recorded in
progress, never an improvised Luna implementation choice. No push is implied.

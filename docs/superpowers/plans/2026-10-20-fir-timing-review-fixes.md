# FIR timing and manuscript review fixes

> Execute inline on `research/fir-clarity-rewrite`. User authorized the timing
> correction and the three remaining numbered suggestions from the review.

**Goal:** Correct current-paper timing from saved evidence and close the
generation-budget, missing-data and float-order findings.

**Spec:** `research/fir-upgrades/paper/manuscript-review-2026-10-20.md`, findings
1–3 and 5; the user's subsequent instruction authorizes implementation.
The renewed request to continue the suggested fixes also covers finding 4's
versioned compiler-semantics references and supplementary primary-source link.

**Architecture:** Preserve frozen v1 inventories, first-paper artifacts and
archive. A versioned `timing_correction.py` reads bound raw logs and emits
corrected timing for 20 original, 280 admitted panel and four intervention
rows, retaining legacy values and eight unavailable identities explicitly.
The current manuscript uses that report. No target execution is permitted.

**Stack:** Python standard library, existing pytest, Pandoc/Tectonic/Poppler.

## Review focus

- Missing/duplicate POP counters must fail closed.
- Corrected cycle claims must bind to the same measured raw events/binaries.
- An unsupported instruction cannot silently receive the scalar model cost.
- Energy, rankings, unavailable identities and frozen payloads must not change.
- Tables/figures must appear beside the section using them, without overflow.

## Tasks

1. **Corrected timing reanalysis** — create
   `research/fir-upgrades/timing_correction.py`, `test_timing_correction.py`
   and `timing/` report/README. First demonstrate the 15-versus-16 error at
   the legacy calculation seam; then test the new authoritative calculator
   with the same literal Arm-table fixture. Add saved-row regression,
   missing/duplicate-counter, binding and unsupported-instruction cases.
   Run the focused suite and the complete host research suite. The report
   must admit 304 timing rows, preserve eight unavailable panel cases, and
   reproduce every original energy total. Audit the scalar instruction subset;
   append one POP-PC cycle to the existing event expression.
2. **Paper fixes** — update formula and all affected cycle cells from the
   report; define fixed generation recipes and three-state missing-data logic.
   Use inline column tables for the small principal results and bounded float
   flushing at relevant section ends. Preserve author/arithmetic/energy data.
3. **Verification and delivery** — verify corrected report regeneration and
   hash preservation, render/inspect every PDF page, record reviewer closure
   and current hashes, obtain one fresh-context scientific/code review, fix
   actionable correctness gaps, and commit locally on the current branch.

## Progress

- Initial diagnosis already confirmed from cited Arm Table 3-1, raw logs and
  simulator source. The ranked-hypothesis phase is unnecessary: counter
  semantics and the omitted term are directly established.
- Ruling: use a separate versioned correction rather than mutate frozen
  calculators/inventories. Otherwise the admitted protocol/dependency hashes
  and historical reproduction contract would be silently changed. Cost: users
  of old scripts must follow the explicit supersession documentation.

## Completion, 20 October 2026

- Tasks 1–3 complete. Corrected report regenerates byte-for-byte and verifies
  from a relocated 920-file tree with `PATH=/nonexistent`: 304 timing identities,
  eight unavailable, no target tools. Energy totals and cycle orderings checked
  independently; all 24 changed manuscript cells match the correction.
- Full host research suite: 249 passed, zero skips, with the optional Tectonic
  integration enabled. The initial collection attempt needed this repository's
  explicit module paths and existing render-environment dependencies; the
  successful command is recorded in the paper render log.
- All 19 protected manuscript/numeric/protocol/archive/figure payload hashes
  from the preceding editorial validation remain unchanged. The historical
  archive remains a historical snapshot; the new report is delivered separately.
- Final PDF: 12 pages, all viewed at 1400-pixel page height; no overfull boxes,
  clipping or overlaps observed. Inline principal tables and section barriers
  keep evidence with its argument. Final reference-page balance changes only
  page 12 relative to the independently inspected preceding render.
- One independent fresh-context scientific/code review passes with no
  actionable Critical, Important or Minor findings. It independently checks all
  304 rows, all 24 cycle cells, official Arm/GCC sources and every PDF page.
  Its limits remain physical validity, target reproduction, comprehensive
  arithmetic/compiler correctness and publication suitability, none of which
  this saved-data correction establishes.
- Local commit on the existing branch is the delivery action; no integration
  or publication is included.

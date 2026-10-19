# FIR paper execution checkpoint

Plan: `docs/superpowers/plans/2026-10-20-fir-stage1-paper.md`.
Start commit: `c654960`; branch: `research/fir-independent-check`.
User authorized completion of stage 1, followed by stage 2, on 20 October 2026.

## Current state

Stage 1: **complete; committed locally as `6482810`**.
Stage 2: **bounded formulation gate complete; no-go for the current H1 rule**.
Current task: none within the completed paper/formulation gate. No optimizer implemented.

## Decisions

- Preserve the completed paper outline's bounded empirical scope. User approval
  to execute the paper and explicit model/TDD workflow covers routine reversible
  implementation choices; no repeated permission gate is needed.
- Central H_R: prior Hcub modeled-energy superiority persists against certified
  partial direct in all four frozen compiler/block configurations. This is a
  retrospectively formulated robustness assessment; reject it on any equality
  or higher Hcub cost, and report all four outcomes. Sol 6.1 verified the actual
  prior all-four superiority before recommending this assessment.
- Public test seam: frozen evidence -> exported paper numbers/hypothesis verdict.
  Tests check identity, selection, arithmetic and rejection, not prose novelty.
- User specified IEEE format: anonymous IEEEtran conference two-column paper/PDF;
  no venue/page limit was supplied. Main-prose target about 4,000-5,500 words, with substance judged by
  argument and evidence, not length.
- Model telemetry is not exposed. The coordinator makes no claim about its own
  backend; delegated scientific decisions/reviews request Sol 6.1 explicitly.

## Delegation

The following rows describe the previous session; their work is complete.

| Task | Agent | Requested settings | Owned output | Status |
|---|---|---|---|---|
| Scientific design | `/root/stage1_research_decisions` | `gpt-6.1-sol`, high, clean context | Stage 1 design spec | Complete; see design spec and review |
| Source identity inventory | `/root/stage1_source_manifest` | `gpt-6-luna`, low, clean context | `source-manifest.json` | Complete; 10 hashes independently read back |

## Completed checks

- Repository is on the existing dedicated research branch; no main/master edits.
- Existing numerical and causal evidence is complete; no new target run needed.
- Matplotlib and Poppler are installed. ReportLab/PDF extraction dependencies are
  absent from the default Python environment and will be isolated for rendering.
- Source manifest has ten existing input files and matching digests.

## Next actions

1. Use the completed Stage 1 manuscript and reproduction guide for the project.
2. Read `research/fir-stage2-formulation-gate.md` before reviving H1. Further
   method work needs a distinct structural rule and a useful, falsifiable
   search claim; the current no-go does not justify an implementation campaign.

## Recovery

After token exhaustion or compaction, read this file before dispatching work.
Check agent status and files; do not redo completed inventory or experiments.
Use the same worker for a bounded fix. Record each completion, check result and
commit here. Stage 2 is a separate research formulation gate; no optimizer is
implemented merely because stage 1 finishes.

## Execution update

- Scientific design complete and checkpointed by `e08b197`; exact public numerical
  interfaces and IEEE conference-format assumption are in the design spec.
- User specified IEEE format. Output will use the actual IEEEtran conference
  class, two columns, anonymous author block, editable LaTeX and PDF.
- Sol 6.1 now owns substantive manuscript authoring. Luna 6 owns numerical
  export through RED/GREEN cycles; its initial untested full draft was preserved
  privately and production reset to the tested helper after a sequencing error.
  Subsequent TDD evidence must reflect actual failures, not retroactive claims.
- Ruling: permit a third concurrent child for independent IEEE rendering only.
  Scientific manuscript, numerical exporter and format renderer have disjoint
  write ownership. This avoids blocking mechanical setup on scientific prose.
- Isolated tools: `/tmp/fir-paper-render-env` has ReportLab 5.0.1, pypdf 6.21.1,
  markdown-it-py 4.2.0 and pypandoc_binary 1.17 (Pandoc 3.9);
  `/tmp/fir-paper-tools/tectonic` is official Tectonic 0.17.0.
  Final IEEE rendering uses Pandoc/Tectonic rather than ReportLab.

## Task 2 numerical completion

Luna exporter and plots are complete after fresh Sol 6.1 review corrections.
Fourteen numerical tests pass; production CLI emits exactly 20 rows and H_R
passes `[false, false, true, true]`. Reviewer independently reconstructed all
20 energies/cycles and reproduced three original false admissions, then
confirmed their rejection after fixes. Diagnostic provenance and deterministic
PNG/SVG assets are present. See `tdd-log.md` for honest RED/GREEN history,
including the initial sequencing correction and shadowed-test-class defect.

Sol 6.1 authored the full manuscript (~4,100 main-prose words) and independently
reviewed science: central hypothesis is meaningful within its retrospective
finite-case scope; no substantive manuscript revision requested.

At the previous session's end, the remaining task was actual IEEE PDF render,
stable renderer tests, every-page visual QA and final checks/navigation/commit.
Requested independent reviewer: `/root/stage1_independent_review`,
`gpt-6.1-sol`, high, fresh context; review tracked in `review.md`.
Requested renderer: `/root/stage1_ieee_render`, `gpt-6-luna`, low, fresh context.
Its first integration compilation downloads Tectonic bundle; renderer fixes
include subtitle handling across blank lines and preserving reference links.

Runtime dependency note: plain `unittest discover` does not execute pytest-style
renderer tests. Run numeric unittest and renderer pytest commands separately.

## Resumed verification, 20 October 2026

- Read project navigation, historical handoffs, this checkpoint, the complete
  Stage 1 plan/spec, scientific review, manuscript and Stage 2 research plan.
  The peer baseline and compiler explanation are complete; do not restart them.
- Fresh numerical suite: 14 tests passed. Fresh renderer suite: two tests passed,
  neither skipped, with the recorded isolated Python/Tectonic tools.
- Regenerated numerical outputs into `/tmp/fir-paper-resume-results`; results,
  tables and six-source manifest match the delivered files byte-for-byte.
- Checked 75 local Markdown/image links across project navigation and paper
  notes: no missing targets.
- Rendered and inspected all nine original PDF pages. Tables, both figures,
  range argument, references and resource appendices are readable. Found one
  definite formatting defect: the question title has an extra colon before its
  subtitle. Long Appendix C archive commands initially looked clipped; subsequent
  PDF bounding-box inspection shows complete wrapped paths ending at x=556.38 pt,
  within the approximately 563.3 pt text edge. No archive-command fix is needed.
- Requested bounded mechanical corrections from `/root/stage1_render_finish`,
  `gpt-6-luna`, low, clean context; ownership restricted to renderer/tests,
  template/filter, render log and regenerated TeX/PDF. Scientific text and
  frozen evidence remain unchanged. Final every-page QA is recorded below.

### Additional numerical defect found during the resume audit

- Coordinator code inspection found a stale `h` variable in the second comparison
  loop. The exported Hcub-versus-ordinary percentages used GCC15/block64 Hcub
  energy in all four cells. Three JSON values were wrong; the last was already
  correct. Principal margins, H_R, figures, tables and manuscript statements were
  unaffected.
- `/root/stage1_incremental_fix`, requested `gpt-6-luna`, low, clean context,
  added an independent four-cell Decimal regression, observed its failure,
  selected the current cell's Hcub total and regenerated the report. See the
  appended RED/GREEN record in `tdd-log.md`.
- Fresh coordinator run: all 15 numerical tests pass. Only those three incremental
  percentages differ from the original draft JSON. Correct vector, in the fixed
  four-cell order: +3.410536%, -0.172202%, -4.284890%, -6.686823%. The manuscript's
  qualitative comparison and 6.69% GCC15/block64 saving agree with this correction.

## Stage 1 completion evidence

- Final renderer corrects question-title punctuation. The initially inherited
  PDF also preceded the source's equation-format update by 38 seconds; the new
  PDF now reflects the existing Markdown formulas as typeset mathematics.
  No manuscript content or scientific claim changed during this resume.
- The complete renderer initially hit a Tectonic SIGSEGV while scanning fonts
  inside the sandbox. Repeating the same build with approved external cache/font
  access succeeded. See `render-log.md` for exact commands and warnings.
- Final PDF: nine US-letter IEEEtran conference pages, anonymous authors,
  249,263 bytes. Coordinator rendered all nine pages with Poppler and inspected
  each image, including title/abstract, equations, all seven tables, both
  figures, assembly, five references, hashes and reproduction commands. No
  clipping, overlap, blank pages or missing glyphs were observed. Long paths
  wrap within the column; ordinary underfull-box warnings have no visible defect.
- Numerical tests: 15 passed; renderer tests: three passed, neither integration
  nor preservation skipped. Final numerical CLI succeeds; saved results, tables
  and six-source manifest match a separate fresh export byte-for-byte. Four
  regenerated plot files match saved PNG/SVG assets byte-for-byte.
- Combined final command with the recorded isolated Python/Tectonic environment:
  `python -m pytest research/fir-paper -q`: 18 passed. Generated Matplotlib SVG
  path-data spaces are preserved; `.gitattributes` exempts those two generated
  vectors from source whitespace checks rather than changing reproducible bytes.
- Independent scientific acceptance is in `review.md`; the later auxiliary
  exporter correction and its separate verification are disclosed there.
- Raw target reproduction was not repeated. The existing archive/ignored-build
  limitations remain documented in the reproduction guide. No push is implied.

## Stage 2 formulation gate

Started only after Stage 1's completed artifact/review/QA and local commit.
Requested reasoning owner `/root/stage2_formulation_gate`, `gpt-6.1-sol`, high,
clean context, owns only `research/fir-stage2-formulation-gate.md`. The task is
the four-step paper challenge in `fir-novelty-establishment-plan.md`: explicit
H1 formulation, at most three closest methods, a tiny fully specified symbolic
instance and a surviving claim/falsifier with a go/no-go or unresolved verdict.
Source access and mathematical verification must be recorded. No optimizer or
additional target measurement is part of this gate.

### Completed gate and checks

- Scientific owner delivered `research/fir-stage2-formulation-gate.md`, with a
  roughly one-page core, three-method comparison and analytic attachment.
  Fresh full-text passages were inspected for Ménard–Sentieys, SPIRAL FIR and
  Unison; alternative access, failed endpoints and inspection limits are explicit.
- No-go for implementing the present H1 state rule. In a specified abstract
  machine, two reachable equal-cost prefixes with the same tap/range/live-value
  key have minimum suffix costs K and K+mu because locations differ. This is
  a model-level counterexample, not a Cortex-M0 measurement, a universal
  impossibility result or a claim about every possible tie/pruning rule.
- Adding full suffix-relevant state permits ordinary dominance, without a new
  FIR-specific compression/search-efficiency result. Other structural hypotheses
  remain possible. Originality has not passed; utility and broader priority
  remain unresolved. No optimizer or additional target run followed.
- Author and coordinator separately checked all 64 toy input triples, every
  prefix of all six contiguous groups, exact widened sums/final quantization,
  signed extremes and negative-floor boundary, plus 13/14 symbolic instruction
  counts. Coordinator reviewed the minimum-continuation proof and scope limits;
  all five local note links resolve after excluding inline-code expressions.
- Stage 1 source/PDF and its scientific conclusions remain unchanged. Its local
  completion commit is `6482810`; the gate/navigation update is a separate commit.

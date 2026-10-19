# FIR paper execution checkpoint

Plan: `docs/superpowers/plans/2026-10-20-fir-stage1-paper.md`.
Start commit: `c654960`; branch: `research/fir-independent-check`.
User authorized completion of stage 1, followed by stage 2, on 20 October 2026.

## Current state

Stage 1: **in progress**. Stage 2: **queued after stage 1**.
Current task: scientific design and exact exporter contract.

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

| Task | Agent | Requested settings | Owned output | Status |
|---|---|---|---|---|
| Scientific design | `/root/stage1_research_decisions` | `gpt-6.1-sol`, high, clean context | Stage 1 design spec | Running; hypothesis recommendation received |
| Source identity inventory | `/root/stage1_source_manifest` | `gpt-6-luna`, low, clean context | `source-manifest.json` | Complete; 10 hashes independently read back |

## Completed checks

- Repository is on the existing dedicated research branch; no main/master edits.
- Existing numerical and causal evidence is complete; no new target run needed.
- Matplotlib and Poppler are installed. ReportLab/PDF extraction dependencies are
  absent from the default Python environment and will be isolated for rendering.
- Source manifest has ten existing input files and matching digests.

## Next actions

1. Receive spec and exact mechanical exporter contract from Sol 6.1.
2. Dispatch Luna 6 for sequential RED/GREEN numerical-tool slices.
3. Sol 6.1 authors paper while mechanical figure/render tasks proceed under
   separate file ownership; then fresh Sol 6.1 review and PDF QA.

## Recovery

After token exhaustion or compaction, read this file before dispatching work.
Check agent status and files; do not redo completed inventory or experiments.
Use the same worker for a bounded fix. Record each completion, check result and
commit here. Stage 2 is a separate research formulation gate; no optimizer is
implemented merely because stage 1 finishes.

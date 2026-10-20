# FIR upgrades execution checkpoint

Plan: `docs/superpowers/plans/2026-10-20-fir-paper-upgrades.md`.
Spec: `docs/superpowers/specs/2026-10-20-fir-paper-upgrades-design.md`.
Start commit `8be6f32`; branch `research/fir-independent-check`.
User authorized all five upgrades and per-upgrade novelty/pursuit gates.

## Current state

Tasks1-2 complete: gates/design `a5ba80b`; exact saved-event analysis through
`0f52a87`, approved after two scoped fix rounds. Root verified production export,
18-test first fix suite and >4300-digit finite root at caller precision6; worker's
final19 analyzer +15 exporter tests pass. Original four paper hashes unchanged.
Task3 complete at `2394cf4`; independent Astra spec/quality review approved. The package contains 531 files and passes 24 historical, four peer
and two explanation-row checks with 29 explanation hashes and zero skips.
Task4 preparation and independent scientific/code review complete after two
admission fix rounds. Task5 execution is complete pending fresh scientific/code
review. Remaining: Task5 review and Tasks6-7.

## Workflow and decisions

- Sol6.1 high scientific research/decisions/manuscript/review; Luna6 low explicit
  mechanical implementation with actual RED/GREEN tests. Routing telemetry not
  observable. No recursive delegation, one implementation task at a time.
- Earlier resume routing: Sol6.1 was absent and the user authorized Astra/high
  as fallback; Task4 review used that fallback. This continuation's allowlist
  includes `gpt-6.1-sol` again, so subsequent scientific authoring/review uses
  the preferred Sol6.1/high. Mechanical work remains `gpt-6-luna`, low.
  These are requested settings, not independently verified backend routing.
- Continue existing dedicated research branch to retain pinned ignored raw/tools;
  no main edit, merge, push or publication. Existing artifact hashes are binding.
- User's concrete five-upgrade authorization covers routine reversible execution
  decisions; do not repeatedly ask permission between tasks.
- Gate IDs follow saved improvement plan: U1 framing, U2 saved analysis, U3 fresh
  panel, U4 artifacts, U5 intervention. Supporting work can pass without a new
  method claim. New experiments require a bounded useful empirical contrast.
- Preliminary scientific choices from `/root/stage2_formulation_gate` recorded
  in spec; final primary-source gate/contract is `research/fir-upgrade-gates.md`.
  U1/U4 GO-as-supporting; U2 GO for reanalysis; U3/U5 GO only for the declared
  finite empirical questions. No algorithm-novelty or field-priority claim.
- Original paper baseline:18 tests passed in fresh run. NumPy1.26.4/SciPy1.15.3,
  exact GCC10/GCC15 and simulator available. Historical+partial raw slice:
  24+4 rows,462 raw/dependency files,3,314,263 bytes. No prior full grids rerun.
- RAM-safe prospective long condition:64 unmeasured+1025 measured samples;
  short257. No steady-state or application-population claim from synthetic48tap
  designs. Scientific recipes/candidates frozen before new performance costs.
- Root reviewed complete gate and reconciled interfaces. U2 production reports
  live in `analysis/`; revised manuscript/figures/TeX/PDF live in `paper/`, keeping
  the original paper files byte-identical. Archive462 count means combined raw
  artifacts plus10 dependency files, not462 separate source dependencies.
- Root independently reproduced all three coefficient hashes/intervals and the
  four specified wide-design cuts/group proofs, plus LCG prefix and both input
  hashes, directly from the pinned recipes. No target compilation/execution.

## Resume

Read this checkpoint, scientific gate and plan. Inspect Git history and live
agents; resume first unfinished task. Never regenerate historical input/results
or repeat already admitted measurements to seek a preferred outcome.

## Deferred review notes

- Task2 Minor: direct execution of test_analyze.py omits later class because
  unittest.main() precedes it; documented discovery command runs all19 tests.
- Initial Task2 CLI RED history was not independently verifiable; later real-file
  mutation/preservation tests and actual successful CLI are recorded honestly.

## Resume verification, 20 October 2026

- At `582a4c1`, all 19 saved-analysis tests passed and all six frozen source
  hashes matched. Original manuscript Markdown/TeX/PDF and results digests were
  saved in the ignored plan workspace for final preservation checks.
- Pinned NumPy 1.26.4/SciPy 1.15.3, both target compilers, simulator and Hcub
  executable remain available. Existing dedicated research checkout retained.
- Task3 worker: `/root/resume_portable_evidence`; read-only Task4 scientific
  preflight: `/root/panel_science_preflight`. Both were resumed after the user
  interruption; no replacement workers or duplicate measurements were started.

Task4 preflight: Astra permits preparation with explicit pinned-GCC integer
semantics for CMSIS helpers. A distinct fast-CMSIS block64 pointer-aliasing
question remains pending; unresolved cases must remain unavailable, never
counted as admitted through finite tests. Generated source proofs and host
sanitation checks remain separate from library/compiler-specific evidence.

## Continued Task4 acceptance, 20 October 2026

- Preparation was committed as `bf97665`; do not regenerate its three Hcub
  graphs or repeat completed preparation as a new experiment.
- Fresh coordinator verification: nine panel tests passed; 28 generated-C
  UBSan builds and 140 stream/state/guard checks passed. All ten preserved
  historical/paper hashes and 36 generated source-pair identities matched.
  The frozen protocol contains 288 unique cases and has SHA256
  `d2b85b2580ec551efcbc457159ff9237482aa2f146417ed236bbd0c0aeb8646c`.
- Independent Astra/high review confirmed the frozen arithmetic and graph
  identities, but requires three admission repairs: enforce public candidate
  eligibility/named cuts, reject missing recorded graphs without rerunning Hcub,
  and reject frozen dependency drift before preparation writes any output.
- Luna/low worker `/root/task4_admission_fixes` owns that validation-only fix
  round. Frozen arrays, protocol, graphs and generated sources must remain
  byte-identical. Task5 target work remains gated on accepted fixes.
- Requested model settings are recorded, with backend routing still unobservable.
- All three Important findings are addressed after two scoped fix rounds;
  Astra/high accepted the final preparation gate. Fresh coordinator checks:
  16 panel tests passed and all 95 frozen payload/historical hashes matched.
  No graph was regenerated and no target work occurred. Task5 may now proceed
  under its independent source/binary, correctness, memory and event gates.

## Task5 correctness and infrastructure checkpoint

- Task4 acceptance/admission fixes were committed as `22fe5cf`.
- `/root/task5_panel_execution` owns the new runner, independent saved-evidence
  verifier and tests. Root freshly ran 30 runner/verifier tests successfully
  before the subsequent shared-audit refactor. No performance cases have run.
- Initial correctness sweep recorded all 72 identities: 54 admitted, two
  unavailable fast-CMSIS block64 identities, and 16 stopped by admission-parser
  defects. Repair attempts remain separate and immutable; successful identities
  must be reused. Counts are an intermediate checkpoint, not final admission.
- Root independently audited native direct/GCC15/block1 attempt003: all 194
  outputs, 98-byte state, initial SP `0x20001ff0`, static RAM end `0x20000388`,
  and 688-byte maximum live stack chain. Earlier attempts preserve the ABI
  size-check and wrongly recorded multilib failures.
- Remaining closures include exact frozen source/command/macro/dependency
  identities, ELF/input/binary/disassembly binding, portable audit after
  relocation, and whole live stack chains. A GCC10 internal far branch was
  inspected and distinguished from recursion; no kernel optimization occurred.
- `/root/upgraded_manuscript`, requested Sol6.1/high, prepares only stable
  scientific prose in the new paper copy. New panel/intervention outcomes
  remain pending; original paper bytes stay unchanged.

## Task5 execution delivered for review

- All 288 frozen performance identities recorded: 280 admitted, eight native
  fast-CMSIS block64 unavailable, zero failed. Successful performance identities
  were not rerun; all 280 firmware binaries are distinct. Correctness remains
  70 admitted plus two declared skips. Failed mechanical correctness attempts
  are preserved separately.
- Root freshly ran all 42 runner/verifier tests successfully and the production
  independent performance audit (280/8/0). A separate calculation using the
  original strict decoder and literal integer model weights reconstructed every
  admitted raw event/cycle/energy/normalization and all 24 reversal witnesses
  among the 32 complete widening-required fixed-compiler cells.
- The finite wide-panel existential result has witnesses; the full-panel
  assessment stays incomplete because eight required native cases are missing.
  No missing candidate is assigned an infinite cost or counted as a loss.
- All 95 frozen panel/historical hashes remain unchanged. Maximum admitted
  static RAM end is `0x20001210`, maximum live stack is 688/2048 bytes, and
  vector SP remains `0x20001ff0`. These are simulator/build checks, not hardware
  SRAM high-water or physical energy measurements.
- Results, summaries, 70-gate and 280-row independent audits, raw-evidence
  manifest and honest TDD/repair chronology are under `research/fir-upgrades/`.
  Task5 requires fresh Sol6.1 scientific/spec/code review before acceptance.

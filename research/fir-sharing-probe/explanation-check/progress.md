# User explanation-check execution record

Plan: `docs/superpowers/plans/2026-10-20-fir-compiler-explanation.md`.
Started 20 October 2026 from `98d1b85` on `research/fir-independent-check`.

**Current status:** final join complete with accepted partial attribution; see
[final-decision.md](final-decision.md). The entries through “Final independent
milestone” below preserve the earlier pre-delivery state. The takeover record
at the end supersedes its pending status.

The user authorized continuing the USER assignment with its specified delegation.
Work stays in the existing research checkout and the owned `explanation-check/`
directory; the peer's directory and frozen evidence are read-only. No new worktree
or shared-file change is needed for this assignment's disjoint ownership.

## Work and routing

- Checker worker: `/root/explanation_checker`, requested `gpt-6-sol`, `high`,
  fresh context; implementation/tests/reports/fixtures only.
- Claim worker: `/root/explanation_claims`, requested `gpt-6-astra`, `high`,
  fresh context; `claims.md` and `paper-outline.md` only.
- Final reviewer: `/root/explanation_final_review`, requested `gpt-6-astra`,
  `high`, fresh read-only context after the two workers finished and outputs
  were integrated. One P2 event-ownership defect was independently reproduced
  and corrected by the original checker worker with RED/GREEN regressions.
- Maximum two concurrent children; no worker delegation. The spawn tool accepted
  both explicit model/effort requests. Independent backend routing telemetry is
  not exposed; recorded settings are the requested settings.
- Parent coordinator retains its existing session; its exact backend model is
  not independently reported by the available tools.

## Progress

- [x] Read the USER prompt, shared plan and existing checker interface.
- [x] Confirm the peer report is absent at assignment start.
- [x] Dispatch independent checker and claim work with separate write ownership.
- [x] Independently verify original input identities and aggregate deltas.
- [x] Receive the claim/evidence matrix and paper outline; their causal sections
  remain pending and literature-access claims are explicitly inherited.
- [x] Integrate the checker and claim files; run the new suite and pending CLI.
- [x] Obtain and handle the fresh final review; the P2 correction passes its
  regression tests and the final suites.
- [x] Record actual verification results and independent milestone.

The peer explanation and final causal decision remain pending until real peer
evidence arrives. Fixture success never certifies an unseen peer report.

## Coordinator source check

All 17 artifact hashes per block1 case matched (34 total). The existing
independent raw-histogram parser reconstructed the eight frozen counters for
both compilers. GCC15 minus GCC10 is: instructions 43,820; MUL 0; RAM reads
13,878; RAM writes 19,275; Flash reads/writes 0; taken branches 131; BL 0.
Reconstructed timing totals are 273,733/350,968, delta 77,235.

The CPU-energy model's 70,469.699925 nJ delta decomposes algebraically into
42,253.785560 nJ for additional instructions, 15,402.262374 for RAM reads,
12,539.601825 for RAM writes and 274.050166 for taken branches. This is cost-model
accounting, not a PC-level or compiler-cause attribution. Multiplication and
Flash-data count deltas are zero.

Recalculation also confirmed the selectable-compiler Hcub/direct reductions:
3.967359% at block1 and 2.302880% at block64. Their comparator is GCC15 Hcub
versus GCC10 partial direct; they do not replace within-compiler comparisons.

## Integrated verification before fresh review

All 15 new checker tests, 27 existing independent-check tests, three peer host
tests with nonrecovering UBSan, and ten baseline tests passed: 55 total. The
actual missing-peer command exited 0 with `status="pending"`, zero peer rows
checked and no peer-report hash. The worker records its additional post-edit
15/27 passing runs and RED/GREEN sequence in `implementation-report.md`.

The review package is an ignored snapshot under `build/review-package.diff`.
No new performance binary, compiler experiment or peer explanation was run.

## Final independent milestone

The review's event-ownership defect was fixed in the original worker, with five
incorrect-admission subcases observed before the change and passing rejection
checks afterward. The positive multi-register-transfer control still passes.
Final coordinator runs: 18 new + 27 existing independent-check + 3 peer UBSan +
10 baseline tests = **58 passing tests**. There are no open important findings;
the deliberate manual causal-review limit remains documented.

Our independent assignment is complete. `verification.json` and `comparison.md`
remain the actual missing-peer reports, not fixture certification. The peer
directory/report is still absent, so no `final-decision.md` is created yet.
Final join requires real peer evidence, successful numerical admission and manual
PC/source-value review. This record does not claim that final join is complete.

## Peer checkpoint takeover and completed join

The preceding pending statements describe the pre-delivery milestone and are
superseded here. The user supplied `partial-direct-baseline-delivery-2`; the
coordinator fetched and inspected peer tip `7315427`, then merged it by
`4a72620`. Only the peer's `compiler-explanation/` directory was added by that
checkpoint; frozen source/performance artifacts were preserved. The user
authorized taking over the unfinished delivery after the peer's quota ran out.

The actual report passes the independent checker: `status="consistent"`, two
rows admitted, report hash
`f39dc297271e4d706196690884a91b7eaedb414661230bd6e678a2bfc593aad2`,
29 evidence hashes checked. All 34 original case-artifact hashes match.
Regenerating the peer analyzer in a temporary output directory reproduced the
accounting and all 29 hashed files byte-for-byte. The tracked verification and
comparison reports now describe this actual delivery. Their manual-review flag
is deliberately automated-only; `final-decision.md` supplies partial acceptance.

The coordinator independently enumerated ten syntactic quantizer paths per
compiler, with block1 entry/copy/output branches fixed by the saved wrapper and
pointer bounds. All paths have identical direct-SP sequences: GCC10 9 loads/9
stores, GCC15 63/84. The zero-block-only store is excluded; history-copy loop
iterations add no direct-SP events. Manual partial-sum, sample-slot and ABI
review supports the bounded emitted-code account. Costs and residuals are
recorded in `final-decision.md`; no compiler-pass or universal spill claim is made.

### Takeover delegation and independent review

- `/root/peer_checkpoint_assembly_audit` was requested as `gpt-6-astra`, high,
  fresh read-only context. It returned a model usage-limit error before findings.
  It provides no independent review evidence.
- `/root/peer_checkpoint_sol_review` was requested as the permitted fallback
  `gpt-6-sol`, high, fresh read-only context. It independently checked hashes,
  binary bytes, saved outputs/history, counters, paths and value-flow claims,
  then reviewed the integrated final decision and claim documents. It found no
  substantive issue; its editorial request to distinguish historical pending
  text from current status was addressed in this record and `review.md`.
- No child edited files or delegated. At most two child task slots were used,
  including the failed Astra attempt. Requested settings were accepted; actual
  backend routing telemetry is unavailable. This substitution was disclosed.

### Final verification

Coordinator commands, all successful:

```bash
python3 -m unittest discover -s research/fir-sharing-probe/explanation-check -p 'test_*.py' -v
python3 -m unittest discover -s research/fir-sharing-probe/compiler-explanation -p 'test_*.py' -v
python3 -m unittest discover -s research/fir-sharing-probe/independent-check -p 'test_*.py' -v
FIR_UBSAN=1 python3 -m unittest discover -s research/fir-sharing-probe/partial-direct -p 'test_*.py' -v
python3 -m unittest discover -s research/fir-baseline -p 'test_*.py' -v
python3 research/fir-sharing-probe/explanation-check/verify.py --peer-report research/fir-sharing-probe/compiler-explanation/accounting.json --output-dir research/fir-sharing-probe/explanation-check
```

Counts: 18 + 6 + 27 + 3 + 10 = **64 passing tests**; actual-report CLI:
consistent, two rows. No code correction was needed for the peer checkpoint.
No new target build, simulator execution, performance row or literature
retrieval was performed. The proposal and paper outline now incorporate only
the accepted partial explanation. The bounded investigation is complete.

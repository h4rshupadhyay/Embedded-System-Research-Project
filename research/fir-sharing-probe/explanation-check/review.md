# Fresh final review and handling

**Current status:** this first review covers the independent checker before peer
delivery. The final takeover review is recorded below; its actual-report and
manual findings supersede the historical pending state in this first section.

20 October 2026. Reviewer `/root/explanation_final_review` was a fresh read-only
child, requested `gpt-6-astra` at `high` effort after both workers finished.
The tool accepted those requested settings; independent backend routing telemetry
was not exposed. The reviewer read the change package, actual code/tests,
shared contract, original evidence and claim/outline documents. It independently
checked the five fixed input hashes and 34 block1 artifacts and ran targeted
in-memory admission probes. It did not repeat the full suites, inspect nonexistent
peer evidence or perform a fresh literature search.

## Finding P2 — impossible component event ownership

Initial verdict: correction required before completion. Only the MUL count was
bounded by component instruction count. The reviewer moved one RAM write, taken
branch or BL into `stream_wrapper` while leaving that component's instruction
count zero and subtracting the same event from `unattributed`. With the existing
hashed fixture reference, all three reports were admitted despite impossible
instruction/event ownership. The coordinator reproduced all three independently.

This is a consistency defect, distinct from the manual question of whether a PC
label or stack-value explanation is true. The responsible original worker added
tests that reproduced it before the fix: zero instructions must imply zero
events, and taken-branch/BL counts cannot exceed owning instruction counts.
Multiple RAM transfers from a single PUSH/POP/LDM/STM-like instruction remain
valid; memory counts must not generally be bounded one-to-one by instructions.

The five rejection subcases failed before the fix. The corrected checker now
rejects zero-instruction components with events, and branch/BL counts exceeding
component instructions. A positive one-instruction/two-RAM-writes control passes.
The original worker observed RED then GREEN; the coordinator inspected the change
and reran all suites: 18 new, 27 existing independent-check, three peer UBSan and
ten baseline tests passed (58 total). The production command still reports pending,
zero peer rows checked. The P2 is closed by regression and suite verification;
no second independent review of the small correction was performed.

## Remaining review verdict

Otherwise, the reviewer found the specified USER workstream substantially
compliant and the implementation compact and inspectable. Numerical independence,
frozen identities, manifests, raw counters/costs, schema/count validation, component
sums, path containment and pending-versus-consistent reporting were verified.
The claim documents preserve comparator choices, unfavorable GCC10 outcomes,
inherited literature access, finite-stream/model limits and pending causation.
No important claim overreach or file-ownership violation was identified.

The suffix check on supporting evidence does not prove that arbitrary text is a
dynamic trace or a valid control-flow-frequency proof. This disclosed limitation
remains a manual join obligation. The automated result is numerical consistency,
never automatic trace-semantic or causal certification.

The production report remains **pending with zero peer rows checked**. Synthetic
fixtures were not promoted to actual peer measurements. The independent USER
milestone and the combined causal research decision are separate completion gates.

## Final post-delivery takeover review

The preceding pending/zero-row statements describe the historical pre-delivery
review. They are superseded by the actual production report: **consistent,
two peer rows checked, 29 evidence hashes verified**. Manual acceptance is
**partial**, as recorded in [final-decision.md](final-decision.md).

The coordinator first requested a fresh Astra assembly audit. That child stopped
at a model usage limit before returning findings, so it is not counted as a
review. The disclosed fallback was `/root/peer_checkpoint_sol_review`, requested
as `gpt-6-sol`, high effort, fresh read-only context, with no recursive delegation.
Independent backend routing telemetry is unavailable. This review is separate
from the peer checkpoint's inherited Astra review.

The fallback reviewer independently verified all 29 accounting evidence hashes,
both binary identities, saved counters and component sums, and every parsed
full-disassembly row against binary bytes (816 GCC10, 978 GCC15, including data
rows). A separately computed 48-tap reference matched all 257 outputs and 47
retained history values per compiler. It enumerated ten syntactic quantizer
paths in each body and found identical SP-access sequences across each body's
paths. The saved wrapper's 257 block1 calls and the exclusion of GCC10's
zero-block store support 9/9 versus 63/84 executed SP loads/stores per call.
The repeated history body has no direct-SP memory accesses.

It independently reconstructed the extra-transfer deltas: 13,878 reads, 19,275
writes, 33,153 instructions, 66,306 estimated cycles and 59,909.909673 modeled
nJ. Residual: 10,667 instructions, 131 branches, 10,929 estimated cycles and
10,559.790252 modeled nJ. It also reviewed the integrated final decision,
claims, outline, reports, root README and top proposal paragraph. Its verdict:
**no substantive numerical or causal overclaim found**. The 85.0151% energy-
increase fraction and compiler-pass uncertainty are consistent across them.

The sole editorial integration request was to make historical pending language
explicitly superseded. Current-status banners and this post-delivery section
address it. The generated automated reports retain `manual_causal_review=pending`
by contract, with the separate manual verdict explained in the README and final
decision. The reviewer agreed that distinction is accurate.

The coordinator ran all five suites after integration: **64 tests pass**, including
three nonrecovering UBSan host tests. The actual report CLI accepted both rows;
analyzer regeneration matched all hashed outputs byte-for-byte. The reviewer
did not claim a separate rerun of those suites. No substantive issue remains
open; the explicit residual and unknown compiler-pass cause are result limits,
not evidence of a complete causal explanation.

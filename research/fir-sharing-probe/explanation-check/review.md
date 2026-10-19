# Fresh final review and handling

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

# Final two-binary explanation decision

20 October 2026. **Numerical verdict: consistent. Manual attribution verdict:
partial, accepted within the bounds below.** The bounded compiler-explanation
assignment is complete. Continue with the empirical paper; no additional
benchmark or optimizer is needed to complete this investigation.

## Delivery and independent admission

The peer checkpoint `7315427` on `partial-direct-baseline-delivery-2` was merged
into `research/fir-independent-check` by `4a72620`. Despite its “Incomplete
Changes” commit title, it contains the analyzer, six tests, two-row accounting,
29 hashed evidence files, assembly notes, findings and its own review record.
The takeover assessed the actual artifacts rather than assuming completion from
that inherited review.

The admitted `compiler-explanation/accounting.json` SHA256 is
`f39dc297271e4d706196690884a91b7eaedb414661230bd6e678a2bfc593aad2`.
The independent checker accepts both rows, verifies all 29 evidence hashes and
reconstructs the original counters and costs using the existing independent raw
decoder, without importing the peer analyzer. All 34 original case-artifact
hashes match the frozen manifest. Regenerating the peer analyzer's output in a
temporary directory reproduces the accounting and every hashed evidence file
byte-for-byte. No new target compilation or simulator execution was performed.

The binary identities remain:

| Build | SHA256 |
|---|---|
| GCC10/block1 | `07fd7023d12ead52fee14a266c647627d664f37c18c234a0b41e2f226f143a6a` |
| GCC15/block1 | `114041b0f03a20c34a9c8a37b147116dff9f74c3c321bd2af4d7709d710e3470` |

See [verification.json](verification.json) and [comparison.md](comparison.md).
Their `manual_causal_review="pending"` field is deliberately the automated
checker's boundary; this document records the subsequent manual judgment.

## What the assembly supports

Both wrappers pass `b=1` on each of 257 calls. Copy-in and the output loop each
execute once per call; history copy executes 47 times. The zero-block path is
unreachable for this fixture. Every quantizer alternative joins before the
common output tail, and none contains a direct SP-relative memory access.
SP stays fixed between local allocation and deallocation.

The coordinator independently enumerated all ten syntactic quantizer paths in
each body from the saved disassembly, fixing the entry/copy/output branches to
their established block1 behavior. Every path has the same SP-access sequence.
The repeated history-copy body has no direct SP accesses. GCC10's store at
`0x08000406` is confined to the unused zero-block path and is excluded. Thus
the counts below follow from execution frequencies and paths, rather than
static-site counts alone.

| Direct SP-relative transfers | GCC10 | GCC15 | GCC15 minus GCC10 |
|---|---:|---:|---:|
| Loads per call | 9 | 63 | 54 |
| Stores per call | 9 | 84 | 75 |
| Loads across 257 calls | 2,313 | 16,191 | 13,878 |
| Stores across 257 calls | 2,313 | 21,588 | 19,275 |

These differences equal the **entire saved RAM-read/write delta**. Other RAM
work reconciles equally in both builds: per call, 48 history-sample reads for
convolution, one input read, 47 history-copy reads, and nine ABI restores; one
input write, one output write, 47 history-copy writes, and nine ABI saves. The
stream wrapper contributes six reads and six writes once. The GPIO closing
instruction is excluded consistently with the frozen decoder.

Manual value-flow inspection supports the narrower mechanism in
[assembly-notes.md](../compiler-explanation/assembly-notes.md): GCC15 keeps
history samples across possible output iterations, using many stack slots and
rotating those samples before testing the loop exit. Those rotations execute
even in the only output iteration of each block1 call. GCC10 loads most samples
near use and carries one into the next possible iteration. For example, GCC15
`[sp,#40]` holds `h_45`, is used at `0x0800016c/16e`, and is rotated at
`0x080004d4–0x080004de`; `[sp,#128]` holds `h_0`, used at `0x0800047a`,
then replaced by old `h_1` at `0x08000522/524`. These are identifiable
sample lifetimes and updates, not an inference from frame size.

Both bodies retain two native-width partials, sign-extend their completed
values and combine them with `ADDS/ADCS` before a single quantizer. Each has
four partial-interface stores and four reloads, eleven MULs per output and
nine saved/restored ABI words per call. Those shared features do not explain
the traffic increase. The 72/240-byte frame reports agree with the actual
36-byte register-save area plus 36/204 local bytes; allocating a larger frame
does not itself write all those bytes.

## Explained costs and residual

Each extra direct-SP LDR/STR contributes one instruction and one RAM event.
Applying the unchanged event-cost models yields:

| GCC15 minus GCC10 | Frozen total | Extra direct-SP transfers | Residual |
|---|---:|---:|---:|
| Instructions | 43,820 | 33,153 | 10,667 |
| RAM reads | 13,878 | 13,878 | 0 |
| RAM writes | 19,275 | 19,275 | 0 |
| Taken branches | 131 | 0 | 131 |
| Estimated cycles | 77,235 | 66,306 | 10,929 |
| Modeled CPU energy, nJ | 70,469.699925 | 59,909.909673 | 10,559.790252 |

MUL, flash-read/write and BL deltas are zero. Additional direct-SP transfers
account for **85.0151% of the modeled energy increase**, using the total
GCC15-minus-GCC10 increase as denominator. This is an additive event-model
explanation, not the predicted saving from deleting those instructions: an
alternative implementation could change other instructions and events.

The seven accounting components reconcile independently. Their labels describe
the attributed subset (MULs and proved direct-SP accesses), not exhaustive
costs of source phases. Many non-SP events remain `unattributed` in each row;
zero counts in another component do not mean that work is absent. The residual
above is the difference of the remaining costs, not a complete PC attribution.

The exact compiler pass and reason for stack placement remain unproved. Do not
call all accesses register-allocation spills, claim a compiler bug or infer
the causal effect of frame size. No optimization-pass dump or diagnostic
counterfactual build was collected. Aggregate event logs are not per-PC traces.

## Research decision and review

The stronger direct baseline still wins both GCC10 comparisons; Hcub wins both
GCC15 comparisons. The explanation adds inspectable evidence about generated
sample lifetimes and stack traffic for these two block1 binaries. It does not
establish a new FIR algorithm, substantial field novelty, a general compiler
ranking or physical energy savings. Keep the corrected comparator percentages
and finite-stream/model limits in [claims.md](claims.md).

A fresh Astra audit was attempted but stopped at the model's usage limit before
returning findings. The fallback reviewer was requested as `gpt-6-sol`, high
effort, with a fresh read-only context and no delegation. Requested model/effort
settings were accepted; independent backend routing telemetry is unavailable.
Its independent binary/control-flow checks and integrated-document verdict are
recorded in [review.md](review.md), separately from the inherited peer review.

Final coordinator verification passed all 64 tests (18 independent explanation,
6 peer analyzer, 27 existing checker, 3 UBSan host and 10 baseline tests).
The actual-report CLI returned `consistent` with two admitted rows. The fresh
fallback review found no substantive numerical or causal overclaim; its request
to mark historical pending language as superseded was addressed.

The next scoped task is writing the paper from [paper-outline.md](paper-outline.md),
including this partial explanation and its residual. The bounded investigation
stops here; no further performance experiment is implied.

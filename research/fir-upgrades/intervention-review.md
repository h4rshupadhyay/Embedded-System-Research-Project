# Independent bounded intervention review

20 October 2026. Review of the actual Task 6 sources, eight saved attempts,
raw traces, ELF/binary/disassembly, and comparison reducer against scientific U5.
No new target compilation or simulation was performed. The 39 scoped tests
pass; `python3 research/fir-upgrades/intervention.py --verify` independently
admits four performance and four correctness rows locally, with
`toolchains_executed: false`. Each scientific identity has one attempt directory.

**Scientific ruling: the stronger bounded conjunction is supported by manual
code inspection and the admitted numerical results. Artifact/code acceptance
passes after the two scoped repair rounds recorded below.** The reducer's machine-readable
preparation-removal field correctly remains pending manual review; this document
is the separate manual ruling, not an automated proof or a change to raw data.

## Matched evidence and outcomes

The general kernels reproduce the frozen source. Specialization changes only
the three body uses of `b` to literal `1`, adding `(void)b;`, under the explicit
precondition `b=1`. Header, wrapper, input, startup/linker, separate translation
units, compile/link order, `-DBLOCK=1`, `-O2`, and no-LTO contract are retained.
Both general performance binaries match the frozen loadable binaries exactly
(`07fd7023…143a6a` for GCC10, `114041b0…e3470` for GCC15), as do all ten corrected
event counters. Every performance output (257), edge output (361), final history
(47 words), guard record and 98-byte state allocation admits independently.
The host test covers signed windows, negative floor boundaries, zeros and long
repeated one-sample calls under UBSan, including history after every call.

| Compiler/condition | Energy (nJ) | Energy/output (nJ, rounded) | Arm model cycles | Process symbol bytes | Process frame bytes | Whole stack peak bytes | Flash load bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| GCC10 general | 266394.093850 | 1036.552894 | 273733 | 1036 | 72 | 144 | 2166 |
| GCC10 literal-1 | 242800.957748 | 944.750808 | 248804 | 888 | 20 | 92 | 2018 |
| GCC15 general | 336863.793775 | 1310.754061 | 350968 | 1372 | 240 | 312 | 2490 |
| GCC15 literal-1 | 230943.514627 | 898.612897 | 236467 | 884 | 16 | 88 | 2002 |

Process symbol sizes include their literal pools. Frames agree between actual
prologues and `.su` diagnostics; whole-stack peaks use the conservative
`main → measured → process_stream → probe_process` chain. Static RAM remains
1160 bytes, state 98 bytes, and initial SP `0x20001ff0` in all four conditions.
The four edge conditions are correctness-only, not additional performance claims.

| Corrected counter, general minus specialized | GCC10 | GCC15 |
|---|---:|---:|
| Instructions | 17219 | 72605 |
| Flash instruction fetches | 17219 | 72605 |
| RAM reads | 3855 | 17733 |
| RAM writes | 3341 | 22873 |
| Taken branches | 257 | 645 |
| MUL | 0 | 0 |
| BL | 0 | 0 |
| Flash data reads | 0 | 0 |
| Flash writes | 0 | 0 |
| Raw tick delta | 23901 | 112828 |
| Arm model cycles | 24929 | 114501 |

The exact energy reductions reconcile with the complete event vectors:

| Energy contribution (nJ), general minus specialized | GCC10 | GCC15 |
|---|---:|---:|
| Non-MUL instructions | 16603.558502 | 70009.952090 |
| Taken branches | 537.640402 | 1349.330970 |
| RAM reads | 4278.406215 | 19680.668589 |
| RAM writes | 2173.530983 | 14880.327499 |
| MUL and Flash data reads | 0 | 0 |
| Total | 23593.136102 | 105920.279148 |

`G_general = 70469.699925 nJ`, `G_specialized = -11857.443121 nJ`, and
`G_general − G_specialized = 82327.143046 nJ`. Thus GCC15 specialized costs
less than GCC15 general, and the signed compiler gap contracts and crosses zero.
This is the declared gap definition, not a new implementation ranking.

## Actual preparation-removal inspection

The inspected files are `build/intervention/performance-{gcc10,gcc15}-
{general,specialized}/attempt-001/firmware.disasm`, with linked machine bytes
bound to each ELF and binary by the saved verifier.

**GCC15: identified preparation removed.** The general function's initial
36-sample preload/stack-staging region at `0x0800004c–0x0800011c` and its
loop-carried register/stack sample window are absent in the specialization.
The general output/rotation tail `0x080004c6–0x08000530` performs sample
rotations before testing whether another output remains: for example old
`h45` at `[sp,#40]` moves to `ip`, old `h46` replaces that slot, and old `h1`
replaces `[sp,#128]` for a potential next `h0`. The literal-1 function has
no corresponding tail or output-loop backedge and no SP-relative local
load/store instructions. It loads history near arithmetic use, stores the
single output at `0x08000358`, and performs the required history shift at
`0x0800035c–0x08000364`. Necessary sample loads remain: removal of the
preload organization does not mean those input values cease to be read.

**GCC10: its smaller next-output recurrence also disappears.** The general
function seeds `r8=h0` at `0x08000058–0x0800005e`, uses it for the final
coefficient, and sets `r8=h1` at `0x08000352/0x08000358` for a possible next
output. The output-loop pointer/test/backedge at `0x080003b4–0x080003c2`
disappears in literal-1. The specialized function instead uses `h1` directly
near `0x08000308` and retains it to seed the first required history store;
the subsequent history loop is `0x0800035c–0x08000366`. That retained copy
work is required state maintenance, not surviving next-output preparation.

Other emitted changes prevent exclusive attribution to those preparations.
Both runtime copy-in loops become a single load/store and both output loops
lose runtime setup and exit bookkeeping. General high-register saves/restores
and 36/204-byte local allocations disappear: specialized prologues save
20/16 bytes respectively. General stack-materialized accumulator pairs become
register pairs. Arithmetic scheduling, register moves and quantizer branches
also differ; GCC10 retains an `sxth` on one quantizer path whereas GCC15 does
not. The 47-element history-copy algorithm remains, with changed addressing
and in GCC10 reuse of the first copied value. Aggregate MUL and Flash data-read
counts stay fixed while instruction, branch and RAM counts fall.

These observations plus the two strict numerical predicates satisfy U5's
stronger conjunction. The total modeled saving belongs to the complete
block-knowledge intervention. The event reconciliation above is by event
category, not a dynamic attribution of every saved instruction/transfer to
one source-value subset. It does not transfer the historical 85.02% fraction,
identify a compiler pass, establish GCC optimality, rank other FIR forms, or
support block64 or physical-energy claims. Frame shrinkage alone is not
traffic evidence; the actual raw event reductions supply the traffic result.

## Artifact acceptance and review history

Scoped repair round 2: **spec and code quality accepted for the bounded Task 6
artifact**. All 50 scoped tests pass. Local and no-target-tools-on-PATH saved
verification admit all eight unchanged rows; the actual complete-package
relocation regression also passes. Both frozen compiler headers are now
independently admitted before each present row is compared to its header, so
the actual one-general-control prefix checkpoint verifies successfully. After
failed evidence recovery, the common recovery/compile seam blocks prior raw
execution evidence even when an invalid `evidence.json` exists; its regression
uses a copied actual specialized row with altered saved cost and confirms zero
compile callbacks. The earlier receipt-bearing post-simulation size failure
remains fail-closed. All three original Important findings and both round-1
residuals are resolved. No new Critical/Important finding arose from these
scoped changes. No target compilation/simulation, new condition, raw/cost change
or adjustment to the manual scientific ruling was needed for acceptance.

Historical scoped repair round 1: **artifact/code acceptance remained changes required**.
All 48 scoped tests pass, local eight-row admission passes, and the actual
complete eight-row tree now verifies after relocation with no target tools.
The path failure in item 1 is resolved: only validated stack diagnostic file
and source path prefixes are normalized, retaining semantic frame/chain/byte
checks. The copied metadata mutations in item 3 now reject. However, its new
toolchain-header check rejects a legitimate one-control checkpoint because it
requires both compiler identities to appear in the row subset. Item 2's new
pre-simulation intent/completion receipt blocks the mocked size-failure case,
but existing unreceipted raw evidence with an inadmissible `evidence.json` is
still skipped by recovery and passes the repeat-compilation guard. Bind both
frozen toolchain headers independently of a partial row inventory and block
new execution after recovery fails whenever prior intent/raw exists. These
are infrastructure limitations; the manual scientific ruling above is unchanged.

The following numbered findings preserve the initial review and reproductions.
The initial ruling was that local numerical admission was sound but artifact
release required these fixes, without new target runs:

1. **Important: actual evidence relocation fails.** Copying the complete
   actual campaign and its required source/helpers to a fresh project under
   `/tmp`, then executing the copied `intervention.py --verify` with
   `PATH=/nonexistent`, fails at the saved stack comparison. Reconstructed
   `stack.frames[].file` paths contain the new prefix while serialized paths
   contain the old checkout. Normalize only validated diagnostic path prefixes;
   preserve frame/function/kind/byte/chain/resource equality and add a real-row
   relocation regression. Historical fixture rows constructed at the final
   test location do not exercise this case.
2. **Important: a completed execution can become eligible for rerun.** A
   mocked size-diagnostic failure immediately after successful simulation leaves
   raw stdout/stderr but no `commands.json` or `evidence.json`. Recovery searches
   only `attempt-*/evidence.json`, returns no match, and permits another attempt
   for that scientific identity. Persist command/execution receipts before
   downstream diagnostics and either reconstruct completed attempts without
   target execution or stop on executed-but-incomplete evidence. Preserve
   failures and prevent automatic reruns. The existing test interrupts after
   final attempt evidence exists, leaving this earlier interval untested.
3. **Important: several published summaries bypass binding.** With raw data
   untouched, changing top-level `historical_anchor.G_general_nj` to `"0"`
   still passes `verify_saved`; changing a row's `.text` size to `1` also passes.
   Core row events/costs, stack/memory and `comparisons` are correctly rederived,
   but duplicated historical-anchor and resource/source summaries must be
   independently compared or explicitly removed from admitted output. Add
   finite mutations for those existing fields; no broader framework is needed.

The implementation log explicitly distinguishes retrospective regressions from
later RED/GREEN evidence. The passing tests do not establish an earlier
test-first history. No critical scientific defect or altered raw measurement
was found. Acceptance of the fixes used scoped host/mutation tests and
tool-free saved verification, including a relocated actual complete tree;
the eight-condition target budget is closed.

# Task 6 implementation log

The interrupted source and test files were retained and reviewed against the
Task 6 brief and integration seam. The prior interrupted execution history is
not available as verifiable evidence, so no earlier RED/GREEN claims are
carried forward.

## Host behavior

The host harness runs both the frozen general kernel and the exact literal-1
specialization. Each stream is partitioned into repeated one-sample calls and
checked under UBSan against Python integer convolution with floor division,
retained history after every call, surrounding guards, and the fixed 98-byte
state allocation. Inputs include signed extrema, zero runs, negative floor
boundaries, and long repeated calls. The specialization has the explicit
precondition `b == 1`; this does not establish correctness for general `b`.

Scoped verification before target runs reported **39 passed** with
`python3 -m pytest -q research/fir-upgrades/test_intervention.py`. New saved
row tests use copied historical GCC10/GCC15 controls and exercise real raw,
output, ELF, binary, stack, wrapper, input, and anchor admission. Behavioral
mutation tests added after the interrupted implementation are retrospective
regressions, not historical TDD evidence. Binary-identity, fixture checkpoint,
bounded CLI option, and immutable attempt tests failed before their fixes.

## Saved evidence audit work

The CLI entry point was moved after helper definitions so `--run` and `--verify`
can resolve their functions when invoked as a script. Saved-row checks bind
rows to fixed identities, contained artifacts, exact input and wrapper bytes,
actual binary digest, ELF, disassembly, stack, commands, tools, raw counters,
and full output/history/guard/state traces. The copied historical rows pass
`audit_row`; they remain test fixtures, not new measurements. The runner now
atomically checkpoints only after `audit_row`, resumes admitted checkpoint
rows without invoking target tool identities, and recovers a complete
`evidence.json` attempt before choosing a new attempt. The controls-only CLI
regression patches target execution and fails on specialization or duplicate
identity invocation. These behavioral tests were added after most runner code;
they establish regressions but do not rewrite the unverifiable interrupted
history as test-first development.

## Released target campaign

After root review accepted the two saved general controls, the remaining two
specialized performance and four edge correctness conditions were released.
An initial GCC10 control attempt had already completed compilation and
simulation before admission found that GCC reported the assembler as `/usr/lib/
arm-none-eabi/bin/as`. The attempt and raw output were preserved. The saved
admission rule was corrected to accept the compiler-reported `as` and `ld`
basenames, and the same completed identity was recovered without a second
target run. The GCC15 control and the six released rows each ran once.

The completed checkpoint contains exactly four performance and four
correctness-only rows. Direct `--verify` reports all eight admitted and no
tool execution. Both performance general controls match their frozen binary
hashes and full corrected event vectors; the reducer recomputes the per-compiler
event/cycle/energy deltas and `G_general=70469.699925 nJ`. Scoped tests were
rerun after completion: **39 passed**. Assembly-based preparation-removal
interpretation remains pending independent Sol review.

## Scoped admission repair round 1

The reviewer reproduced three saved-evidence defects using copied metadata and
mocked commands; no target compiler or simulator was invoked for these fixes.
The complete eight-row package initially failed relocated verification because
stack frame diagnostic paths retained the original workspace prefix. Admission
now canonicalizes only `frames[].file` and `frames[].source` when their
attempt-relative suffix is verified, while comparing every semantic frame,
chain, edge, byte count, line, column, and kind unchanged. The actual complete
campaign now verifies from a copied tree with `PATH=/nonexistent`.

The mocked size-command failure occurs after a simulated run has written raw
stdout/stderr. An atomic execution receipt written before the simulator records
the command intent; after simulation it binds status and both raw digests. A
later invocation sees that executed but unadmitted attempt and fails closed
before calling the simulator again. Its artifacts remain in place. Existing
completed evidence without receipts remains reusable.

Saved admission now rederives ELF section sizes, stack usage diagnostics,
fixture source hashes, kernel identity/delta, and size output from their actual
files. The top-level bound, source identities, toolchain identities, simulator
hash and historical anchor header/rows are also checked against the frozen
protocol and raw anchors. The reviewer-provided mutations for the anchor header
and `.text` size had failed to reject before these checks; they now fail
admission. Final scoped verification reports **48 passed**; direct `--verify`
reports 8 admitted rows with `toolchains_executed: false`. No target artifacts,
commands, flags, or historical results were changed in this repair round.

## Scoped admission repair round 2

The rereview supplied two concrete regressions. First, an actual one-control
prefix checkpoint was rejected because the verifier reconstructed the frozen
toolchain header from whichever rows happened to be present. The new test
failed on that checkpoint before the change. Verification now validates both
frozen compiler identities independently, then binds each present row to its
matching header entry. Second, a copied specialized row with only its saved
energy changed to `0` was rejected by recovery but could fall through toward
another run. The new test failed because the recovery seam was missing. All
campaign recovery paths now fail closed when an unadmitted attempt already has
an intent receipt or raw output, even when an invalid `evidence.json` exists.
The regression forbids the compile callback and confirms it is never called.

After these changes, `python3 -m pytest -q research/fir-upgrades/test_intervention.py`
reports **50 passed**. Direct verification and verification with
`PATH=/nonexistent` both admit the unchanged eight-row package with
`toolchains_executed: false`; the copied complete package also verifies after
relocation. No target command, measurement, raw artifact, build flag, or
reported result was changed. These RED/GREEN checks are new behavioral evidence
and do not rewrite the earlier chronology or claim test-first history for the
interrupted implementation.

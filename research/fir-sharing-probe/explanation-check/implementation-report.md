# Checker implementation record

20 October 2026. This file records the Sol 6.0/high checker worker's implementation and observed commands. The peer `compiler-explanation/accounting.json` was absent during this run. The generated `verification.json` therefore says `pending`, has zero peer rows checked and no peer hash. Literal fixtures are illustrative tests, never measurements of the peer's generated code.

## Frozen input and derived result

The checked source hashes equal the plan: design `bc4fac9e…`, sharing result `57c8b9f9…`, partial-direct result `eb53d3e5…`, kernel `5832b52e…`, and six-case archive `8aa24f41…`. The checker rehashes all 17 manifest artifacts in each block1 case, including the exact firmware binaries (`07fd7023…` for GCC10, `114041b0…` for GCC15). It decodes the two original `firmware.stderr` histograms with the pre-existing independent checker and checks the original result rows against them; the closing marker instruction is excluded. The model is recomputed with the frozen decimal weights. ELF symbols, `.su` reports and saved `probe_process.disasm` yield respective symbol/frame/SP-address-site values of 1036/72/19 and 1372/240/147. An SP-address site means an instruction line containing `[sp]` or `[sp, …]`; it is not evidence of a spill.

GCC15 minus GCC10: instructions 43,820; MUL 0; RAM reads 13,878; RAM writes 19,275; flash reads/writes 0; taken branches 131; BL 0; estimated cycles 77,235; modeled CPU energy 70,469.699925 nJ. The four frozen candidate winners remain GCC10 partial direct at blocks 1/64 and GCC15 demand Hcub at blocks 1/64. The GCC15/block1 within-compiler Hcub saving is 24.06%; the selectable-compiler Hcub savings against GCC10 partial direct are 3.97% at block1 and 2.30% at block64.

## Test-first evidence

The initial command, before `verify.py` existed, was:

```text
python3 -m unittest discover -s research/fir-sharing-probe/explanation-check -p 'test_*.py' -v
```

It exited 1. Its first failure was `test_absent_peer_is_pending_with_no_checked_rows ... FAIL` with `/usr/bin/python3: can't open file '.../explanation-check/verify.py': [Errno 2] No such file or directory`; the observed footer was `Ran 14 tests in 0.400s` and `FAILED (failures=28, errors=2)`. The two errors were a test-loop reset issue, corrected before implementation. After the first implementation, the same command exited 1 with `verification failed: frozen source groups mismatch`: the result stores objects with `first`/`past_last`, rather than bare pairs. Correcting that reader made all 14 tests pass.

The later comparator test was added before comparator code. The same command exited 1 with the specific failure:

```text
test_literal_fixture_reconciles_two_rows_without_causal_certificate ... FAIL
AssertionError: Lists differ: [] != ['partial_direct32x2', 'partial_direct32x2', 'trans_hcub_demand', 'trans_hcub_demand']
Ran 15 tests in 1.438s
FAILED (failures=1)
```

After comparator implementation, the exact command exited 0: `Ran 15 tests in 1.822s` and `OK`. These tests exercise two-row admission, residual and one positive dynamic component fixture, changed totals and component sums even with renewed evidence hashes, missing/duplicate/extra compilers and components, source/binary/block mismatches, schema/enums/boolean/negative counts, missing/malformed/changed evidence, absolute/traversal/symlink escapes, unsupported static-only attribution, missing dynamic references, pending delivery, and invalid-peer nonzero exit without overwriting prior reports.

An additional report-field test for per-component GCC15-minus-GCC10 deltas was then run before implementation. The same 15-test command exited 1 with `AssertionError: None != 43820`, `Ran 15 tests in 1.655s`, `FAILED (failures=1)`. After adding those deltas to consistent reports (and `null` while pending), it exited 0 with `Ran 15 tests in 1.661s` and `OK`.

The pending report's explicit `reconstructed_totals` field was likewise tested first: the same command exited 1 with `AssertionError: None != 198670`, `Ran 15 tests in 1.844s`, `FAILED (failures=1)`. Adding the raw-log-derived field led to exit 0, `Ran 15 tests in 1.749s`, `OK`.

Final fresh verification after the last code edit: the explanation-check suite exited 0 (`Ran 15 tests in 1.786s`, `OK`); the existing independent-check suite exited 0 (`Ran 27 tests in 0.902s`, `OK`). The default checker command again exited 0 with `{"status": "pending", "peer_rows_checked": 0}`.

The production invocation:

```text
python3 research/fir-sharing-probe/explanation-check/verify.py
{"status": "pending", "peer_rows_checked": 0}
```

exited 0. The existing independent checker suite also passed:

```text
python3 -m unittest discover -s research/fir-sharing-probe/independent-check -p 'test_*.py' -v
Ran 27 tests in 0.898s
OK
```

## Deliberate limit

`consistent` means exact frozen counter totals, component sums, file identities, schema and declared basis passed. It does not parse an arbitrary peer PC trace to prove each classification or infer causal value flow. A nonzero component needs a hashed non-static-only supporting reference, but a plausible reference can still mislabel a PC. Manual causal review remains `pending` even for a consistent report. Zero and residual counts remain permitted. An exact-control-flow claim requires manual inspection of its path-frequency proof. No new simulator run or performance measurement was made.

## Final-review correction: component event feasibility

The fresh reviewer found that a component could claim RAM writes, taken branches or BL events while claiming zero executed instructions, provided its global sums stayed correct. A new test redistributed one event at a time from `unattributed` to the zero-instruction `stream_wrapper`, retaining the original totals and a hashed fixture reference. A second test assigned two taken branches or BL events to one instruction. The corresponding test command was:

```text
python3 -m unittest discover -s research/fir-sharing-probe/explanation-check -p 'test_*.py' -v
```

Before the fix it exited 1. The five relevant subtests each returned `{"status": "consistent", "peer_rows_checked": 2}` where rejection was expected; the observed footer was `Ran 18 tests in 2.067s` and `FAILED (failures=5)`. A positive control with one instruction and two RAM writes passed, preserving multi-register transfer semantics.

The checker now requires every zero-instruction component to have zero events and bounds `taken_branches` and `bl` by that component's instruction count. It does not impose an invalid one-transfer-per-instruction RAM limit. After the fix the same command exited 0 (`Ran 18 tests in 2.019s`, `OK`). The existing checker suite exited 0 (`Ran 27 tests in 1.016s`, `OK`). Regenerating the production report with `python3 research/fir-sharing-probe/explanation-check/verify.py` exited 0 and printed `{"status": "pending", "peer_rows_checked": 0}`. The actual peer report is still absent, so manual causal review remains pending.

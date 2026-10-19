# Independent missing-baseline check

Task 2 of the [two-person plan](../../../docs/superpowers/plans/2026-10-20-fir-baseline-check.md).
This directory owns verification and comparison; it contains no peer kernel.

The checker uses Python's standard library and arbitrary-precision integers. It
does not import the generator, baseline reference, peer code, or their expected
values. It reads existing artifacts without executing firmware or compiling a
target binary. It checks all four admitted nontransposed historical alternatives,
ordinary transposition and demand Hcub: 24 rows across the four configurations,
6,168 output comparisons, one common 257-sample stream.

From the original workspace, which retains ignored raw artifacts:

```bash
python3 -m unittest discover -s research/fir-sharing-probe/independent-check -p 'test_*.py' -v
python3 research/fir-sharing-probe/independent-check/check.py
```

From a normal checkout with a separate copy of the original artifact tree:

```bash
FIR_PROBE_ROOT=/path/to/original/research/fir-sharing-probe python3 -m unittest discover -s research/fir-sharing-probe/independent-check -p 'test_*.py' -v
python3 research/fir-sharing-probe/independent-check/check.py --probe-root /path/to/original/research/fir-sharing-probe --output-dir research/fir-sharing-probe/independent-check
```

`--probe-root` must include the frozen sources/results and `build/cases/`; sibling
`fir-baseline/` must contain the frozen design and recorded dependency sources.
Without raw artifacts, portable reference/parser/model tests still run and the
historical integration tests explicitly skip. A saved report does not remove the
need to retain the raw evidence for independent rechecking.

Outputs are [verification.json](verification.json), [comparison.md](comparison.md)
and [reference-cases.json](reference-cases.json). The last file specifies expected
outputs and per-call history for signed edges, zeros, sign-aligned overflow cases
and repeating `1/64/3/16` partitions with short final calls. It is a reference
specification, not a record of target executions. [positioning.md](positioning.md)
maps the possible contribution against primary sources and keeps the decision
conditional until the peer evidence arrives.

## Once the peer returns

```bash
python3 research/fir-sharing-probe/independent-check/check.py --peer-results research/fir-sharing-probe/partial-direct/results.json
```

The peer JSON must contain exactly the four configuration rows from the plan.
Top-level metadata uses `stage`, `design_sha256`, `sharing_results_sha256`,
`compilers`, `flags` and `model`. The sharing hash also accepts
`baseline_results_sha256` or `results_sha256`; if several are present they must
agree. Compiler entries contain `version` and `sha256` matching the frozen
compiler identities. `flags` is a JSON list of command arguments, either common
at the top level or under each compiler entry. `model` copies the explicit
historical parameter fields from the frozen sharing results. This checks the
pinned environment; a different compiler build requires a separate comparability
decision rather than silently treating it as identical.

Each row's `directory` is relative to the peer result directory. `artifacts`
maps filenames relative to the case directory to SHA256 digests. Preserve the
kernel source, `firmware.c` with literal `input_data` and `BLOCK`/`SAMPLES`, binary,
ELF, disassembly, `.su` files and raw `firmware.stdout`/`firmware.stderr`. Keep
the existing `O:/H:/G:/M:` records. This matches the current research fixture;
alternate field/file conventions need an explicit adapter, not guessed values.

All checks finish before reports are written. A verification error exits nonzero.
The four peer evidence rows can then populate the comparison; no peer numerical
values are inferred when they are absent.

## What remains a manual check

Checksums and matching transcripts establish saved-evidence consistency, not
artifact authenticity, a proof that source compiled into the claimed binary,
or correctness for every possible stream. In particular, equal outputs cannot
prove that the peer used native-width partial sums: tests intentionally exercise
the result format with existing wide-direct fixtures. Those fixtures never
become reported peer measurements. At the join, inspect the actual C and emitted
instructions for the fixed groups, safe prefixes, widening before the final add,
single final quantization, flags and complete measurement boundary. Review the
peer's host UBSan/signed-edge tests and logs separately.

Code bytes are the historical selected-symbol metric, not complete image size.
Wrapper and callee frame reports are separate, not a stack high-water estimate.
Timing and CPU-energy costs retain their architectural/model assumptions; raw
simulator ticks are diagnostic and no physical energy claim follows.

## Completion audit, 20 October 2026

A fresh requirements and code review found one evidence-integrity defect that
the original 24 tests missed: opcode secondary bins were not checked against
their primary totals. Changing the MUL bin while updating the manifest and
derived energy could therefore pass despite an internally inconsistent trace.
Two regression tests reproduced this, including a copied historical artifact;
both failed before the fix. The checker now validates bin shape, nonnegative
counts and totals according to the pinned simulator's actual dispatchers.
Primary-only opcodes correctly retain zero secondary bins. All 26 tests pass,
and all 24 historical rows / 6,168 outputs still verify with unchanged costs.
A separate forward-convolution calculation also matched all 594 saved reference
outputs, per-call histories and terminal states across the four reference cases.

The review found no documented coding-standard violations or consequential
code-quality concerns beyond that repaired defect. The missing Doppler
partial-accumulation precedent is now included in the positioning note.

One integration limitation remains explicit: the checker implements the
historical fixture's filenames and literal C input format described above,
not every possible artifact layout allowed by the plan's general schema.
Alternate peer layouts require an adapter at the final join; rejection of an
unrecognized layout is not a numerical failure. Actual peer arithmetic,
assembly and UBSan evidence still require review when delivered.

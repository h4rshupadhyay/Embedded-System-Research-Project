# Independent compiler-explanation check

USER workstream of the [parallel plan](../../../docs/superpowers/plans/2026-10-20-fir-compiler-explanation.md).
The peer owns `../compiler-explanation/`; this directory owns consistency checks
and paper-claim preparation. It does not generate a replacement FIR kernel or
new performance rows.

**Independent milestone complete, 20 October 2026:** the checker, rejection
tests, claim/evidence assessment and paper outline are ready. A fresh Astra
review found one event-ownership defect; regression tests reproduced it and
the fix passed all 58 tests across the new and existing suites. The actual peer
report remains pending. See [review.md](review.md) for the review and correction.

The peer report is absent at assignment start. A pending report means the source
evidence was checked and no peer rows were admitted. Passing synthetic-fixture
tests does not establish that a real compiler explanation is correct.

## Run

Use Python 3.10 or later and the standard library. If the original raw cases are
absent, restore the versioned archive from the repository root:

```bash
sha256sum -c research/fir-sharing-probe/independent-check/partial-direct-target-evidence.sha256
tar -xzf research/fir-sharing-probe/independent-check/partial-direct-target-evidence.tar.gz -C research/fir-sharing-probe/partial-direct
```

Then run the tests and the real report command:

```bash
python3 -m unittest discover -s research/fir-sharing-probe/explanation-check -p 'test_*.py' -v
python3 research/fir-sharing-probe/explanation-check/verify.py --peer-report research/fir-sharing-probe/compiler-explanation/accounting.json --output-dir research/fir-sharing-probe/explanation-check
```

Missing peer report: exit 0, `status="pending"`, zero peer rows checked.
Admitted report: exit 0, `status="consistent"`, two rows checked, manual causal
review still pending. Invalid delivered evidence: nonzero exit and an actionable
error; previously valid reports are preserved.

## Evidence boundary

The canonical inputs are the frozen `partial-direct/results.json`, its two
block1 raw case manifests and the existing numerical decoder/cost model in
`../independent-check/check.py`. The checker does not import the peer's analyzer
or its classification logic. Original eight event totals, source identities and
the exact GCC15-minus-GCC10 deltas must agree independently of peer statements.

Component counts must reconcile to each original total. Unsupported components
remain in `unattributed`; static instruction sites and compiler frame sizes are
diagnostics, not dynamic counts or proof of spill causation. Hashing an annotation
establishes its identity, not the truth of its explanation. A numerically
consistent report still requires checking representative PC/source-value claims.

Zero-instruction components must have zero events; branch and BL counts cannot
exceed the component's instruction count. Multiple RAM transfers per instruction
remain allowed. `sp_relative_instruction_sites` is checked using the original
`probe_process.disasm` lines containing `[sp]` or `[sp, ...]`; this convention
does not count all possible stack accesses or establish spill causation.
Candidate-ranking context comes from the frozen saved results, not a new run
or a fresh verification of historical raw traces.

## Files and final join

- `verification.json` and `comparison.md`: generated source verification and
  peer-accounting status. Regenerate using the command above, not a fixture.
- `claims.md` and `paper-outline.md`: bounded paper argument with pending causal
  evidence, primary-source overlap and explicit comparator/model limits.
- `implementation-report.md`: worker's implementation and test evidence.
- `progress.md` and `review.md`: execution/routing and fresh-review record.

When the peer delivers real `accounting.json` and its hashed evidence files,
rerun the same command. Resolve rejected data and inspect the annotations before
writing `final-decision.md` or changing the paper's causal claims. This independent
milestone can finish before the peer; the final causal join cannot.

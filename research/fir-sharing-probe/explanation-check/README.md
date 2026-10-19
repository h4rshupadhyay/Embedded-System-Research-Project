# Independent compiler-explanation check

USER workstream of the [parallel plan](../../../docs/superpowers/plans/2026-10-20-fir-compiler-explanation.md).
The peer owns `../compiler-explanation/`; this directory owns consistency checks
and paper-claim preparation. It does not generate a replacement FIR kernel or
new performance rows.

**Final join complete, 20 October 2026:** the actual peer report is numerically
consistent (two rows, 29 evidence hashes). Manual review accepts a partial
explanation: extra direct-SP transfers account for the full RAM-traffic increase
and 85.0151% of the modeled energy increase. Remaining instruction/branch costs
and the compiler-pass cause are unresolved. See [final-decision.md](final-decision.md)
and [review.md](review.md) for evidence and independent review.

The peer report was absent at assignment start; the original independent
milestone and its checker correction are preserved in `progress.md` and
`review.md`. The reports now describe the actual delivered accounting.

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
- `claims.md` and `paper-outline.md`: bounded paper argument with accepted partial
  evidence, primary-source overlap and explicit comparator/model limits.
- `implementation-report.md`: worker's implementation and test evidence.
- `progress.md` and `review.md`: execution/routing and fresh-review record.
- `final-decision.md`: manual acceptance, explained costs, residual and stopping
  decision. This supplements the automated report's deliberately unchanged
  `manual_causal_review="pending"` field.

The takeover merged peer checkpoint `7315427` and verified the actual report
with the command above. Analyzer regeneration matched every hashed output;
binary/control-flow and source-value review preceded the paper-claim update.
No new target measurements were made. The next scoped step is writing the paper.

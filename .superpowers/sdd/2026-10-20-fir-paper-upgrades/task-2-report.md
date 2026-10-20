# Task 2 report: saved-event analysis

## Status and commits

Implemented and committed Task 2. The implementation and generated outputs are in
commit `2b0d24b54108dd35045971eed6783175c75b9a86` (`Add exact saved-event FIR
analysis`). This report is committed separately because it records that commit.

## Changed files

- `research/fir-upgrades/analyze.py`
- `research/fir-upgrades/test_analyze.py`
- `research/fir-upgrades/analysis/analysis.json`
- `research/fir-upgrades/analysis/analysis.md`
- `research/fir-upgrades/tdd-log.md`
- `.superpowers/sdd/2026-10-20-fir-paper-upgrades/task-2-report.md`

The concurrent change in `research/fir-upgrade-gates.md` was already present in
the shared workspace and was not staged or committed by this task.

## Behavior and output contract

`analyze_report(report: dict) -> dict` accepts the 20 rows and checks unique
compiler/block/variant identities, 257 samples, event counts, reconstructed
modeled energy, and Arm zero-wait cycles. It produces the 12 oriented pairs in
GCC10/1, GCC10/64, GCC15/1, GCC15/64 order, with each of the three U2
contrasts. Six event coordinates determine event dominance. The JSON also
retains instruction, BL-call, and flash-write deltas; six component-energy
deltas; whole-stream and per-output energy differences; full-precision relative
percentages; cycle and separate resource deltas; and affine stress results.

`affine_boundary(A: Decimal, B: Decimal) -> dict` rejects non-Decimal or
nonfinite inputs. For nonconstant lines it derives the root as an exact
`Fraction`, retains its integer numerator and denominator, and classifies it
against lambda ≥ 0 and the closed [0.5, 2] region without using the displayed
six-decimal root. Constant lines and all-tie lines have no unique root. Winner
labels at 0.5, 1 and 2 and strict-throughout flags use unrounded endpoint
values. Percentage divisions use a local precision-50 Decimal context; the
module does not change the process-wide Decimal context.

The command
`python3 research/fir-upgrades/analyze.py --output-dir research/fir-upgrades/analysis`
checks all six pinned source hashes, rebuilds the paper report through the
existing exporter, requires equality with the saved 20-row report, then writes
only `analysis.json` and `analysis.md`. It refuses the original paper directory.
Input/admission failures occur before output writes; a temporary real-file test
changed one frozen source and confirmed that existing output sentinels were
preserved.

The output schema is version 1. Its top-level and per-pair `source_digests`
identify the six frozen inputs. Each pair names compiler, block, left/right
variant and sample count. The Markdown table summarizes all 12 contrasts and
explicitly describes the RAM coefficient as arbitrary model sensitivity, not a
physical confidence interval or hardware price.

## RED/GREEN evidence and checks

Detailed command history and results are in `research/fir-upgrades/tdd-log.md`.
The observed behavior REDs included the absent `affine_boundary` seam, absent
`analyze_report` seam, a report-row admission mismatch exposed by the saved
CMSIS rows, missing event delta keys, root display precision disagreement with
the six-decimal U2 anchors, and uncaught `decimal.InvalidOperation` on malformed
serialized energy. Each identified implementation issue was corrected and the
focused tests passed. The literal GCC10/block1 event-vector test checks
`(-5141, -2570, -10794, 21845, 30326, -1028)`, plus instruction, BL and flash
write deltas. Tests also cover all four literal A/B/root anchors, the four
incremental-sharing percentage anchors, all 12 pair identities, nominal
A+B reconciliation, affine zero/constant/all-tie/negative/endpoint/outside
cases, a constructed event-equal pair, mixed outcomes, nonfinite input,
mutation rejection, CLI identity rejection, output preservation and
repeatability.

One final staged verification attempt failed after an apparently unused `os`
import was removed; the atomic writer still uses `os.fdopen`. I restored the
import, reran the CLI successfully, and recorded the failed attempt in the TDD
log. The failed call left a temporary file, which was removed; it did not
replace either analysis output.

Actual final commands and outcomes:

- `python3 -m unittest discover -s research/fir-upgrades -p test_analyze.py -v` — 12 tests passed.
- `python3 research/fir-upgrades/analyze.py --output-dir research/fir-upgrades/analysis` — completed; six frozen hashes passed, raw report reconstruction matched the saved 20-row report, and both outputs were regenerated.
- `python3 -m unittest discover -s research/fir-paper -p test_build_results.py -v` — all 15 exporter tests passed.
- `git diff --cached --check` — passed before commit.

The original report SHA-256 is unchanged from base:
`research/fir-paper/results.json` —
`3161d9a01ae81d0cb1ae38b81bc0ea2d02bd1e3cb8ca604e13f5a2f72defe6fd`.
The original manuscript TeX is unchanged:
`research/fir-paper/manuscript.tex` —
`78e83e6283ede9ae2d79d3e440a3246fd6b052028a3a6143c4a161c878bd49c4`.

## Concerns and limits

A subset of affine edge-case tests was added after the minimal helper existed,
so those cases have passing regressions but not separate pre-implementation
RED observations; the TDD log marks this explicitly. The scientific analysis
itself is bounded to the frozen 257-output report and the prescribed arbitrary
RAM-weight path. No target builds/runs or physical-energy claims were made.

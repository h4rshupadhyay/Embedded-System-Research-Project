# U2 saved-event analysis TDD log

Base: `a5ba80b35cd730db8696257ddca8e58e546a959e`. Production code was built
against the saved 20-row `research/fir-paper/results.json` and the U2 appendix.
No target compiler or target program was run.

## RED/GREEN record

1. `affine_boundary` exact-root behavior: wrote a test for `A=-2, B=2`, exact
   root `1/1`, and selected-region classification. The first import attempt
   failed because the module did not exist; after creating the empty module,
   the focused command failed specifically because `affine_boundary` was
   absent. Added the minimal Fraction-based helper and reran; the test passed.
   When the literal U2 root anchors were added, they failed against the helper's
   unrounded display; display was changed to six decimals and the test passed.
2. Boundary behavior: added checks for all-tie and constant cases, a negative
   root, exact 0.5 and 2 region endpoints, zero as the nonnegative-domain
   boundary, a positive root above the region, and nonfinite Decimal input.
   The focused suite passed. These edge tests were added after the initial
   helper existed, so they are useful regressions but were not independent
   pre-implementation RED cycles.
3. Public report analysis: added literal percentage and A/B/root anchors for
   the 12 pairs. Before adding `analyze_report`, discovery failed specifically
   because that public function was absent. The first implementation then
   produced an expected failing result because the saved report has 20 rows,
   including CMSIS, while the contrast uses four variants. The admission set
   was corrected to retain all five saved variants. A later anchor run showed
   that the test expected too many root decimals; the U2 displayed anchors are
   six decimals, and the test was corrected to those literal anchors. The
   report test then passed.
4. Event delta shape: after writing a regression requiring `delta_events` to
   include all six coordinates plus instructions, BL calls, and flash writes,
   the focused suite failed with the three requested keys missing. Added those
   deltas and kept dominance over only the six U2 coordinates; rerun passed.
5. Invalid serialized energy: added a mutation test with a nondecimal energy.
   It failed with uncaught `decimal.InvalidOperation`. Converted malformed
   energy into a `ValueError` admission failure; rerun passed.
6. Independent event reconstruction: the literal GCC10/block1 Hcub-minus-
   partial event vector is checked as `(-5141, -2570, -10794, 21845, 30326,
   -1028)` in the ordered six coordinates, with `instructions=-7711`,
   `bl=0`, and `flash_writes=0`. It passes. All 12 affine `A+B` totals are
   also checked against their nominal energy deltas.
7. CLI behavior: temporary real files exercise a changed frozen source and
   preexisting output sentinels. The CLI returns failure and preserves both
   outputs. Another temporary root checks that the original-paper output
   directory is refused without modifying its sentinel. Both pass.

## Final commands and results

`python3 -m unittest discover -s research/fir-upgrades -p test_analyze.py -v`
passed 12 tests. The tests cover literal incremental-sharing margins,
all four literal affine anchors, pair identities/order, exact event deltas,
nominal A+B reconciliation, affine ties/domain/endpoints, nonfinite input, event equality and mixed
outcomes, report mutation rejection, deterministic semantic output, and CLI admission and
output preservation.

`python3 research/fir-upgrades/analyze.py --output-dir research/fir-upgrades/analysis`
completed successfully. It checked the six frozen source identities, rebuilt
the saved paper report through `build_results`, verified equality with the
saved 20-row report, and emitted `analysis.json` and `analysis.md`. One staged
verification attempt immediately after removing an import failed with
`NameError: os is not defined` at the atomic writer; restoring the required
`os` import made the CLI pass. That failed attempt did not replace either
output file.

`python3 -m unittest discover -s research/fir-paper -p test_build_results.py -v`
passed all 15 relevant exporter tests. Decimal precision is changed only in
local contexts in the new analyzer; there is no import-time global context
mutation.

The existing report and manuscript TeX SHA-256 values match the base commit:
`results.json` `3161d9a01ae81d0cb1ae38b81bc0ea2d02bd1e3cb8ca604e13f5a2f72defe6fd`
and `manuscript.tex`
`78e83e6283ede9ae2d79d3e440a3246fd6b052028a3a6143c4a161c878bd49c4`.

## Review fix round (base `9912373819bc13a26779cc97ccba1589642b6a69`)

### Observed REDs

Added public-behavior tests before the fix for a canonical `analyze_report`
call under caller `localcontext(prec=6)`, an exact root of `1e50`, and an
endpoint only `1e-51` below 0.5. The first focused suite observed:

- `test_analysis_is_independent_of_callers_low_decimal_precision` raised
  `ValueError: report row ('gcc10', 1, 'cmsis64_unroll') energy does not
  reconstruct from its event counts`.
- `test_large_finite_root_can_be_displayed` raised
  `decimal.InvalidOperation` while quantizing the valid `1e50` root.
- The beyond-50-digit test then failed on the missing public `winner_at`
  result for lambda 0.5. Added that behavior to `affine_boundary`; it now
  reports `right` at 0.5 while preserving the exact root classification as
  below the interval even though the displayed root rounds to `0.500000`.

The exact-endpoint fixture separately sets A/B so the root is exactly 0.5 or 2;
for either tie, the corresponding strict-throughout flag must be false. The
hand-built report fixture uses literal integer event deltas and reconstructed
row energies/cycles. It passed after the exact Fraction implementation. Added
public report mutations proving event dominance in left, right and mixed cases,
and physically swapped the numeric rows in the Hcub/partial pair to check that
the report's oriented event and energy signs reverse. These added coverage
cases passed; they did not each have a distinct pre-fix RED.

### Fix and final verification

Replaced Decimal-context-dependent event products, sums, deltas and endpoint
comparisons with exact Fractions derived from the frozen finite Decimal
weights. `analyze_report` now preserves its caller's Decimal context. Decimal
conversion for display uses a local context sized to the exact integer digits;
percentage and per-output divisions use precision 50. Root and endpoint
classifications continue to use exact rational values. A follow-up test run
caught a `NameError` from the first internal affine-helper extraction (the
constant-line branch still referenced the public parameter name); changing it
to the helper's exact coefficient fixed the issue.

Final review-round commands:

- `python3 -m unittest discover -s research/fir-upgrades -p test_analyze.py -v` — 18 tests passed.
- `python3 research/fir-upgrades/analyze.py --output-dir research/fir-upgrades/analysis` — completed and regenerated both saved outputs through the six-source identity and raw-report reconstruction gates.
- `python3 -m unittest discover -s research/fir-paper -p test_build_results.py -v` — all 15 exporter tests passed.

The JSON output intentionally changed in three ways: it now includes exact
`winner_at` labels for 0.5/1/2 in each affine boundary; exact rational energy
ratios have corrected final displayed digits that previously depended on
ambient Decimal rounding; and exact per-output decimals omit insignificant
trailing zeroes. The six-decimal A/B values, six-decimal displayed roots, six-
decimal Markdown percentages, all literal gate anchors and all strict outcome
labels remain unchanged. The paper report and manuscript were not written.

The independent exact-endpoint fixtures additionally assert literal affine
coefficients: `(A,B)=(16.723762,-33.447524)` at lambda 0.5 and
`(35.207920,-17.603960)` at lambda 2. The first expectation draft had the
signs reversed and failed; correcting the fixture signs made both endpoint
cases pass, with the tied endpoint defeating the corresponding strict flag.

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

# Stage 1 derived-analysis TDD log

Commands below ran from the repository root. RED entries record observed command output; no RED result is inferred after the fact.

1. **Hypothesis helper.** Added the strict four-margin equality case and ran `python3 -m unittest discover -s research/fir-paper -p test_build_results.py -v`. RED: the test reached `assess_hypothesis` and raised `NotImplementedError`. Implemented the pure helper; the same command passed.
2. **Report path.** Added the successful report contract and confirmed RED with `AssertionError: hasattr(build_results, 'build_report') is not true`. Implemented selection and derived report generation; the same focused command passed with 20 rows and H_R passes `[false, false, true, true]`.
3. **Duplicate semantic row.** With the semantic validator reduced to a placeholder, its test failed because no `ValueError` was raised. Added duplicate selection detection; focused tests passed.
4. **Changed numeric total.** With `build_report` not yet invoking semantic admission, the test failed because no `ValueError` was raised. Connected the pure validator to `build_report`; the test passed with an actionable energy reconstruction error.
5. **Selection and cross-source admission.** Added missing-row, bad-sample-count, wrong-filter, wrong-range, and conflicting verification-total cases. The first run showed missing/wrong-filter/wrong-range rows reaching a `KeyError`, while invalid samples and conflicting totals were accepted. Added/connected explicit admission checks so these are `ValueError`s; all cases passed. The earlier duplicate and changed-energy tests remained green.
6. **CLI byte identity and output preservation.** Added copied-fixture cases that alter a frozen identity field and a numeric total while an existing output sentinel is present. RED: the identity-field mutation exited successfully; the numeric mutation failed later with a semantic energy error instead of a frozen-identity mismatch. Added the SHA-256 gate before document loading/building; both cases then failed at the identity gate and preserved the sentinel bytes.
7. **Independent numerical expectations.** Added independently known historical Hcub/CMSIS, four corrected Hcub/partial margins, explanation residual/fraction, and selectable-compiler percentage. RED caught the selectable comparison using the wrong denominator (`-7.953687...` rather than `3.96735885`). Corrected it to compare each block's best Hcub result against its best partial-direct result; all numeric assertions passed.
8. **Table contract.** Added a table-header/value assertion. RED showed a misleading repeated H_R value under a per-row “Hcub relative energy” heading. Changed the main table to report per-row cycles/output and energy, with H_R margins in a separate table; focused tests passed.
9. **Additional helper and determinism checks.** Added all-negative, positive, equality, invalid-count/type/nonfinite margin cases. The valid CLI was run twice into separate directories; `results.json`, `tables.md`, and `source-manifest.json` were byte-identical. These checks record observed behavior; they were added after the initial helper/exporter RED/GREEN slices.
10. **Final commands.** `python3 -m unittest discover -s research/fir-paper -p 'test_*.py' -v` ran all 9 `test_build_results.py` tests successfully, then exited 1 on the concurrently present `test_render_paper.py` because the environment lacks `pypdf` (`ModuleNotFoundError`). `python3 research/fir-paper/build_results.py --output-dir research/fir-paper` completed successfully and generated the three artifacts. No source evidence was edited and no compiler, simulator, build, or target process was run.

A first broad exporter draft was written before its tests; after the sequencing issue was raised, that draft was preserved at `build/fir-paper-tdd/build_results-draft.py`, production `build_results.py` was reduced to the already-tested hypothesis helper, and subsequent production capabilities were reintroduced in the test-first slices above. The preserved draft is a private workspace reference, not test evidence.

## Combined-suite environment follow-up

The standard `python3` full-discovery run above accurately records the initial `pypdf` import failure. `test_render_paper.py` contains pytest-style function tests; `unittest discover` imports that module but does not execute those pytest functions. With `/tmp/fir-paper-render-env/bin/python`, full unittest discovery passed the 14 `test_build_results.py` cases. This log makes no claim about the renderer's pytest checks. The scoped command `python3 -m unittest discover -s research/fir-paper -p test_build_results.py -v` passed the same 14 cases.

## Review-driven semantic checks

After the initial 9-case run, I observed duplicate class declarations in `test_build_results.py` that had shadowed the duplicate-source-row test. I gave the two test groups distinct class names; unittest discovery then included that case. Independent percentage assertions now compare `Decimal` values to literal expected margins/tolerances without converting through binary float.

Added first, then observed RED for four further semantic contracts: event-reconstructed timing cycles; accounting totals and explanation totals jointly changed away from the selected partial raw events; exactly one GCC10 and one GCC15 block1 accounting identity; and explanation delta matching the raw block1 rows. The prior validator accepted each mutation. Added validation of the cycle formula, exact accounting compiler/block set, all eight accounting event totals against selected partial rows, raw GCC15-minus-GCC10 event deltas, and the modeled-cycle/energy delta formulas. Focused unittest discovery then passed all 14 cases.

The report rows now identify the independent diagnostic source path and whether diagnostics came from `rows` or `peer_rows`; a test failed on the missing provenance fields before they were added. The comparison object carries exactly the three requested Hcub-relative vectors; the ordinary-transposed comparison remains in `derived_comparisons`, as checked by a test that first failed on the extra vector.

## Plot metadata reproducibility follow-up

Applied a fixed Matplotlib SVG hash salt (`fir-stage1-paper`) and disabled SVG Date metadata. Ran the plot generator twice with:

```sh
/tmp/fir-paper-render-env/bin/python research/fir-paper/make_figures.py
```

SHA-256 outputs matched across runs for all four artifacts:

- `baseline-robustness.png`: `3da27ea260d37fa984c94bc413a5e7b691557b73ab9b63386be2d1cc76f97df8`
- `baseline-robustness.svg`: `1702c36f0160d8d72493f225faa911ad212fff98fdf776137d764dc5b4c3c98c`
- `stack-attribution.png`: `549a7f14b4f2f1855ad0f0ef90d3f63d6ddaff7ce4486df055d41f2440c11655`
- `stack-attribution.svg`: `5bdc5940c8a17987f0ca46b0a0a441c40aafdb5a4cb736a438019e22e3636806`

## Incremental Hcub comparison regression

Added an independent `Decimal` regression using the four literal whole-stream
energies reconstructed from the frozen event rows for Hcub and ordinary
transposition. From `research/fir-paper`,
`python3 -m unittest test_build_results.ReportTests.test_incremental_hcub_margins_use_each_cells_frozen_event_energy -v`
was RED: the first exported margin was `-46.20708608324741723692365398`,
while the GCC10/block1 event energies independently yield
`3.410536315066206486451892900`. The exporter reused the Hcub energy left in
`h` by the preceding comparison loop. The minimal fix selects the Hcub energy
for the current compiler/block inside the ordinary-comparison loop. The same
command then passed. Regenerated `results.json`, `tables.md`, and
`source-manifest.json` with
`python3 research/fir-paper/build_results.py --output-dir research/fir-paper`.
The scoped command `python3 -m unittest discover -s research/fir-paper -p
test_build_results.py -v` passed all 15 tests. Corrected margins are
`+3.410536315066206486451892900%`, `-0.1722020936602859443170901900%`,
`-4.284889921729122075968083230%`, and `-6.686822548045987384796790370%`
in GCC10/block1, GCC10/block64, GCC15/block1, GCC15/block64 order. The existing
manuscript's qualitative statement (Hcub costs more only at GCC10/block1) and
its cited GCC15/block64 value of 6.69% agree after correction; no manuscript
change was needed. Principal H_R margins and verdict are unchanged.

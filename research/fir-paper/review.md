# Independent Stage 1 scientific and numerical review

20 October 2026. Fresh read-only review; only this file is reviewer-owned.
Requested reviewer settings: Sol 6.1, high effort; backend routing is not independently observable.

**Verdict: accepted for scientific substance, numerical export and renderer integration within the stated case-study scope.** The current frozen numbers are correct. Findings below record discovered defects and their bounded correction, not a request to make H_R survive. Final page-by-page visual QA remains the coordinator's responsibility.

## Scientific assessment

H_R is a fair, useful, nontrivial **retrospective finite-case robustness assessment**. It asks whether an actual earlier four-cell decision survives one missing arithmetic-fair control. The manuscript explicitly says the hypothesis followed inspection of results (manuscript.md:72–79, 301–308, 534–540), distinguishes both historical comparators and ordinary transposition (55–62, 216–222, 380–395), and defines missing evidence as unavailable rather than rejection (310–320). It does not manufacture a universal transposition claim. The original protocol and subsequent join/final-decision records support this chronology.

Independent inspection of the frozen sharing rows confirms `cmsis64_unroll` is the lowest-energy historical nontransposed form among `direct64`, `cmsis64`, `cmsis64_unroll`, and `spec_direct` in all four cells. Hcub beats that comparator and wide specialized direct in all four, so the hypothesis is grounded in a real prior advantage. Safety of the two partials alone cannot predict the compiler-dependent instruction/event totals or opposite winning forms. The evidence supports a bounded baseline-sensitivity observation and partial emitted-code explanation; it establishes no new arithmetic method, broad implementation selector, physical energy winner, or substantial field-level novelty. Those limits are stated explicitly (81–88, 525–540, 561–600). This is a substantive empirical paper rather than an algorithm proposal; evaluator/publication acceptance remains external.

The exact 48 literal coefficients in partial-direct/kernel.c:33–80 independently yield L1 sums 12,778 and 59,731, bounds 418,709,504 and 1,957,265,408, and legal aligned sums 2,375,922,255 and −2,375,955,060. The widening at kernel.c:81 precedes addition; quantization at 18–25 implements one saturating floor. The main manuscript correctly separates this domain argument from finite output agreement. Its principal energy and diagnostic tables cover exactly five forms × four cells. Fixed-GCC15 and selectable-compiler denominators remain separate; 85.0151% is attribution of an **increase**, with 10,559.790252 nJ residual, not a predicted saving (473–510).

Fresh primary retrieval corroborated the XScale generation/physical-energy discussion ([D'Alberto et al.](https://users.ece.cmu.edu/~franzf/papers/hipeac07.pdf), §§2.2–4) and the exact six weights/configuration/MAPE ([Nikov et al.](https://arxiv.org/html/2301.12806v1), Table II). Primary indexed passages corroborated bit-true generation, FIR adaptation, and MCM register-pressure context in references [1], [2], [4]. Direct full retrieval of [1], [2], [4] was unreliable; detailed overlap therefore remains partly inherited, as manuscript.md:122–128 admits. No exhaustive novelty search was performed. The five references are relevant primary works and their role is appropriately limited.

## Required corrections found

1. **Medium — incomplete independent accounting join.** Initial build_results.py:125–135 checked only two rows, matching binary identity, and accounting-versus-explanation totals. A pure-helper fixture could replace the GCC15 accounting row with a copy of GCC10, or change accounting and explanation instruction totals together, and still be admitted. Require exactly the two distinct compilers and compare every accounting event against its selected partial row. Also reconstruct explanation deltas/cost from that admitted pair. Frozen CLI hashes prevent corrupted on-disk input from bypassing the gate, so this does not invalidate current results; it does violate the promised semantic helper contract.
2. **Medium — mutually consistent incorrect cycles admitted.** Initial build_results.py:118–119 compared serialized cycle totals only. Adding one to both a selected raw total and its verification total passed `build_report`, despite disagreement with the event formula. Reconstruct cycles independently before comparing summaries.
3. **Medium — duplicate test class silently removed coverage.** Initial test_build_results.py:32 and :50 used the same `SemanticValidationTests` name. The latter replaced the former, so unittest did not execute the duplicate-row test. Rename the class and verify the case is actually collected. Independent expected-value checks also used float conversions instead of the specified independent Decimal expressions; retain exact Decimal denominator assertions.
4. **Medium — subtitle promoted to a numbered section.** Initial ieee-filter.lua promotes all remaining H2 headers, including manuscript.md:3, to sections, before the Abstract. Combine the subtitle with the title or remove that header in rendering, so Introduction is the first numbered section. PDF reference conversion also discards Markdown link URLs through `stringify`; preserve links if they are intended as artifact access references.
5. **Low — diagnostic provenance and vector plots.** Initial exported rows name their raw source path, but stack/symbol diagnostics originate in independent-check/verification.json. Record that distinct provenance. Initial make_figures.py exports only PNG despite the spec's requested PDF/SVG option; supply vector artifacts beside the PNGs.

## Checks actually performed so far

- Read design spec, complete manuscript, exporter/tests/plot code, original protocol, partial kernel, join review, explanation claims/final decision, rendering template/filter/tests, and TDD log.
- Independently reconstructed all 20 cycle totals from events and all 20 modeled energies with literal Decimal weights: all agree exactly with the current exported rows.
- Recomputed all four historical/current margins, both compiler-selectable percentages, and attribution fraction. Results agree with manuscript/report; H_R passes `[false, false, true, true]` and is rejected.
- Ran three in-memory mutation probes without modifying evidence; each reproduced the false admissions described above.
- Ran the requested scoped unittest command during the worker's correction: 14 collected, four newly added RED validation failures, with duplicate-row coverage restored. Awaiting bounded GREEN re-review and one exact production CLI run after the worker completes.
- No target compiler, simulator, fresh performance experiment, Git operation, or manuscript edit was performed. Final page-by-page visual QA belongs to the coordinator.

## TDD and verification provenance

The log honestly records an initial full exporter draft before tests and its later reset. Subsequent red/green slices improve coverage but cannot retroactively make that initial draft test-first. Preserve that disclosure. Plain pytest renderer functions are not executed by unittest discovery; a successful import is not renderer test coverage. Run the renderer tests with pytest in the isolated environment (or an equivalent explicit harness) and report that command separately.

## Re-review status

The numerical worker corrected findings 1–3 and the diagnostic-provenance part of finding 5. Current build_results.py:103–110 reconstructs cycle/energy totals, :129–155 requires the distinct accounting pair and reconciles eight events and derived explanation costs, and :186–187 names the independent diagnostic source/array. The two semantic-test classes now have different names; the duplicate-row case is collected. Decimal assertions replace binary-float comparisons. Independent expected constants and the reviewer's separate literal-weight/formula reconstruction guard the denominators; these are meaningful checks rather than snapshots generated from the same implementation.

Fresh verification after correction:

- `python3 -m unittest discover -s research/fir-paper -p test_build_results.py -v`: **14 tests passed**. Coverage includes strict ties, invalid/missing rows, changed frozen bytes with existing-report preservation, accounting/delta/cycle defects, independent numerical expectations and byte-identical repeated output.
- `python3 research/fir-paper/build_results.py --output-dir research/fir-paper`: **exit 0**; executed once by this reviewer after correction.
- Repeated the reviewer's three independent mutation probes: incorrect mutually agreeing cycles, jointly altered accounting/explanation totals, and duplicate GCC10 accounting now each raise the appropriate `ValueError`.
- Generated both plots twice into separate temporary directories: all four PNG/SVG artifacts are **byte-identical**. make_figures.py uses fixed SVG IDs and suppresses date metadata.
- Intermediate renderer snapshots failed first with an f-string syntax error and then an undefined highlighting environment. Those failures were reported and corrected; the final run `FIR_PAPER_TECTONIC=/tmp/fir-paper-tools/tectonic /tmp/fir-paper-render-env/bin/python -m pytest research/fir-paper/test_render_paper.py -q` **passed both tests**, with neither skipped. The fixture includes the real blank-line title/subtitle spacing, a table, C listing, PDF content extraction and existing-PDF preservation on a missing image. The tests now use the active Python and an environment/PATH-selected Tectonic rather than fixed temporary paths.
- Current renderer preserves bibliography links, combines the actual subtitle with the title, and uses stable distinct figure labels. Extracted the actual nine-page PDF: its Abstract retains the four margins and attribution limit; Introduction is the first numbered section. This content check is not a substitute for visual inspection.

No substantive manuscript revision is requested. Main prose is approximately 4,159 words excluding headings, code, tables/captions, references and appendices, meeting the agreed size target with an actual argument, four-cell evaluation and emitted-code evidence. The manuscript is suitable as a bounded IEEE-style empirical case study. The README now documents separate numerical and renderer commands and reproduction levels. An additionally notified minor subsection-prefix problem is corrected in current ieee-filter.lua:64, which removes the complete dotted number before IEEE numbering. Final regenerated PDF layout, artifact links and completion of the rendering work log remain coordinator checks.

## Coordinator resume audit

The preceding independent review is preserved as received. Subsequent coordinator
inspection found a stale loop variable in the auxiliary Hcub-versus-ordinary
transposition JSON metrics: GCC15/block64 Hcub energy was reused in the first
three cells. The principal results, H_R verdict, tables, figures and reviewed
manuscript statements were unaffected. A Luna worker added a literal-energy
four-cell Decimal regression, observed RED, and corrected the lookup; a fresh
coordinator run passed all 15 numerical tests. The TDD log records exact commands.
This correction is a coordinator/worker check, not a new independent scientific
review or a claim that the preceding review detected this defect.

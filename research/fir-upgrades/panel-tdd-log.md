# Task 4 panel TDD log

## RED

- Added contract tests before `panel.py`; `python3 -m pytest -q research/fir-upgrades/test_panel.py` failed during collection with `ModuleNotFoundError: No module named 'panel'`.
- After the first implementation, the recipe, exact-interval, input-identity and direct-generator tests passed. The prepare test was blocked because the production Hcub graph set had not yet been frozen. I prepared the production stage once, then temporary test stages copied and hash-checked those exact files rather than invoking Hcub.
- The first UBSan host run found a ctypes harness guard failure on `native_lp1800/wide_direct64/block1`. Inspection showed the harness could align the state pointer to the start of its backing buffer and place the leading canary before the allocation. This was a harness defect, not a generated-kernel result. The allocator now aligns after an eight-byte reserved prefix and checks both guards lie inside the allocation; an explicit allocator test covers that range.
- A later public-input validation test was added first and failed because coefficient `1.5` was accepted by integer coercion. Group boundaries had the same potential truncation. Both are now rejected before source generation.

## GREEN

- Pinned recipes reproduce all three required little-endian coefficient hashes, L1 values, tight full-sum intervals, legal first/balanced cuts and extremal windows. The LCG full and ADC input streams reproduce the specified prefix and hashes.
- `prepare_panel()` freezes 288 unique case identities and 36 generated wrapper/header pairs. The three Hcub stdout graphs were generated once each with the unchanged vendored executable; later prepares verify the recorded command, fundamentals, executable/archive provenance, stdout hash and stderr hash and reuse the saved bytes.
- Generated direct bodies preserve tap order, int32 multiplication before widening, separate group widening, one final floor/saturating quantizer and retained history. Capacity is a documented caller precondition; no per-call runtime capacity branch is emitted.
- Final scoped tests: `python3 -m pytest -q research/fir-upgrades/test_panel.py` → **9 passed**.
- Final host checks: 28 unique generated direct/transposed shared-library builds under GCC `-O2 -fsanitize=undefined -fno-sanitize-recover=undefined`; 140 stream checks passed. Every call checks newly emitted outputs, full consumed-prefix state, state canaries and output guards. Streams cover full and ADC masters, extrema, `[-1]+zeros`, mixed capacity-64 partitions `1/64/3/16`, and a separate warmup call ending exactly at sample 64 followed by the 1025-sample suffix without state reset. Quantizer threshold and negative-floor boundaries are explicit unit checks.

## Evidence limits and admission state

- Host UBSan applies to generated direct/transposed C only. Unmodified CMSIS is not host-emulated. Its exact source revision and source/header hashes, pair/full-domain arithmetic bounds, reversed coefficients and helper obligations are recorded separately.
- CMSIS packed signed shifts depend on pinned GCC implementation semantics; portable ISO-C validity is not claimed. Native `cmsis32_unroll` block64 remains **pending** unresolved pointer-object aliasing admission. Block1 source gating is recorded as a distinct unreachability argument. Task 5 still owns effective macro/binary identity, target correctness, and memory/frame evidence.
- No target compilation, target execution, performance measurement, cost selection, or resampling occurred. The protocol reports zero Task 4 performance runs.

## Admission fix round 1 (2026-10-20)

### RED

- `test_public_generator_enforces_frozen_form_and_cut_eligibility` failed because the public API returned a wide filter's `cmsis32_unroll` source instead of rejecting the ineligible form.
- `test_recorded_or_temporary_missing_graph_fails_without_acm` failed because deleting a recorded `.txt` graph reached the Hcub subprocess. The test guards the actual executable invocation; the corrected regression also covers missing recorded stderr bytes.
- `test_prepare_rejects_changed_frozen_dependency_identity_before_rewrite` failed because a temporary stage with a changed recorded legacy-helper hash was silently rewritten and accepted.

### GREEN

- Public generation resolves the exact coefficient hash before dispatch, checks the frozen per-filter form set, and requires each form's named group policy. Native fast-CMSIS source remains generatable at block 64 with its pending aliasing admission recorded separately.
- A recorded graph manifest now requires every recorded stdout/stderr file and exact command/hash identity. Partial temporary roots fail closed; only a genuinely unrecorded production stage may invoke Hcub. Temporary roots copy the verified frozen graph bytes.
- Preparation checks the pinned legacy helper hash, the protocol and checksum, CMSIS tracked working-tree content against pinned HEAD, the separately pinned Core header tree, and recorded CMSIS source/header hashes before writing. Repeated preparation also compares existing design, input, certificate, protocol, source manifest and generated source bytes before replacing any of them.
- Regression RED/GREEN: the focused round-1 tests first failed **3/3** with the reviewed behaviors; after the fix, the focused tests passed. Full scoped suite: `python3 -m pytest -q research/fir-upgrades/test_panel.py` → **13 passed**.
- Production `prepare_panel` reused its recorded graphs, returned the original protocol SHA256 `d2b85b2580ec551efcbc457159ff9237482aa2f146417ed236bbd0c0aeb8646c`, and reported zero performance runs. The coordinator's 85-file frozen payload snapshot matched exactly after prepare.
- No graph generation, target compile/execution, performance run, host UBSan build, or vendor/helper mutation occurred.

## Admission fix round 2 (2026-10-20)

### RED

- Added `test_production_partial_graph_set_without_manifest_fails_without_writes`, using a temporary root designated as production, with the manifest/native artifacts absent, a wide graph retained, and a protocol marker. Before the guard, it failed because the guarded subprocess observed an `acm` invocation on the missing native graph.
- Added `test_previously_prepared_production_with_no_graphs_fails_without_acm`, with a temporary production root containing a protocol marker and no graph artifacts. Before the guard, it failed because the guarded subprocess observed an `acm` invocation.
- Both regressions snapshot every file in the isolated root and assert the snapshot is unchanged after rejection.

### GREEN

- Graph admission now decides production freeze state globally, before entering the per-filter loop. If the manifest is absent, any expected stdout/stderr artifact or an existing protocol makes the stage frozen/incomplete and causes rejection. Manifest existence, including an empty manifest, makes outputs recorded and therefore requires complete per-filter records and bytes.
- The two regressions pass after the guard. Final scoped suite: `python3 -m pytest -q research/fir-upgrades/test_panel.py` → **15 passed**.
- Snapshot check covered 95 frozen payload/historical files (85 Task 4 files plus 10 earlier-study files): no changed or missing hashes. No graph generation, target work, or host UBSan was performed.
- Added `test_empty_production_graph_manifest_is_recorded_and_fails_closed`; it first failed when the admission bit was temporarily reverted to manifest truthiness, because `{}` reached `acm`. Manifest existence now governs recorded status. Final scoped suite including this case: **16 passed**.

## Task 5 provenance admission fix (2026-10-20)

### RED

- Replayed the reviewed concrete mutation against a temporary import of the pre-fix verifier and a copied real direct correctness row. Replaced effective dependency, dependency-hash, and macro documents by `{}` and rehashed the three artifacts. The prior verifier returned `admitted` with `dependency_count=0`.
- Added copied real direct and CMSIS regressions for empty evidence documents, jointly removed `probe.c` translation units, a missing per-TU required header, and rewritten copied-header bytes. Added CMSIS removal of `cmsis_gcc.h` from every C translation unit plus the hash inventory, and a rewritten local dependency digest with its artifact digest updated.

### GREEN

- Independent source admission now requires the exact translation-unit set (`probe.c`, `firmware.c`, `startup.s`, plus `library.c` for CMSIS), nonempty C macro/dependency records, and empty startup assembler records. Each C translation unit must retain its expected local source/header dependencies. CMSIS C translation units must also retain all pinned common headers; the library unit must retain the correct pinned FIR source.
- Dependency hashes bind copied case-local files to their actual bytes and external CMSIS/core files to the frozen protocol source hashes. These checks use normalized recorded paths and work in a relocated saved-evidence tree.
- Scoped verification: `python3 -m pytest -q research/fir-upgrades/test_panel_run.py research/fir-upgrades/test_panel_verify.py research/fir-upgrades/test_panel.py` → **68 passed**. Saved performance audit: **288 identities, 280 admitted, 8 unavailable, 0 failed**. Saved correctness audit: **72 identities, 70 admitted, 2 skipped, 0 failed**. No target tools or measurements were run.

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

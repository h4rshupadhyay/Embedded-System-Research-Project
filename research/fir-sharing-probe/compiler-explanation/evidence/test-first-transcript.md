# Test-first run record

Command: `python -m unittest discover -s research/fir-sharing-probe/compiler-explanation -p 'test_*.py' -v`

1. Before `analyze.py` existed: exit 1, `setUpClass` raised `FileNotFoundError` for `analyze.py`.
2. After the first implementation: exit 1, 3 tests run with 1 failure. `test_disassembly_excludes_literal_pool_and_data` found an extra `abcdef00` mnemonic from a raw `input_data` line.
3. After rejecting raw data bytes: exit 0, 3 tests passed.
4. After adding the direct-SP path fixture: exit 1, 4 tests run with 1 error. `AttributeError: module 'fir_compiler_analyze' has no attribute 'direct_sp_events'`.
5. After implementing the path count: exit 0, 4 tests passed.
6. Independent review found that the evidence-writing loop reused GCC 15's final `sp_path` for both case certificates. Added `test_generated_certificates_keep_each_compilers_path`; before the fix, exit 1 with 5 tests run and 1 failure: GCC 10's generated certificate reported `(63, 84)` instead of `(9, 9)` direct SP reads/writes per call.
7. Staged each compiler's own path with its case data; final suite passes 5 tests.
8. Reviewer requested an evidence hash for the final `assembly-notes.md` annotation. New tests first failed: generated report lacked the hash (`KeyError`) and absent annotation was accepted. The analyzer now requires the annotation before writing and records its SHA256; final suite passes 6 tests.
9. A Git packaging review found that Windows CRLF output changed generated JSON bytes when staged. Added a test that first failed because `accounting.json` contained CRLF. The writer now fixes LF newlines for the report, command record and both site certificates; final suite passes 6 tests.

The final command and analyzer command were rerun after all code changes; see the delivery message for the final output. This record is a development transcript, not source evidence for dynamic counts.

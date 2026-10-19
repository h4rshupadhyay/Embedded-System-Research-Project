# Fresh read-only review and handling

The fresh reviewer was requested as `gpt-6-astra` with high reasoning effort,
after the Sol analyzer and Astra assembly workers finished. The collaboration
runtime did not expose independent model or effort telemetry, so actual routing
is **unverified**. The reviewer edited no files and did not delegate. The two
earlier workers were requested as `gpt-6-sol`/high and `gpt-6-astra`/high;
their actual runtime routes are likewise unverified. The two-active-worker
limit and three-child-task limit were observed.

## Findings and disposition

| Severity | Finding | Handling |
|---|---|---|
| High | `analyze.py` initially reused GCC15's final `sp_path` while writing GCC10's `site-classification.json`. The GCC10 certificate incorrectly claimed 63/84 direct-SP reads/writes and omitted unused `0x08000406`, though row totals were correct. | Analyzer worker staged each compiler's own path; a regression test reproduced the failure before the fix. Final GCC10 certificate says 9/9 and excludes `0x08000406`; GCC15 says 63/84. |
| Medium | The supporting `assembly-notes.md` annotation was missing from the accounting evidence hashes. | Analyzer now requires and hashes the note; the final manifest has 29 verified entries. |
| Low | `findings.md` lacked a component-delta table. | Added a table that reconciles with `accounting.json`. |
| Delivery | Git ignores `firmware.bin` and `firmware.map` in both case evidence directories. | The owned-files-only commit force-adds all four files and checks that manifest paths are tracked. |

The reviewer's final verdict was **accepted after corrections**, with no
remaining substantive accounting or causal-overclaim issue. The reviewer
independently checked seven frozen input identities, all 34 two-case archive
artifacts, all eight counter sums for both rows, 514 reference outputs, both
histories, guards, state sizes, compiler flags and versions, and 796/958
disassembly instruction/literal rows against the binaries. The reviewer
enumerated all ten syntactic quantizer paths in each body and found the same
once-only direct-SP sites on each path. The 257 calls all pass `b=1`; the
GCC10 `b=0` store is excluded, and the 47-iteration history loop has no
direct-SP accesses. Marker/setup/printing boundaries, ABI saves, literal
pools, partial sums and wide reduction were also checked.

The reviewer first ran the read-only fixture suite with four tests passing,
then checked the final 29 hashes, certificates and sums and reproduced the
analyzer's final JSON with writes intercepted in memory. The coordinator's
final six-test run and analyzer command are reported in the delivery result.
The reviewer did not rerun two later tests that create temporary files. The
remaining 10,667-instruction and 131-branch delta, and the compiler-pass cause
of stack placement, remain unresolved.

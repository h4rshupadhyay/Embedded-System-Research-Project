# Task 5 RED/GREEN and verification log

Date: 2026-10-20. This log distinguishes test-first regressions, fixture
authoring corrections, real campaign outcomes, and validation commands.

## Test-first implementation evidence

- The Task5 runner/verifier import and panel CLI routing tests were run RED
  before implementation. The `panel.py measure` dispatch was then added.
- State-layout test expected AAPCS size 98 for the native b1 state; it went RED
  when the parser aligned fields incorrectly, then GREEN after field alignment
  was fixed. Independent ABI reference sizes are saved in
  `.superpowers/sdd/2026-10-20-fir-paper-upgrades/task-5-root-abi-sizes.json`.
- Toolchain identity, `.su`/disassembly call-chain, and complete allocated
  section range tests were introduced RED and passed after fixes for the
  Cortex-M0 `libgcc` multilib, tail/internal CFG edges and orphan/overflow
  sections. Real attempt-002 was rejected for generic libgcc; the attempt was
  retained and not edited.
- New performance selector test requires the exact first two frozen protocol
  cases and rejects case three. Initial test data mistakenly changed case one
  into case two, so the failure correctly showed that the supposedly invalid
  identity was valid; the test was corrected to use an unknown regime. This was
  a test-data correction, not claimed as feature RED.
- Exact event-to-cost serialization test first used a primary opcode row with
  secondary histogram bins, which the independent raw decoder properly
  rejected. The synthetic fixture was corrected; this is recorded as fixture
  repair, not feature RED.
- First real performance CLI run completed/admitted attempt-001 but checkpoint
  serialization raised `TypeError: Object of type Decimal is not JSON
  serializable`. Added `test_checkpoint_json_preserves_decimal_estimands_as_exact_strings`;
  it first failed on `panel_run.dump`, then passed after Decimal values were
  encoded as exact strings. The run was not repeated: the same attempt-001 raw
  files were independently re-audited and reused for the checkpoint.
- Added exact quantizer-threshold test over absolute sample range `[1,3)` with
  positive/negative exact sums; it passes and checks the inclusive source
  predicates at `+/-1073741824`.
- After full-campaign release, the all-identity selector regression first went
  RED at the old first-two guard, then passed for all 280 executable identities
  while rejecting the eight exact pending fast block64 cases. A real saved
  performance-row mutation test then went RED because the independent adapter
  ignored a rewritten serialized clamp count; it passed after the verifier
  compared saved counts with exact measured-region sums.
- The first full verifier CLI reached the unavailable inventory formatter and
  failed with `KeyError: 'filter'` because unavailable rows store identity
  fields under `identity`. The formatter was corrected and the full independent
  audit then passed. No target identity was rerun for this report-layer failure.

## Commands and outcomes

Correctness campaign had previously completed 70 admitted / two skipped / zero
failed identities. Its independent audit is
`verification/correctness-audit.json`; Task5 CLI uses the same immutable saved
gate attempts and the verifier has a `--correctness-only` mode.

Latest focused suite:

```text
python3 -m pytest -q research/fir-upgrades/test_panel_run.py research/fir-upgrades/test_panel_verify.py
42 passed
```

Released first case:

```text
python3 research/fir-upgrades/panel.py measure performance --identity native_lp1800/wide_direct64/gcc10/1/adc/startup
status=passed; raw=build/panel/performance/native_lp1800__wide_direct64__gcc10__1__adc__startup/attempt-001
```

Released second case:

```text
python3 research/fir-upgrades/panel.py measure performance --identity native_lp1800/wide_direct64/gcc10/1/adc/post_startup
status=passed; raw=build/panel/performance/native_lp1800__wide_direct64__gcc10__1__adc__post_startup/attempt-001
```

Both attempts have independently admitted whole-prefix output/state/guard
traces, frozen source/fixture and binary binding, exact raw histogram/markers,
serialized compiler/options/macros/dependencies, memory sections and
conservative live-stack chain. Checkpoint is
`build/panel/performance/checkpoint-results.json`; it contains the first two
frozen identities. Full campaign results and audits are in
`panel-results.json`, `panel-summary.json`, `panel-summary.md`,
`verification/independent-audit.json`, and
`verification/scientific-evidence-manifest.json`. The final inventory is
288 rows: 280 admitted, eight unavailable, zero failed. No admitted logical
performance identity was run twice.

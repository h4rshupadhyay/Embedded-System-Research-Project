# FIR Missing-Baseline Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans when implementing this plan. The assignments below are for the user's human peer and the user with Codex; this document does not dispatch agents or start implementation.

**Goal:** Determine whether the apparent transposed-FIR advantage survives an equally range-specialized direct implementation.

**Architecture:** Two independent workstreams share frozen inputs and a result format, with separate file ownership. The peer builds and measures the missing baseline. The user with Codex independently prepares verification, comparison analysis and contribution assessment. Only the final comparison requires both deliverables.

**Tech Stack:** C11, Python, host GCC/UBSan, existing Arm GCC 10.3.1 and 15.2.Rel1, existing audited Thumbulator and CPU cost models.

**Spec:** [Pursuit audit](../../../research/fir-sharing-pursuit-audit.md), especially “Minimal decision gate”; [existing probe protocol](../../../research/fir-sharing-probe/PROTOCOL.md).

**Progress, 20 October 2026:** Task 2 is independently complete and reverified:
26 tests passed; 24 historical rows and 6,168 output comparisons checked from
saved raw evidence; regenerated reports match the saved files exactly. See the
[checker handoff](../../../research/fir-sharing-probe/independent-check/README.md).
**Final join completed, 20 October 2026:** The peer kernel and runner were merged.
The final expanded host suite passed three UBSan tests. Four target performance
runs and two signed-edge runs passed 1,750 outputs, history and guards; all four
performance rows passed independent verification. The checker now passes 27
tests, including an explicit adapter for the delivered `compiler_flags.compile`
layout. Manual arithmetic and four-build assembly review is recorded in the
[completed join](../../../research/fir-sharing-probe/independent-check/join-review.md).
Partial direct wins both GCC 10 configurations; demand Hcub wins both GCC 15
configurations. The fixed gate is complete; algorithmic novelty is unestablished.

## Global constraints and shared inputs

- One filter: `speech_minphase48` from `research/fir-baseline/selection-design.json`. No coefficient changes or partition search.
- Guaranteed input domain: full int16, `[-32768,32767]`. Timed input: the first 257 saved `inputs.adc_raw` values; this small actual stream does not relax the domain guarantee.
- Fixed zero-based coefficient groups: `[0,2)` and `[2,48)`. Their absolute-sum bounds are `418709504` and `1957265408`, both below `2147483647`.
- Reference: `clip_int16(floor(exact FIR sum / 32768))`, with zero initial history. Combine partial sums exactly before the single final quantizer; retain every requested output.
- Four performance configurations: two existing compilers × block sizes `1` and `64`; Cortex-M0 Thumb, `-O2`, no LTO. Include complete recurring state/call/tail costs under the existing measurement boundary.
- Use the existing Arm-table zero-wait-state, single-cycle-MUL timing estimate and 20 MHz/prefetch-off/zero-wait CPU energy model. Report estimates, not measured board energy.
- Keep existing `probe.py`, its results, baseline sources and original findings unchanged during parallel work. Write new artifacts under the owned directories below.
- Frozen design SHA256: `bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f`.
- Frozen sharing-results SHA256: `57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa`.

## Review focus

1. Casting after `partial0 + partial1` is too late: widen an operand **before** addition. The full sum can exceed int32.
2. Negative output division must floor correctly; intermediate truncation or saturation changes the reference.
3. Block64 ends with a one-sample call for the 257-sample stream; history must remain correct.
4. Performance comparisons must use identical input/coefficient hashes, compiler settings, numeric guarantees and counting boundaries.
5. Correct outputs do not prove safe arithmetic or a strong contribution: inspect range certificates, target instructions and existing-method overlap separately.

---

## Task 1 — Peer: implement and measure the exact partial-sum direct baseline

**Own directory:** `research/fir-sharing-probe/partial-direct/`.

**Create:** `kernel.h`, `kernel.c`, `run.py`, `test_kernel.py`, `results.json`, and `notes.md`. Generated build artifacts stay inside this directory's `build/`. Read/import existing measurement helpers as needed; do not edit shared runners.

**Consumes:** The frozen design/input and measurement conventions above; existing [runner](../../../research/fir-sharing-probe/probe.py) and [baseline instructions](../../../research/fir-baseline/README.md).

**C interface:** Match the existing fixture's five-function adapter:

```c
typedef struct { int16_t history[48 + BLOCK]; } ProbeState;
void probe_init(ProbeState *state);
void probe_process(ProbeState *state, const int16_t *input,
                   int16_t *output, uint32_t block_size);
int64_t probe_get_state(ProbeState *state, uint32_t index);
unsigned probe_state_bytes(void);
```

`BLOCK` is 1 or 64 for target builds; host mixed-partition tests use capacity 64. Getter indices `0..46` return chronological retained input history, matching the existing direct wrapper. Coefficients/tap count are compile-time constants, matching `spec_direct`; use the existing unrolled direct organization with the two fixed partial sums as the only substantive arithmetic change.

- [x] Peer recorded tests-first implementation and the expected initial missing-kernel failure; signed edges, quantization boundaries, mixed blocks, history and guards are covered.
- [x] Two int32 accumulators widen before final int64 addition and quantize once; prefix/product/final range review is recorded in the join.
- [x] Final expanded suite passed all three tests with nonrecovering UBSan; log retained in the independent-check directory.
- [x] Exactly four performance configurations and two separate signed-edge runs completed; raw evidence and diagnostics archived.
- [x] All four assemblies reviewed for native-width partials and final wide reduction; addresses recorded in the join.
- [x] Peer sources, runner, notes and completed `results.json` delivered; mixed outcome reported.

**Done when:** Four reproducible performance rows exist, all correctness gates pass, and the exact arithmetic proof and emitted-code check are documented. No favorable speedup is required.

If the peer develops on another computer, they can implement and run host correctness checks there. Run the final four target measurements in the existing pinned environment here, or reproduce that environment using the baseline README. Sharing the peer's owned directory is sufficient for code handoff; do not assume ignored toolchain/build directories travel with an ordinary Git checkout.

## Task 2 — User + Codex: independent verification, analysis and contribution assessment

**Own directory:** `research/fir-sharing-probe/independent-check/`.

**Create:** `check.py`, `test_check.py`, `comparison.md`, and `positioning.md`. The first two may read Task 1 artifacts once delivered. No edits to the peer's implementation/results.

**Consumes:** Existing frozen sharing results immediately; Task 1's result format below when available. Implement an independent arbitrary-precision reference instead of importing the peer's expected-output computation.

- [x] Independently reproduce the two coefficient-group bounds and establish the expected full-sum overflow case. Specify reference outputs/history for mixed partitions and signed boundary cases.
- [x] Build the checker against existing saved `spec_direct`, `trans_const` and `trans_hcub_demand` artifacts for the four matching configurations. Verify metadata, output/history, raw events, cost reconstruction and hashes without rerunning the full matrix.
- [x] Add rejection tests for a changed output, shortened history, altered input identity and a cost value inconsistent with saved raw counters. These tests must fail on the altered artifacts.
- [x] Prepare a comparison that accepts one new `partial_direct32x2` row per configuration. Compare against the strongest previously tested nontransposed control, ordinary mixed-width transposition and dependency-driven Hcub. Report code/state/frame costs alongside cycles and model energy. Until peer results arrive, mark the new values pending; do not invent placeholders that look measured.
- [x] Read the closest primary sources already identified in the pursuit audit. In `positioning.md`, map each candidate contribution to existing work, the specific additional evidence, and its limitations. Distinguish an empirical finding from a new algorithm; separate model estimates from physical energy.

**Done independently when:** The checker passes existing artifacts and rejects deliberately altered ones, the comparison is ready to consume peer results, and the cited positioning note is complete. The peer does not need to finish before this work starts or reaches that milestone.

## Shared result format

Task 1 writes `partial-direct/results.json` with `stage: "post-audit missing-control"`, frozen design/results hashes, compiler identities/flags, explicit cost-model parameters and a `rows` array. Reuse existing row names where possible:

`compiler`, `filter`, `variant`, `maximum`, `block`, `samples`, `instructions`, `mul`, `ram_reads`, `ram_writes`, `flash_reads`, `flash_writes`, `taken_branches`, `bl`, `arm_zero_ws_cycles`, `estimated_cpu_energy_nj`, `state_allocation_bytes`, `stack_usage`, `outputs_verified`, `retained_state_verified`, `guards_verified`, `directory`, `artifacts`.

Fixed row identifiers: `filter="speech_minphase48"`, `variant="partial_direct32x2"`, `maximum=32768`, `samples=257`; compiler names `gcc10`/`gcc15`. Paths in `directory` are relative to `partial-direct/`; artifact hashes identify the source, binary, disassembly and raw output/event files used. Preserve the existing `O:`, `H:`, `G:` and `M:` output encoding so Task 2 can independently decode them. Correctness-only runs belong in a separate array.

**Current checker compatibility:** The implemented reader uses the existing
fixture's exact `firmware.*` filenames, literal decimal `input_data` array and
`BLOCK`/`SAMPLES` definitions. Its accepted metadata and artifact conventions
are documented in the [checker README](../../../research/fir-sharing-probe/independent-check/README.md#once-the-peer-returns).
The general schema above permits other layouts; those require an explicit
adapter when the peer evidence arrives. Task 2 completion does not certify
compatibility with an unseen peer implementation or replace the final manual
arithmetic/assembly review.

## Final join — after both tasks, not a third parallel workstream

Run the independent checker on the peer's four rows, inspect discrepancies together, then fill the comparison and revise the research decision. If the direct partial-sum baseline removes the apparent benefit, revise the headline. If a useful benefit/tradeoff survives, write the bounded contribution statement with its explanation and closest-work distinction. Wider bank claims later require equally fair controls for other wide-sum cases; that expansion is outside these two tasks.

The handoff is published in [Embedded-System-Research-Project](https://github.com/h4rshupadhyay/Embedded-System-Research-Project/tree/research/exact-fir-baseline-handoff), on `research/exact-fir-baseline-handoff`. Create separate working branches from that branch; see the [peer prompt](../../peer-sol-6.1-handoff.md). The original workspace exposes a virtual read-only `.git` directory, so publishing uses a separate normal checkout. Do not attempt to initialize or commit through that virtual directory.

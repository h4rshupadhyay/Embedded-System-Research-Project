# FIR Compiler Explanation Parallel Work Plan

> **For agentic workers:** Use the applicable execution workflow when the human starts an assignment. This document assigns two human workstreams; it does not start them. Read the shared contract before delegating. Each workstream has its own bounded model routing below.

**Goal:** Explain the existing GCC10/GCC15 block1 partial-direct cost difference and independently assess what that explanation adds to the college paper.

**Architecture:** The peer owns binary/assembly analysis. The user owns an independent evidence checker and paper-claim assessment. Both start from the same frozen evidence; only verification of the peer's completed accounting waits for delivery.

**Tech Stack:** Python standard library, saved Thumb disassembly/ELF/maps/events, existing independent checker; optional diagnostic replay of the same two binaries in an isolated copy of the pinned simulator.

**Spec:** [Post-join research assessment](../../../research/fir-post-join-research-assessment.md), especially “Single most useful bounded next step”; [completed comparison and arithmetic review](../../../research/fir-sharing-probe/independent-check/join-review.md).

## Assignments and file ownership

| Person | Question | Owned directory | Independent milestone |
|---|---|---|---|
| Peer | Which generated-code differences account for the GCC15 block1 direct overhead? | `research/fir-sharing-probe/compiler-explanation/` | Reproducible accounting, annotated assembly, honest attribution limits and review |
| User + agent | Is that accounting internally consistent, and what claim can the paper defend? | `research/fir-sharing-probe/explanation-check/` | Tested checker against hand-calculated fixtures and frozen totals; claim/evidence note ready before peer delivery |

Prompts: [peer](../../peer-sol-6.0-compiler-handoff.md), [user](../../user-fir-explanation-handoff.md).
Shared sources, old results, existing checkers and the two other owned directories
are read-only. Each worker writes only the files its coordinator assigns. Parent
coordinators own their workstream's final narrative and integration.

## Shared inputs and scope

- FIR-only, simulator-only college empirical study; publication optional. The professor is the final evaluator, not an available project guide.
- Analyze only `partial_direct32x2`, `speech_minphase48`, full-int16 guarantee, **block 1**, GCC10/GCC15, `-O2`, no LTO, 257 saved samples and zero initial history.
- Preserve the fixed groups `[0,2)`/`[2,48)`, coefficients, exact floor/saturating quantizer, binary bytes and measurement boundary.
- Existing block64 and transposed rows supply context only. Performance rankings remain the completed four-row comparison. This assignment adds explanatory evidence, not replacement benchmark rows.
- The saved aggregate event logs contain totals, not a per-PC execution history. Static opcode counts cannot establish dynamic counts. A stack access alone does not identify a register-allocation spill.
- Prefer saved evidence. If needed, replay only the same two block1 binaries for diagnostics. A separate logging-only simulator build may live in the peer's directory; preserve its upstream commit, source diff, build commands and hash. Reconcile outputs, history, guards and aggregate events before using its trace. Instrumentation is diagnostic and is not a new performance model.
- Keep target kernels, toolchains, shared simulator, frozen results and existing checker unchanged. No partition search, compiler-flag sweep, new filter bank or optimizer belongs to this task.
- An explicitly unresolved causal component is an acceptable outcome. A complete explanation, favorable result, compiler bug or novelty claim is not assumed.

## Frozen identities

| Input | SHA256 |
|---|---|
| `research/fir-baseline/selection-design.json` | `bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f` |
| `research/fir-sharing-probe/results.json` | `57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa` |
| `research/fir-sharing-probe/partial-direct/results.json` | `eb53d3e556a6f8444742856b8c45a7d3236f443fed6cc0312010b2840095dc4f` |
| `research/fir-sharing-probe/partial-direct/kernel.c` | `5832b52eaf1d5eb76e8087d47307feeccf74809cc0f22b288d111505851501cd` |
| Six-case target evidence archive in `independent-check/` | `8aa24f417ff266a2be2a850750defe06d8cbc46766b03d0ba67639f0a154cb83` |
| `partial-direct/build/target/gcc10-b1/firmware.bin` | `07fd7023d12ead52fee14a266c647627d664f37c18c234a0b41e2f226f143a6a` |
| `partial-direct/build/target/gcc15-b1/firmware.bin` | `114041b0f03a20c34a9c8a37b147116dff9f74c3c321bd2af4d7709d710e3470` |

Restore the six-case archive as described in [join-review.md](../../../research/fir-sharing-probe/independent-check/join-review.md).
An ordinary clone of the older handoff branch is insufficient. Pull the current
`research/fir-independent-check` branch, which includes the completed results,
these assignments and the raw-evidence archive. An offline working-tree snapshot
is also supported; its manifest records included file identities. The manifest
is specific to snapshot delivery and is not required for a Git clone. Stop an
affected comparison on a hash mismatch; report which input is missing or different.

## Reference totals

These totals are copied from the frozen partial-direct result. Read and verify
their raw `firmware.stderr` sources; copying this table is not verification.

| Counter | GCC10/block1 | GCC15/block1 | GCC15 minus GCC10 |
|---|---:|---:|---:|
| instructions | 198670 | 242490 | 43820 |
| mul | 2827 | 2827 | 0 |
| ram_reads | 29304 | 43182 | 13878 |
| ram_writes | 17225 | 36500 | 19275 |
| flash_reads | 1032 | 1032 | 0 |
| flash_writes | 0 | 0 | 0 |
| taken_branches | 13622 | 13753 | 131 |
| bl | 258 | 258 | 0 |

Timing-estimate totals are 273733/350968, delta 77235. CPU-energy model totals
are 266394.093850/336863.793775 nJ, delta 70469.699925 nJ.
Keep these aggregate costs separate from measured board energy or wall time.

## Peer output contract

Create `accounting.json`, `analyze.py`, `test_analyze.py`, `assembly-notes.md`,
`findings.md`, `review.md`, and any evidence under `evidence/`, inside the peer's
owned directory. Use `build/` for regenerable temporary files.

`accounting.json` uses this interface:

```text
schema_version: 1
stage: "post-join compiler explanation"
source_results_sha256: <frozen partial-direct results hash>
evidence: {<relative filename inside compiler-explanation/>: <sha256>, ...}
rows: exactly two objects, one per compiler:
  compiler: "gcc10" | "gcc15"
  block: 1
  binary_sha256: <hash above>
  method: "saved-evidence" | "trace-reconciled"
  totals: {instructions, mul, ram_reads, ram_writes,
           flash_reads, flash_writes, taken_branches, bl}
  components: list of:
    name: one of the names below; each present exactly once
    events: same eight integer counter fields
    basis: "dynamic-trace" | "exact-control-flow" | "residual"
    evidence_refs: list of relative filenames from evidence
  static_diagnostics:
    probe_process_symbol_bytes: integer
    compiler_frame_bytes: integer
    sp_relative_instruction_sites: integer
  causal_status: "supported" | "partial" | "unresolved"
  limitations: list of strings
```

Component names: `stream_wrapper`, `copy_in`, `convolution`, `quantize_store`,
`history_copy`, `function_entry_exit`, `unattributed`. Define boundaries by
compiler-specific PC ranges/basic blocks in hashed evidence. Assign an executed
instruction and its events to one component. `mul` is a subset of `instructions`;
the categories partition each counter independently, not eight disjoint event kinds.

For each counter, sum(component events) must equal the frozen total exactly.
Unresolved counts belong to `unattributed` with basis `residual`. Components with
no demonstrated counts use zero events and explain that in the findings; zero
does not assert that the operation was absent. Never fill a missing dynamic
count by multiplying static sites by 257 unless exact execution frequency and
every relevant branch/loop path are established.

Retain source-value/stack-slot annotations separately in `assembly-notes.md`.
Use “stack-resident temporary” unless value flow or compiler evidence establishes
an actual spill. The checker validates accounting consistency; it cannot certify
that a plausible PC-range label is a causal explanation.

## Completed execution, 20 October 2026

Peer checkpoint `7315427` was merged by `4a72620` after the peer's quota ran
out. The actual accounting passes independent admission (two rows, 29 evidence
hashes), and manual binary/control-flow/value-flow review accepts partial
attribution. All 64 tests pass. Extra direct-SP transfers explain all additional
RAM traffic and 85.0151% of the modeled energy increase; remaining costs and
compiler-pass cause are unresolved. See
[final decision](../../../research/fir-sharing-probe/explanation-check/final-decision.md)
and [takeover/review record](../../../research/fir-sharing-probe/explanation-check/review.md).
The fresh takeover Astra attempt hit its usage limit; a disclosed Sol 6.0/high
fallback completed the independent review under the policy below. No new target
measurement was made. The bounded investigation stops here.

## Task 1 — Peer: generated-code explanation

- [x] Verify the current input hashes and extract the archived raw evidence into an isolated working directory. Record host/tool availability and the snapshot manifest.
- [x] Write parser/accounting tests first, using small literal disassembly/event fixtures: distinguish code from literal pools, reject malformed counters, and detect a missing/duplicated classification or inconsistent sum. Record failing then passing results for the behavior implemented.
- [x] Implement `analyze.py --evidence-root PATH --output-dir PATH`; input root is `partial-direct/`, output is inside `compiler-explanation/`. It must read the two saved case directories and validate their hashes before producing diagnostics/accounting.
- [x] Map copy-in, convolution, final quantization/store, history copy, function entry/exit and stream-wrapper work. Compare native arithmetic, constant lowering, live values and stack-resident values. Annotate at least the two partial sums, one recurring stack-resident arithmetic value and ABI saves, or state exactly why a mapping cannot be established.
- [x] Reconcile dynamically supported contributions to the totals. Use the optional two-binary diagnostic replay only when it adds necessary evidence; inspect the simulator's actual logging behavior before assuming a flag emits the required records. Preserve marker and final-short-call conventions, and exclude setup/printing/closing-marker events consistently.
- [x] Produce the two-row contract, component delta table and annotated excerpts. Distinguish demonstrated contribution, likely interpretation and unresolved cause. Store hashes for every supporting raw file, annotation and command record.
- [x] Run `python3 -m unittest discover -s research/fir-sharing-probe/compiler-explanation -p 'test_*.py' -v`, then the analyzer command. An unresolved attribution can pass consistency checks; label it unresolved in the findings.
- [x] Obtain the fresh review described below; address important errors with a reproducing test where appropriate. Deliver code, tests, accounting, findings, review and any nonversioned raw trace archive.

## Task 2 — User: independent verification and contribution synthesis

- [x] Verify the frozen source result, raw logs and binary identities using the supplied archive; historical raw builds are unnecessary for this task. Reading/reusing the existing independent checker's transcript decoder and model is allowed; importing the new peer analyzer or its classification logic is not.
- [x] Write `test_verify.py` first around hand-calculated report fixtures. Cover valid reconciliation, changed total, altered component with a renewed evidence hash, missing/duplicate compiler, wrong binary identity, path traversal, negative counts, static-only attribution limits and absent peer delivery. A renewed hash must not conceal a total mismatch; a consistent semantic mislabel still requires manual review.
- [x] Implement `verify.py --peer-report PATH --output-dir PATH`. Validate the shared schema, fixed totals, manifests and arithmetic sums independently. Emit `verification.json` and `comparison.md` inside the user's owned directory. Without peer delivery, emit an explicitly pending report and never fabricate a pass.
- [x] Independently derive the exact counter deltas and cost deltas from the two frozen rows. Check that the existing candidate rankings and within-compiler versus selectable-compiler percentages use the intended comparators.
- [x] Prepare `claims.md` and `paper-outline.md` in the user's directory. Reuse the existing primary-source assessment; follow up only sources needed for the proposed claim. Distinguish established mechanisms, original local observations and causal evidence still needed. Mark the explanation section pending until delivery; leave existing proposal/findings unchanged during parallel work.
- [x] Run `python3 -m unittest discover -s research/fir-sharing-probe/explanation-check -p 'test_*.py' -v`. Before delivery, success means fixture/rejection tests pass and the pending state is accurate; it does not mean the peer explanation is certified.
- [x] Obtain a fresh review of the checker and the claim boundaries. Keep reviewers' findings and how they were handled in `review.md`.

User checker CLI outcomes: absent peer path means exit 0 with
`status="pending"` and zero peer rows checked; admitted evidence means exit 0
with `status="consistent"` and two rows checked. Malformed or inconsistent
delivered evidence means nonzero exit with an actionable error and no overwrite
of previously valid reports. `verification.json` records the source-result hash,
peer-report hash when present, per-row reconstructed totals/deltas, evidence
files checked, limitations and `manual_causal_review="pending"`. The coordinator
records the subsequent manual judgment in `final-decision.md`; numerical
consistency never automatically becomes causal certification.

## Delegation policy for each coordinator

Use **Sol 6.0** as coordinator and implementation worker; use **Astra** for the
separate assembly/claim reasoning assignment and final fresh review. These are
the user's available model choices, not claims about comparative pricing.
Select exact model IDs and supported reasoning settings exposed by the runtime.
Request `high` effort for these analysis/review assignments where supported.

| Stage | Child task | Model | Write ownership |
|---|---|---|---|
| Parallel | Parser/checker implementation and tests | Sol 6.0, high | Assigned Python files, JSON/derived output, designated evidence subdirectory |
| Parallel | Peer: assembly value-flow analysis; User: claim/source assessment | Astra, high | Peer: `assembly-notes.md`; User: `claims.md` and `paper-outline.md` |
| After integration | Fresh final reviewer | Astra, high | Read-only; coordinator records the returned review |

- Maximum two child agents active concurrently and three distinct child tasks per coordinator for this assignment. Workers execute directly; no recursive delegation. Both human workstreams can run at the same time on their own machines.
- A child gets a clean task context: objective, exact read paths, owned files, frozen identities, expected outputs, acceptance commands and limits. Do not forward the whole conversation.
- Supply model and effort explicitly when the tool supports them. Inspect runtime/role overrides and reported settings when exposed; do not assume prompt wording proves routing. If routing cannot be verified, record `unverified`. If a requested model is unavailable, continue feasible work on an available permitted model, disclose the substitution and the missing independent review if relevant. Never silently request Sol 6.1, Luna or another unavailable model.
- Keep the two workers' writes disjoint. The coordinator can verify evidence and draft its own narrative while they work. Integration and final review depend on both workers' outputs and happen afterward.
- Each worker returns paths, actual checks/results, supported findings, unresolved issues and a concise evidence pointer. Report output summaries rather than dumping entire traces into the parent conversation.
- Reuse the responsible worker for a bounded correction. A test failure or ordinary analytical difficulty is not a reason to create another team or enlarge the experiment. Ask the human only for genuinely missing input, unavailable required access, or a proposed scope expansion.
- Where native subagent tools are absent, do the assignment sequentially and mark independent review as unavailable. Do not claim delegation occurred. A separate manually opened Astra session can perform the read-only review using the same evidence.

Explicit model/effort selection and concise independent tasks follow the
[official OpenAI subagent guidance](https://learn.chatgpt.com/docs/agent-configuration/subagents).
Permissions and actual available tool schemas remain authoritative; this plan
does not require editing global configuration or bypassing a sandbox.

## Final join and stopping rule

After peer delivery, the user runs its independent checker on the actual report,
checks the key value-flow/PC annotations against the same hashed binaries, and
writes `explanation-check/final-decision.md`. Only then incorporate an explanation
into the paper or proposal.

A good result is either a supported explanation or an accurately bounded account
of what remains unresolved. If the difference is ordinary compiler lowering and
stack traffic, present modest empirical characterization and baseline correction.
If a specific further interaction is supported, state its mechanism and limits.
Neither outcome establishes a new FIR algorithm. Stop this investigation after
the two-binary explanation; any new performance experiment or optimizer needs
its own explicit scope decision.

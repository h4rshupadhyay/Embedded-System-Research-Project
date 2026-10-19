# Peer prompt: explain the existing FIR compiler difference

Start a **Sol 6.0** session with high reasoning if offered, open the updated
repository, and paste the block below. Astra is assigned focused
analysis and review work. The task does not require Sol 6.1.

Pull branch `research/fir-independent-check` from
`https://github.com/h4rshupadhyay/Embedded-System-Research-Project`.
It includes the completed results, current plan and versioned raw-evidence
archive. Preserve local edits when switching branches. The old baseline-handoff
branch alone lacks the completed results. The original
[Sol 6.1 prompt](peer-sol-6.1-handoff.md) is historical.

If receiving an offline snapshot instead, verify its `SNAPSHOT-MANIFEST.json`.
That manifest is specific to archive delivery; it is not required in a Git clone.

```text
Execute the PEER assignment in:
docs/superpowers/plans/2026-10-20-fir-compiler-explanation.md

Purpose: explain the existing GCC10 versus GCC15 BLOCK=1 exact partial-direct
FIR code difference. The user is independently checking evidence and preparing
the paper's claims. Complete your deliverable without waiting for their task.
This is a college empirical study. A complete cause, favorable optimization,
new FIR algorithm or publication result is not presumed.

Read in order:
1. The plan above: ownership, frozen identities, output schema, delegation rules.
2. research/fir-sharing-probe/independent-check/join-review.md
3. research/fir-sharing-probe/independent-check/comparison.md
4. research/fir-post-join-research-assessment.md, next-step section.
5. partial-direct/kernel.c, kernel.h and run.py under research/fir-sharing-probe/.
6. The archived gcc10-b1/gcc15-b1 commands, sources, disassembly, maps, stack
   reports, raw stdout and raw counters. Read simulator code only if needed.

Evidence setup:
- Start from the updated research/fir-independent-check branch, or the supplied
  current snapshot. Create your own working branch before making changes.
- Verify the exact hashes in the plan. For snapshot delivery also verify
  SNAPSHOT-MANIFEST.json; Git delivery does not include that snapshot-only file.
- Restore independent-check/partial-direct-target-evidence.tar.gz into
  research/fir-sharing-probe/partial-direct/ as documented in join-review.md.
- This task needs only the two block1 cases. The other four archived cases
  remain context; no full benchmark rerun is required.
- Inspect available tools. Python and saved disassembly support the initial
  work even when Arm compilers or the simulator are unavailable locally.
  A saved binary is evidence; a missing trace is not permission to invent one.

Write only research/fir-sharing-probe/compiler-explanation/.
Keep the delivered partial-direct code/results, existing simulator, frozen
inputs, existing checker and the user's explanation-check/ files read-only.
Use your owned build/ for temporary work. If necessary, restore the supplied
archive to its documented input location without changing its files.

Expected facts to verify from raw evidence, not simply quote:
GCC10/block1: NI=198670, MUL=2827, RAM reads=29304, RAM writes=17225.
GCC15/block1: NI=242490, MUL=2827, RAM reads=43182, RAM writes=36500.
The difference is +43820 instructions, +13878 reads and +19275 writes.
Frames are 72/240 bytes. These aggregates do not establish why every access
exists. Use the plan for all remaining counters and exact identities.

DELEGATION — explicitly authorized, bounded and required when supported:

Act as coordinator. Use the runtime's exact available model identifiers for
Sol 6.0 and Astra; those display names are not invented API IDs. Select both
model and high effort explicitly where supported. Inspect reported settings
and role overrides when exposed. Record unavailable or unverified routing.
Use no other model without an explicit human change to this restriction.

Spawn these two independent workers concurrently, with clean context:

A. Sol 6.0 / high — implementation and accounting
   Own analyze.py, test_analyze.py, accounting.json, evidence/ and build/.
   Read the shared plan and exact gcc10-b1/gcc15-b1 artifacts.
   Implement a hash-checking saved-evidence analyzer and component accounting.
   Test first using literal fixtures, including malformed evidence, code versus
   literal-pool parsing, and nonreconciling/duplicate classification.
   Keep static diagnostics distinct from demonstrated dynamic counts.
   Emit the plan's exact JSON schema. Preserve explicit unattributed counts.
   Diagnostic replay is limited to the same two binary bytes, under the plan's
   logging-only isolation and output/counter reconciliation rules.
   Return paths, commands/results, reconciliation, limitations and input hashes.

B. Astra / high — assembly reasoning
   Own assembly-notes.md only. Read original source, maps and disassemblies
   directly while worker A builds its analyzer.
   Map the two partial sums through sign extension and final reduction.
   Trace representative recurring stack-resident values and ABI saves.
   Compare constant lowering, value lifetimes, copy/quantization/control work.
   Cite compiler, function, address range and source-value evidence for each
   inference. Distinguish stack temporary from a proven allocation spill.
   Return an annotated explanation with competing hypotheses and explicit
   unresolved points. Frame size or static load count alone proves no cause.
   Do not edit analyzer/output files or conduct new optimization experiments.

Give EACH worker: purpose, plan path, original evidence paths, exact ownership,
hash constraints, expected output, acceptance command and the instruction to
execute directly without spawning further agents. Do not forward the entire
chat. At most two children active at once; no recursive delegation. Reuse a
worker for a bounded correction rather than launching more teams.

While workers run, independently validate setup/identities and draft findings.md
using your own files. After both return, inspect their evidence, integrate their
outputs, run tests and reproduce the analyzer. Do not accept a summary in place
of real files or actual command output.

Then start ONE FRESH Astra/high reviewer, read-only, with the plan, exact inputs,
completed output paths and this review focus:
  * fixed binary and compiler identities;
  * closing-marker/setup/printing boundary;
  * static versus dynamic counts and exact sum reconciliation;
  * literal pools, PUSH/POP transfers, branches and residual attribution;
  * representative stack-slot value flow and causal overclaiming;
  * same-binary diagnostic replay equivalence, if used;
  * scope and shared-file ownership.
Ask for severity, file/address evidence and a concise verdict. Coordinator owns
review.md and records the real findings and handling. This reviewer is the third
distinct child task, after the two workers; workers do not review their own work.
Address important errors with reproducing tests where applicable and rerun the
affected suite. Do not claim an independent review if it did not happen.

If subagent tools are absent, do the work sequentially and mark the review
unavailable, or use a separately opened Astra session with the same read-only
review brief. Record a model substitution if the requested routing is unavailable.

Completion:
- Deliver analyze.py, test_analyze.py, accounting.json, assembly-notes.md,
  findings.md, review.md and hashed supporting evidence.
- Run the plan's peer test and analyzer commands. Report actual output.
- Explain exactly how much of each counter difference is supported, and keep
  the rest explicitly unattributed. A consistent residual is allowed; calling
  it explained is not. Retain negative or routine findings equally.
- Preserve two annotated assembly excerpts and a compact counter-delta table.
- If diagnostic trace files live in ignored build/, archive them separately
  with relative paths and checksums; hashes without the files are insufficient.
- Return only your owned directory plus that archive, or an owned-files-only
  commit/patch if working in a Git checkout. No merge or force-push is requested.
- End with result, evidence paths, tests, actual model/delegation record, review
  findings and unresolved issues. Do not expand the task to improve a percentage.
```

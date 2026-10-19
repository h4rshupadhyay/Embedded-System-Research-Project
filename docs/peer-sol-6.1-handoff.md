# Peer handoff prompt for GPT-6.1 Sol

**Historical assignment — completed.** For the next parallel investigation using
the peer's available **Sol 6.0 and Astra**, use the
[new compiler-explanation prompt](peer-sol-6.0-compiler-handoff.md) and
[user verification prompt](user-fir-explanation-handoff.md). The original prompt
below records the already delivered partial-direct baseline task.

Give the following prompt to your coding agent after cloning the repository.
The repository access URL is public; no collaborator invitation is needed to
clone it. To contribute without write access, use a fork and pull request, or
return your commit/patch and evidence archive to the original author.

```text
You are implementing Task 1 of our two-person exact FIR research project.
Do the implementation and verification, not just a proposed plan.

Repository: https://github.com/h4rshupadhyay/Embedded-System-Research-Project
Starting branch: research/exact-fir-baseline-handoff
Create your working branch from that branch, for example peer/partial-direct-baseline.
If you are starting outside a checkout:
  git clone --branch research/exact-fir-baseline-handoff https://github.com/h4rshupadhyay/Embedded-System-Research-Project.git
  cd Embedded-System-Research-Project
  git switch -c peer/partial-direct-baseline

Read, in this order:
1. README-FIR.md
2. docs/superpowers/plans/2026-10-20-fir-baseline-check.md, especially Task 1 and the shared result format
3. research/fir-sharing-pursuit-audit.md
4. research/fir-sharing-probe/PROTOCOL.md
5. research/fir-sharing-probe/probe.py and research/fir-baseline/README.md

Context: FIR-only, simulator-only college research; time is not a constraint.
Our professor only evaluates the final presentation and is not available as a guide.
The current decision is conditional: an apparent transposed FIR/Hcub advantage
has not yet survived a fair range-specialized direct baseline. Implement that
missing control. A null or negative result is equally useful. Do not claim a new
FIR algorithm, novelty, physical energy savings, or a universal winner.

Ownership: create/edit only research/fir-sharing-probe/partial-direct/.
The other team member independently owns independent-check/ and the comparison.
Do not implement their task, edit shared runners, regenerate frozen inputs,
overwrite historical results, or rerun the old full benchmark matrices.
If a shared change is indispensable, document it and return it as a proposal.

Implement the fixed 48-tap speech_minphase48 direct FIR. Read its literal
coefficients from research/fir-baseline/selection-design.json. Match the existing
spec_direct unrolled coefficient-specialized organization, with two int32 partial
accumulators as the only substantive arithmetic change. Fixed zero-based groups:
  coefficients [0,2): L1=12778; full-int16 absolute bound=418709504
  coefficients [2,48): L1=59731; bound=1957265408
Both fit int32; each product and every partial prefix are safe by the same bound.
The full bound=2375974912 exceeds INT32_MAX. Widen BEFORE adding the partials:
  int64_t exact_sum = (int64_t)partial0 + (int64_t)partial1;
Then quantize once as clip_int16(floor(exact_sum/32768)). Handle negative floor
correctly. No intermediate wrapping, rounding, saturation or sample dropping.
Input guarantee is the complete signed-int16 domain, not just the small timed data.
History initially contains zero. Follow the exact C adapter/history contract in
the plan (five functions, ProbeState history[48+BLOCK], retained history 0..46).

Write tests first and record the initial expected failure. Test arbitrary-precision
integer convolution, coefficient-sign-aligned windows overflowing the full int32
sum, signed extrema, negative floor boundaries, saturation, initial zeros, mixed
blocks 1/64/3/16 and short final calls. Check retained chronological history and
state/output guards. Run host GCC with UBSan and nonrecovering checks. Avoid
floating-point reference calculations and test only mathematically safe arithmetic.

Use first 257 frozen inputs.adc_raw samples for exactly four timed configurations:
  gcc10 and gcc15, each with BLOCK=1 and BLOCK=64, M=32768, -O2, no LTO,
  Cortex-M0 Thumb, identical established measurement boundaries and flags.
Include all recurring stream/state/call/tail costs. Block64 has a final one-sample
call. Preserve O:/H:/G:/M: output encoding and use the existing event-to-cost
functions. Raw ISS ticks are not Cortex-M0 cycles. Report Arm-table zero-wait-state
cycles and modeled CPU energy (20MHz, prefetch off, zero waits, single-cycle MUL).
Keep supplementary signed-edge correctness runs separate from the four timed rows.

Frozen SHA256 values, which you must verify before work and preserve:
  research/fir-baseline/selection-design.json
  bc4fac9ed74742667f90e3ef6504d7fbf41a567ca266f54f3ec12a72b78a876f
  research/fir-sharing-probe/results.json
  57c8b9f95a72a041193aebb70e12319a9c05daf11ef8be37e9f1955875d4edfa

Deliver kernel.h, kernel.c, run.py, test_kernel.py, results.json and notes.md in
your directory. Keep generated files in its own build/. Follow the plan's row
schema: stage="post-audit missing-control", variant="partial_direct32x2",
filter="speech_minphase48", maximum=32768, samples=257, compiler=gcc10/gcc15.
Record exact compiler identities/flags, cost-model metadata, raw event counts,
source/binary/disassembly/raw-log hashes, output/state/guard verification, code
size, stack/frame diagnostics and state allocation. Result directory paths must
be relative to partial-direct/. Inspect target assembly for native-width partial
adds and the final wide reduction; report actual lowering, including surprises.

An ordinary checkout does not include installed target toolchains or historical
raw build artifacts. Do not use the older root simulator patch/environment as a
substitute for the current research/fir-baseline fixture. First complete host work.
Reproduce the pinned target environment from the documented sources when possible.
If it is unavailable on this computer, return tested host code, the four-case runner
and a clear pending-measurement status for the original author to run locally.
Do not fabricate measurements or put placeholders that look measured into rows.

Return a concise implementation summary, actual test commands/results, arithmetic
proof, assembly observations, any blockers/pending measurements and your commit
or PR. Include the generated target evidence in a separate archive if it cannot
be versioned; results with hashes alone are insufficient for independent checking.
Do not force-push or change main. Do not expand to other filters, new partitions,
an optimizer or additional benchmark grids. The final research decision belongs
to the joint independent comparison after both workstreams finish.
```

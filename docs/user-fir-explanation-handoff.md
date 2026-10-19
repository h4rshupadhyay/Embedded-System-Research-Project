# User prompt: independently verify the explanation and prepare the claim

Paste this into your coding-agent session after opening the current project.
It can run while the peer works. The delegation uses the same Sol 6.0/Astra
choices so both handoffs are portable between your environments.

```text
Execute the USER assignment in:
docs/superpowers/plans/2026-10-20-fir-compiler-explanation.md

The peer independently owns the compiler-explanation/ directory. Your job is to
verify the forthcoming two-binary accounting and prepare the paper's defensible
claim. Start immediately with frozen evidence, fixtures and the claim note.
Actual peer certification and the final combined decision wait for delivery.

Read in order:
1. The plan: shared schema, exact hashes/totals, ownership and stopping rule.
2. research/fir-sharing-probe/independent-check/join-review.md and comparison.md.
3. research/fir-post-join-research-assessment.md.
4. research/fir-sharing-probe/independent-check/check.py and test_check.py,
   only the parts needed for evidence parsing/model reuse.
5. The two archived block1 cases and the frozen partial-direct/results.json.

Write only research/fir-sharing-probe/explanation-check/.
Restore the supplied raw archive to its documented input location if needed;
otherwise existing evidence and both other people's directories are read-only.
Leave the current proposal and historical result files unchanged until the join.
This is verification and synthesis, not a new performance experiment.

DELEGATION — authorized within this exact scope:

Use Sol 6.0 and Astra only; resolve their exact identifiers from the runtime.
Request high effort when supported and inspect actual routing/overrides if
exposed. Record unsupported or unverifiable settings honestly. Give workers a
clean, self-contained brief rather than the whole conversation. Workers execute
directly, without further delegation. Maximum two active children and three
distinct child tasks in this assignment.

Run these two workers concurrently:

A. Sol 6.0 / high — independent checker
   Own verify.py, test_verify.py, verification.json, comparison.md and fixtures/.
   Use the plan's JSON contract, original partial-direct artifacts and literal
   fixtures. You may reuse the EXISTING independent checker's raw transcript
   decoder/model, but never import the new peer analyzer or its classification.
   Test first. Cover successful sums, changed totals, altered components even
   with renewed hashes, absent/duplicate compilers, wrong binary identities,
   unsafe artifact paths, negative counts and pending peer evidence.
   Recompute eight event totals and cost deltas from original logs; reject
   mismatches rather than updating expected values to match the peer.
   Keep arithmetic consistency separate from semantic/causal certification.
   Before delivery, use hand-calculated fixtures and mark real peer status
   pending. Fixture success is not verification of unseen peer evidence.
   Return actual commands/results, rejection coverage and known limits.

B. Astra / high — claim/evidence assessment
   Own claims.md and paper-outline.md only. Read completed results and the
   primary-source assessment independently of worker A.
   State the narrowest useful research question, supported contribution,
   established-method overlap, remaining causal evidence and strongest objection.
   Build a claim/evidence matrix and concise paper outline. Mark the causal
   section pending; do not predict or invent the peer's explanation.
   Keep within-GCC15 24.06% separate from selectable-compiler 3.97%/2.30%
   comparisons, and modeled costs separate from physical energy claims.
   Use existing primary literature first. Browse only for a claim that actually
   needs verification, cite the owning primary source, and record access limits.
   Do not start another general novelty search or delegate additional agents.
   Return recommended framing and what evidence would weaken it.

While workers run, as coordinator verify the frozen file identities, reproduce
the known aggregate deltas and prepare the eventual acceptance checklist.
After both workers finish, inspect their files and integrate only owned outputs.
Run the plan's user test command and the checker against fixtures/frozen evidence.

Start ONE FRESH Astra/high reviewer after integration. It is read-only and gets
the plan, source evidence and owned outputs. Review numerical independence,
tamper rejection, path containment, pending-versus-verified reporting, attribution
limits, comparator choice and claims that exceed the literature or experiment.
Record real findings/handling in review.md. Fix important defects with a test
where appropriate. Do not claim an independent review if the runtime could not
provide one; a separate manually opened Astra session is an acceptable fallback.

Independent completion now:
- Tested verify.py/test_verify.py with actual rejection coverage.
- verification.json/comparison.md explicitly pending real peer delivery.
- claims.md, paper-outline.md and review.md complete within their evidence limits.
- Actual checks, actual models/settings and unresolved issues reported.
Do not wait idly for the peer or label the combined study finished at this point.

After the peer returns, in a continuation of this task:
- Recheck source and evidence identities, inspect the peer's files, then run:
  python3 research/fir-sharing-probe/explanation-check/verify.py \
    --peer-report research/fir-sharing-probe/compiler-explanation/accounting.json \
    --output-dir research/fir-sharing-probe/explanation-check
- Manually check representative source-value/PC annotations against the exact
  binaries. A consistent total does not prove the component labels or spill cause.
- Write explanation-check/final-decision.md. Resolve discrepancies before
  ranking explanation quality or importing a causal claim into the paper.
- If the cause is routine lowering/stack traffic, retain modest empirical
  characterization and baseline correction. If unresolved, state what the data
  cannot identify. Neither condition authorizes an optimizer or a new bank.
- Return the numerical conclusion, supported contribution, limitations, checks,
  review findings and owned paths. Keep both compilers' favorable/unfavorable
  outcomes visible and preserve existing frozen results.
```

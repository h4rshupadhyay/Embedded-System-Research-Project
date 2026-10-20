# Improving the existing FIR paper

20 October 2026. Research and recommendations only. No manuscript, source,
frozen evidence or experiment was changed. Effort estimates below are planning
judgments, not measured runtimes or commitments.

## Recommendation

**Make this a stronger empirical paper about the consequences of unequal
arithmetic specialization.** A new algorithm is not necessary to improve it.
First sharpen the argument, expose the remaining sharing effect and test the
cost-model dependence using saved events. Then, if a material scientific
extension is wanted, perform one predeclared prospective validation study with
fresh filters and workload regimes. Improve the reproducibility package in
parallel. Do not revive the failed H1 optimizer to make the paper look novel.

The strongest question is:

> How much does giving direct accumulation the same exact-range information
> change the implementation decision, and which apparent sharing advantages
> remain after matched representation controls, workload boundaries and
> explicit model-cost sensitivity?

The strongest **currently supported** contribution sentence is:

> For one exact full-int16 FIR, an arithmetic-fair direct control reverses two
> of four previously consistent sharing decisions; matched transposed controls
> distinguish the incremental sharing result, while emitted-code accounting
> explains most of one compiler-dependent cost increase.

This is already worthwhile empirical work for a college research project:
it corrects a consequential comparison and explains a concrete outcome. That
assessment is my judgment, not a claim about the professor's rubric. Publication
likelihood remains unknown without a venue and a differentiated evidence claim.
The most useful stronger contribution would characterize **where the correction
matters and where it does not**, rather than seek a universally winning kernel.
Prospective confirmation must precede any such broader sentence.

This ordering separates low-cost execution from scientific return: writing and
saved-event work come first, but the fresh boundary test in item 3 offers the
largest substantive evidence gain. SIGPLAN's primary evaluation guidance
supports matching evidence to scoped claims and principled benchmark choices;
it explicitly treats its checklist as judgment support, not an acceptance
formula. That is the methodological standard used here.
[SIGPLAN empirical-evaluation guidance](https://www.sigplan.org/Resources/EmpiricalEvaluation/).

## What is already strong, and what the literature changes

The [manuscript](fir-paper/manuscript.md) already has exact arithmetic and prefix
bounds, one final quantizer, UBSan and adversarial correctness checks,
independent output/event admission, all four principal outcomes, an ordinary
transposed comparator, compiler-selectable comparisons, resource appendices,
a quantified explanation residual, and honest model/selection limitations.
The [review](fir-paper/review.md) and [checkpoint](fir-paper/PROGRESS.md) record
the completed numerical and rendering checks. These are assets to preserve,
not missing work to repeat.

The relevant primary precedents point toward better **experimental contrast**:

- SPIRAL's FIR paper already varies blocking/computation order and shows
  runtime differences at identical arithmetic counts, including small
  in-register blocks. Consequently “fewer operations can lose” is context;
  this paper's advance must be the precise arithmetic-fair comparison and
  its measured boundaries. [Gačić et al., §§4–5](https://www.researchgate.net/publication/2589071_Fast_Automatic_Software_Implementations_of_FIR_Filters).
- Processor-aware software word-length/instruction search under an accuracy
  constraint already exists. Add a compact comparison of its SQNR-based
  problem with this paper's exact-output audit; do not imply that narrow
  partials or width-aware generation were invented here.
  [Ménard–Sentieys, §§4–5.4](https://www.researchgate.net/publication/220905057_DSP_Code_Generation_with_Optimized_Data_Word-Length_Selection).
- Fixed-point FIR generation, platform adaptation, vendor-library comparisons
  and physically measured energy optimization also predate this work.
  Those physical XScale results are a useful contrast, not validation of
  this simulator. [D'Alberto et al., §§2.2–4](https://users.ece.cmu.edu/~franzf/papers/hipeac07.pdf).

## Ranked improvements

### 1. Lead with the corrected decision and a short causal contrast map

**Type: writing/organization; roughly half to one focused day.** The abstract,
§1, §4.4 and §7.1 repeatedly explain why retrospective H_R is permissible.
That transparency is correct, but its repetition gives the reporting rule
more prominence than the scientific result. H_R is not itself the novelty.

Keep one clear retrospective disclosure, the all-four decision criterion and
the complete table. Reorganize the introduction/results around three questions:
what the direct width correction changes; what Hcub adds over ordinary
transposition; what the compiler-specific emitted code explains. Retain the
fixed-compiler/selectable-compiler distinction. A possible title is
*Arithmetic-Fair Comparisons of Exact FIR Software: A Cortex-M0 Model Case
Study*; this is an editorial option, not a requested manuscript edit.

Add one small representation/data-lifetime diagram beside §3.2. Show direct
history versus transposed suffix state, the two native direct partials, and
the single final quantizer. Label the two informative contrasts:
`partial direct ↔ wide direct` and `Hcub ↔ ordinary transposed`. Do not imply
that `Hcub ↔ direct` isolates sharing. Figure 1 already shows comparator
sensitivity well; another plot of the same four percentages adds little.

**Acceptance:** an unfamiliar reader can identify the changed control, both
compiler-dependent winners, the sharing-only comparison and the unresolved
explanation residual from the first two pages. Every conclusion still traces
to an existing result. No prospective or universal claim is added. A tighter
draft should spend the recovered space on evidence, not additional disclaimers.

### 2. Extract more decision value from the saved event vectors

**Type: reanalysis, no target runs; roughly one to two days.** §5 gives a
complete modeled-energy table but shows detailed arithmetic/memory tradeoffs
for only GCC10/block64. The all-four incremental sharing effects are available
in [results.json](fir-paper/results.json), yet mainly summarized qualitatively:
Hcub relative to ordinary transposition is **+3.41%, −0.17%, −4.28%, −6.69%**
in GCC10/1, GCC10/64, GCC15/1, GCC15/64 order. Promote those contrasts into one
compact table/figure with their signed event differences. This makes clear
how little of some library-relative saving is attributable to adding Hcub
within the same transposed equations. It does not turn each source graph
operation into an executed instruction.

For each named pair compute the exact event-cost difference

\[
\Delta E=w\cdot\Delta v,\qquad
v=(N_I-N_M,N_M,B,R,W,F).
\]

Show which components favor each form and identify any event-wise dominance.
Include a small resource tradeoff summary drawn from Appendix A; keep state
allocation, reported frame and selected-symbol bytes separate. They cannot be
added indiscriminately into peak SRAM or called total image size.

Then report analytic break-even boundaries for selected event-weight changes.
The adopted model uses configuration-specific fitted coefficients. Its authors
explicitly warn that correlated event frequencies influence fitted RAM-read
weights, and its aggregate validation error is not a pairwise error bound.
This motivates sensitivity analysis, not treating each coefficient as an
independently measured physical operation energy.
[Nikov et al., §§2.3–2.5/Table 2](https://arxiv.org/html/2301.12806v1).

Appendix A below demonstrates feasibility on the saved rows. Choose and label
stress paths before presenting conclusions; report exact boundaries, rather
than inventing an uncertainty distribution. If using weights from another
published hardware configuration on frozen counts, call it coefficient-only
reweighting. A real configuration change can alter the events and timing and
would require a compatible simulation model and new runs.

**Acceptance/falsification:** independently reconstruct each original pairwise
energy difference at the nominal weights; publish the difference vectors and
boundaries; preserve unfavorable reversals. Claim robustness only over an
explicitly stated region. A tie/reversal inside that region falsifies it. No
region becomes physically calibrated merely because the nominal MAPE is 2.80%.
Repeated deterministic runs or p-values cannot supply the missing calibration.

### 3. Address the largest scientific gap with one finite prospective study

**Type: new simulation experiments, separately authorized if pursued; likely
several focused days to a few weeks, depending on generator reuse.** §4.1 and
§7.3 correctly limit runtime evidence to one selected filter and one
257-sample, zero-history ADC stream. The full-int16 correctness guarantee is
broader than that performance stimulus; signed-edge correctness runs do not
establish full-range performance behavior. The main missing evidence is a
boundary test, not more compiler versions.

There is a concrete boundary here: the saved 257 values range from −1024 to
1023. With coefficient magnitude sum 72,509, every such window obeys
`|S|≤1024×72509=74249216`, giving final-output magnitude at most 2266. Thus
the timed stream cannot exercise final saturation. This observation, first
identified by the coordinator and checked here against the saved input and
integer bound, concerns performance coverage; the existing separate edge
correctness checks already address saturation correctness.

I recommend a **bounded initial panel of three genuinely new nonsymmetric
48-tap coefficient designs**: one whose full sum is certified native-width,
and two whose full sum needs widening but certified native partials are legal,
with different coefficient/share structures. Keeping length fixed first
reduces confounding; new lengths are an optional later question. Specify
design procedures, numeric contracts, coefficients and hashes before examining
compiled costs. Select designs by mathematical/application properties, never
by whether Hcub or partial direct wins. If this exact panel cannot be obtained
without outcome-driven selection, revise and freeze it before performance runs.
For each widening-required design, require a legal sign-aligned input window
whose exact full sum overflows int32, or a tight exact full-sum interval crossing
the int32 limits. Failure of the symmetric sufficient `M×Σ|h|` bound alone
does not establish that widening is necessary.

Keep the two current compilers and blocks 1/64. Use two predeclared stimuli:
the task-like ADC-range signal and a fixed-seed signed full-range signal. For
each report a short startup case and a long stream, with a separately specified
post-startup region if a steady-state claim is intended. Freeze lengths,
measurement markers, seeds and handling of the final partial block. A long
stream alone does not prove a steady-state model; separate startup/call work
from the later region. These are workload conditions, not independent filters.

Use the current five main forms as the starting baseline set: wide direct,
certified direct, ordinary transposed, demand Hcub and correctly configured
standard CMSIS. Certified direct uses one native group when legal; otherwise
use the first legal two-group cut, and add one range-balanced legal cut,
deduplicated. Freeze these choices before measurement and retain all their
outcomes. This checks whether the original favorable split
was idiosyncratic. It is a conventional baseline-strengthening exercise, not
an H1 optimizer or a claim of optimal direct code. Give every form identical
range information and comparable specialization/tuning budgets.

Arm's documentation distinguishes Q15 standard 64-bit accumulation from fast
32-bit accumulation with wraparound risk and scaling requirements; it also
documents coefficient order, odd-length padding and state requirements.
Consequently include fast CMSIS only when admitted under the same contract,
and inspect the actual pinned v1.14.4 path/configuration rather than assuming
the current documentation certifies an old binary. Full-int16 admission and
unchanged final quantization remain mandatory.
[Arm FIR documentation, Q15 initialization and scaling behavior](https://arm-software.github.io/CMSIS-DSP/main/group__FIR.html).

**Freeze the estimands, not the desired winner:** direct width-correction
percentage; change in the chosen representation within the tested set;
Hcub-versus-ordinary incremental cost; startup/long-region cost difference;
and all integer event/resource counters. Report fixed-compiler decisions and
compiler-selectable decisions separately. Fix the candidate family above: at
most six forms per design, including the balanced-cut alternative on the two
wide-required designs and eligible fast CMSIS on the native-fit control. The
hard cap is **288 performance execution conditions**:
`3 designs × 6 forms × 2 compilers × 2 blocks × 2 stimuli × 2 regimes`.
Deduplicate identical controls/binaries honestly and count correctness-only
runs separately. Do not add schedules, compiler flags or coefficient designs
after inspecting costs. This is a proposed bounded design, not an experiment
launched here, and proves no generalization to other filter lengths or symmetry.

**Acceptance/falsification:** every admitted kernel passes the existing
arithmetic/output/state gates, and both widening-required designs pass the
overflow-witness/tight-interval admission above; all predeclared cases,
exclusions and failures are reported. A claim that the ranking reversal extends beyond the original
filter requires at least one independently specified new design exhibiting
it. No such case means that extension fails, even if direct narrowing still
reduces cost. If results differ between short and long regions, restrict the
guidance accordingly. Three purposively selected designs establish a boundary
panel, not population prevalence or a universal selector. All current and
previously inspected filters remain development evidence, including formerly
held-out cases. Do not replace negative cases with fresh favorable ones.

### 4. Make the raw-evidence level work from a fresh environment

**Type: artifact packaging/reanalysis; roughly one to three days, subject to
toolchain redistribution/access.** Table/plot regeneration is already portable.
The actual gap is Appendix C and the
[independent-check README](fir-sharing-probe/independent-check/README.md):
historical integration needs ignored `build/cases/` artifacts and recorded
dependency sources; integration tests explicitly skip without them. The
partial-direct archive does not by itself supply all historical evidence.

Package the paper's finite evidence slice: input/coefficient bytes, source,
compiler identities/commands, binaries/disassemblies, raw output/events,
historical and new certificates, Hcub invocation/output/license, and manifests.
Document how to obtain dependencies that cannot be redistributed. Have a
separate person exercise the published instructions in a blank environment,
record expected runtimes and every skipped check, and map every paper table
and explanation to its required files. Keep table regeneration, raw-evidence
verification and new target reproduction as distinct levels.

This recommendation follows the official SIGSIM-PADS artifact guidance on
complete/exercisable artifacts and blank-environment trials, used here as a
practice benchmark. It is not an IEEE/college submission requirement or a
claim that this paper should target that venue.
[Official artifact criteria and submission guidance](https://sigsim.acm.org/conf/pads/2026/blog/artifact-evaluation/).

**Acceptance:** a fresh copy can reproduce the selected numerical results and
raw-evidence checks without the original workspace; unavailable levels are
explicitly identified. An integration skip is not a passing raw-evidence
check. Archive publication/DOI is optional and needs its own authorization;
neither a public repository nor a checksum alone supplies independent validation.

### 5. Strengthen the explanation with one matched intervention only if useful

**Type: optional new simulation experiment; roughly several days.** §6 already
provides a sound bounded accounting explanation. Identifying a responsible
compiler pass is not mandatory. The useful next question is whether the
general runtime-block interface makes the block1 comparison pay work that a
known-single-output API could avoid.

Compare the existing general kernel with one mathematically identical
constant-block/single-output specialization, or another carefully justified
source change that prevents unnecessary last-output window preparation.
Predeclare the intended emitted-code change; inspect actual code and count
all resulting events. If claiming an implementation winner, give competitors
the same block knowledge and optimization opportunity. A specialization can
change more than rotation, so do not attribute its whole saving to removed
stack transfers without checking the other differences.

**Acceptance/falsification:** exact outputs/state still agree; the intended
rotation/preload change actually occurs; total traffic/cost changes reconcile
to the emitted code. If the transformation does not remove that work, it is
not a test of that mechanism. If it removes work without reducing total cost,
the benefit prediction fails. Either result can sharpen the paper; stop after
this defined intervention rather than chasing compiler flags until a preferred
ranking appears. Compiler-pass dumps are needed only for a stronger claim
about the pass that caused the transformation.

## Packages and stopping milestones

**Minimal strong upgrade:** items 1, 2 and 4. This adds clearer contribution,
quantified incremental sharing/model sensitivity and a genuinely usable
evidence package without collecting another target result. Finish when the
contrast table, sensitivity boundaries and fresh-environment report are
complete. It remains a selected single-filter empirical case study.

**Largest worthwhile next scientific investment:** item 3, one frozen panel.
Use item 5 only if the API/rotation mechanism is a central claim worth testing.
Before execution, freeze contracts, baseline variants, workloads, estimands,
exclusions and a total run cap. After the panel, write the outcome regardless
of winner. Expand only to resolve a specific contradiction that changes the
claim; failure to find a new reversal is a result, not permission to search
indefinitely.

New allocation/search rules, predictive sharing policies, broader hardware
energy validation and a different architecture would be **separate research
questions** with separate proof/comparison burdens. The
[Stage 2 gate](fir-stage2-formulation-gate.md) rejects the current coarse H1
state; it does not prevent conventional stronger baselines or a better
empirical paper. Physical board validation would strengthen physical claims,
but is outside this simulator-only project and is not a prerequisite for the
recommended improvement package.

## Appendix A. Feasible saved-event sensitivity diagnostic

This diagnostic was first computed by the coordinator, then independently
recomputed here from the 20 exported rows using Python standard-library Decimal
arithmetic. It changes neither events nor the nominal model. Scale both RAM
coefficients by a common `λ≥0`, hold all other coefficients fixed, and write
`ΔE(λ)=E_Hcub−E_partial=A+Bλ`, in whole-stream nJ:

| Configuration | A | B | Tie λ, rounded |
|---|---:|---:|---:|
| GCC10 / 1 | −32436.319000 | 43973.275423 | 0.737637 |
| GCC10 / 64 | −16661.004146 | 24064.520307 | 0.692347 |
| GCC15 / 1 | −94335.682384 | 13297.172804 | 7.094417 |
| GCC15 / 64 | −16351.634074 | 8374.315001 | 1.952594 |

At `λ=1`, each equals its literal exported energy difference exactly; all
`B>0`, so Hcub has lower modeled cost below the tie and higher cost above it
on this path. This demonstrates that a useful sensitivity section is possible
without new target runs. These arbitrary weight stresses are **not** calibrated
uncertainty, predictions of another hardware configuration or a claim that
RAM reads/writes have independent physical prices. They do not overturn the
nominal results or make them physically validated.

## Research provenance and access limits

Read the current manuscript, paper README/review/results/checkpoint,
professor proposal, sharing protocol and independent-check README. The bounded
novelty plan and Stage 2 gate were read in full during the preceding assigned
gate and inform the separation from new-method work. Previous target results,
source/binary reviews and 18 passing paper tests are inherited completion
evidence; none was rerun here. The coordinator's observations about H_R
repetition, workload scope and the possible block1 intervention are integrated
as research judgments, checked against §§1, 4, 6 and 7, not facts claimed by
external sources. No rubric or venue suitability was verified.

Fresh external inspection was restricted to seven usable primary sources:
SPIRAL FIR author-uploaded full text (§§2–5, especially time-domain results);
Ménard–Sentieys author-uploaded full text (§§4–5.4/Fig. 3); the full XScale
author PDF (§§2.2–4); Nikov's full accessible HTML (§§2.3–2.5/Table 2);
official Arm FIR documentation (Q15 arithmetic/init/storage); official
SIGSIM-PADS 2026 artifact criteria/guidance; and SIGPLAN's official
empirical-evaluation page/FAQ. Citations above link directly to
each. These passages informed specific recommendations, not a new systematic
novelty audit. The Arm documentation is current; the pinned historical library
source would still need inspection for any new baseline claim.

ACM's main artifact-policy URL returned 403; its alternate policy URL and
publisher-host endpoint also failed. No unseen general ACM rule was inferred.
The SIGSIM-PADS page was fully accessible and is cited only for its own stated
practices. The SIGPLAN page/FAQ was fully accessible; its linked checklist PDF
failed web extraction because the server returned `application/octet-stream`,
so no unread checklist detail is claimed. Author-uploaded transcriptions supplied the two older FIR/width
papers; their algorithms were not reproduced. This turn performed only
read-only result inspection, the explicit sensitivity arithmetic check and
writing this recommendations file, with no new target experiment.

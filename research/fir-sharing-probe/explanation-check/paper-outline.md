# Paper outline: baseline fairness and compiler-dependent FIR costs

20 October 2026. Reusable outline for the bounded college empirical paper.
The completed comparison is the result; the two-binary causal section is
**pending peer delivery and independent/manual acceptance**. The outline does
not predict that explanation, a publication outcome or a grade. Detailed claim
boundaries and inherited source-access provenance are in [claims.md](claims.md).

## Working title and abstract

**Working title:** *Arithmetic-Fair Baselines Change FIR Implementation Rankings:
A Cortex-M0 Model Case Study*

**Abstract draft:** Constant-multiplication sharing can reduce FIR arithmetic
counts, but a fair software comparison must also account for arithmetic width
and recurring execution costs. We examine one fixed 48-tap, full-int16 FIR with
exact floor/saturating output on a pinned Cortex-M0 model. A direct control uses
two certified int32 partial sums and a single int64 reduction. Across two GCC
versions and block sizes 1 and 64, this correction changes the modeled-energy
winner: partial direct wins both GCC10 configurations, while demand Hcub wins
both GCC15 configurations. At GCC15/block64, Hcub's 32.94% saving relative to
unrolled CMSIS becomes 5.23% relative to corrected direct. If compiler choice is
also allowed, the best tested Hcub/direct modeled-energy margins are 3.97% and
2.30% for blocks 1 and 64. We report exactness checks, event costs and resource
diagnostics for the frozen 257-sample zero-history stream. These observations
support a bounded baseline-sensitivity case study, not a new FIR algorithm or
a physical-energy claim.

Do not insert a sentence attributing the block1 difference to spills or a
specific compiler mechanism until the causal section passes the acceptance
criteria below. If attribution remains unresolved, say so in the submitted
abstract only if the compiler explanation remains a central stated contribution.

## 1. Question and contribution

Ask: after direct and transposed forms receive comparable range information,
which tested implementation has lower complete-stream modeled cost for this
fixed filter, compiler and block size? Then ask what can explain the difference
between the two existing block1 direct binaries.

State the contributions as a certified stronger direct comparator, the corrected
four-configuration observation and a reproducible evidence package. Qualify any
later explanatory contribution by the final manual verdict. Explain that a wide
final result does not force wide arithmetic in every partial, and that graph
operation count alone cannot rank this complete execution. Both are established
principles tested in this particular artifact, not new theorems or algorithms.

## 2. Closest prior work and scope of originality

Use a short related-work section, not a generic FIR survey. Cite the primary
1998 bit-true generation manuscript, SPIRAL FIR (2003), XScale fixed-point
runtime/energy work (2007) and Hcub (2007), linked with access details in
[claims.md](claims.md). Discuss their direct overlap with semantics/range
specialization, locality/register effects, embedded generation and graph costs.
Use official precision-bound documentation and the Doppler narrow-partial/wide-
reduction documentation as supporting context, clearly identifying the latter's
implementation-documentation status and differing quantizer.

Distinguish this worker's inherited literature assessment from fresh full-text
reading. Restricted abstracts/indexed passages cannot support detailed method
equivalence. Do not claim an exhaustive review, firstness, an invented partial-
sum technique or novelty merely from a different processor.

## 3. Numeric contract and implementations

Define the FIR mathematically with frozen coefficient order, zero initial
history and output `sat_int16(floor(sum / 32768))`. Define the allowed input
domain as all int16 values. Explain why test-vector agreement and arithmetic
safety are different obligations.

Show the fixed groups `[0,2)`/`[2,48)` and the three absolute bounds:
418,709,504; 1,957,265,408; 2,375,974,912. Explain prefix/product safety in int32,
converting both partials to int64 before their addition, and applying exactly one
quantizer. Briefly show negative-floor and saturation behavior without relying
on implementation-defined signed right shift.

Describe the actual compared forms: unrolled CMSIS, the former wide specialized
direct control, corrected partial direct, ordinary mixed-width transposition and
demand Hcub transposition. Treat Hcub-versus-ordinary transposition as the relevant
incremental sharing comparison; library-versus-Hcub combines multiple changes.
Retained transposed state and direct history have distinct layouts. No partition
search, optimizer or exhaustive implementation selection is claimed.

**Table 1:** candidate definitions, arithmetic/state choices and comparison role.
**Small listing:** the two partial declarations, widened reduction and quantizer;
reference the full frozen kernel rather than printing 48 tap statements.

## 4. Experimental protocol and evidence admission

Record GCC 10.3.1/GCC 15.2.Rel1, Cortex-M0 Thumb, `-O2`, no LTO; simulator
commit `c55ea1b1926b792d7aabb7e3495b55a7b69ef134`; coefficient/input/source/binary
hashes and reproducible commands. The stream is the same saved 257 ADC samples,
starting from zero history. Blocks are 1/64; the final block64 call has one sample.
Explain the exact boundary including stream/call work, input copy, convolution,
quantization/store and history update, while excluding setup and printing.

Summarize the completed independent output/history/guard, raw-event, artifact,
arithmetic and emitted-code checks from
[join-review.md](../independent-check/join-review.md). Distinguish the separate
signed-edge/UBSan correctness checks from performance observations. They are
admission evidence, not extra timed workloads or statistical replications.

Define estimated timing from the Arm-table event formula and estimated CPU
energy from the saved Nikov model weights at 20 MHz, prefetch off and zero wait
states, assuming single-cycle MUL. Cite the primary model via
[claims.md](claims.md). State that local simulator ticks are not physical cycles,
energy is not board/end-to-end energy and the source model's 2.80% MAPE is not
our uncertainty bound. No physical uncertainty calibration is available.

**Table 2:** exact contract, workload, toolchain/model settings, measurement
boundary and evidence identities. Put long hash manifests in an appendix.

## 5. Results: corrected comparison and resource tradeoffs

Use [the admitted comparison](../independent-check/comparison.md) and unrounded
[verification totals](../independent-check/verification.json). Keep all four
configurations visible. Report nJ/output and estimated cycles/output together
with state allocation, selected-symbol code size and compiler frame diagnostics.

**Table 3:** corrected direct, ordinary transposed and demand Hcub for both
compilers and blocks; retain named historical controls alongside or in an
appendix. Hcub relative energy is +4.33%, +5.00%, −24.06%, −5.23% in
GCC10/block1, GCC10/block64, GCC15/block1, GCC15/block64 order, with corrected
direct as the denominator. Estimated-cycle winners agree for these rows.

**Figure 1:** paired modeled-energy comparison before/after direct correction,
faceted by compiler/block. Label every comparator. At GCC15/block64, distinguish
the 32.94% CMSIS-relative saving from 5.23% corrected-direct saving. Do not label
the full library gap “sharing benefit.”

**Table 4:** selected resource comparison demonstrating that fewer instructions
and MULs can lose under this model: GCC10/block64 Hcub/partial direct has
116,139/129,481 instructions, 257/2,827 MULs, 24,689/13,695 RAM reads and
20,083/1,848 writes. Add the direct state allocation of 98/224 bytes versus
transposed 192 at block1/64. Define selected-symbol bytes as excluding fixture
code and potentially other helpers; `probe_process` frame bytes are not peak
stack or SRAM high-water usage.

Explicitly answer the separate selectable-compiler question: best tested Hcub
uses GCC15, best tested partial direct uses GCC10, and Hcub is 3.97%/2.30%
lower modeled energy at block1/64. This does not contradict fixed-GCC15
24.06%/5.23%; it changes the feasible alternatives. Avoid a physical winner
claim from these small modeled margins. Preserve the old 12/24 bank statistic
only as historical context for its original candidate set; there is no revised
bank-wide result.

## 6. Two-binary explanation — pending

**Present status: no peer directory/report at preparation; no component
attribution is accepted.** This section can presently report only the aggregate
GCC15-minus-GCC10 block1 partial-direct differences:

| Metric | Frozen delta |
|---|---:|
| Instructions | +43,820 |
| RAM reads | +13,878 |
| RAM writes | +19,275 |
| Taken branches | +131 |
| MUL / flash reads / flash writes / BL | 0 each |
| Timing estimate over stream | +77,235 |
| Modeled CPU energy over stream | +70,469.699925 nJ |
| Compiler-reported `probe_process` frame | 72 → 240 bytes |

Reserve **Table 5** for component event/cost deltas and **Listing 2** for a short
annotated assembly pair. Do not populate them from static opcode counts or
invent fractions of overhead. The seven component categories and requirements
are specified by the shared plan and [claims.md](claims.md).

Admission requires exact binary/raw-event identities, independently reconciled
totals, hashed PC/control-flow or reconciled dynamic evidence, and manual
source-value/stack-slot review. Trace-based accounting must match original
outputs, histories, guards, markers and aggregate events. The checker can find
arithmetic inconsistency but cannot certify semantic labels or causation.
Distinguish ABI saves and stack-resident temporaries from demonstrated spills;
do not infer a compiler bug from extra traffic. Keep residual events explicit.

After `final-decision.md`, choose one honest ending: a supported bounded
mechanism; a partial explanation with the residual shown; or an unresolved
attribution. If ordinary lowering/stack traffic explains the difference, retain
the modest empirical/baseline-correction framing. No outcome creates a new FIR
algorithm or authorizes new performance rows.

## 7. Discussion and threats to validity

Address the strongest objection directly: a selected single-filter example and
standard arithmetic correction can be useful engineering without substantial
research novelty. Explain what the corrected evidence teaches locally and how
the unfavorable GCC10 Hcub rows constrain the headline.

Separate full-domain arithmetic validity from finite-stream cost observations;
zero history, startup/short-call work, input-dependent paths, the pinned compiler
versions and the cost model limit transfer. These are already-inspected cases,
not held-out validation. The fairer direct control is not an optimal direct
implementation. State/frame/code diagnostics do not establish peak SRAM or
total executable size. The literature assessment is targeted and access-limited.
No new filter bank, platform, optimizer, compiler-flag sweep or physical campaign
belongs to this assignment.

## 8. Conclusion and reproducibility appendix

Conclude that arithmetic fairness changes this local decision and that a
graph-count-only or globally-wide-direct inference is inadequate for this case.
Summarize the opposite compiler winners, exact comparator and model scope.
Include only an explanation accepted in `final-decision.md`; otherwise retain
an explicit unresolved causal question. Do not promise broader selection rules,
physical savings, publication or an evaluation outcome.

Append the artifact manifests, archive-restore instructions and independent
checker commands from the completed join and USER workstream README when
available. Keep historical performance verification distinct from forthcoming
explanation consistency checks. Record actual test/review results from their
owners rather than treating this outline or fixture success as peer certification.

The writing task can proceed now with Section 6 marked pending. Final causal
integration waits for peer delivery; the four-row empirical result does not.

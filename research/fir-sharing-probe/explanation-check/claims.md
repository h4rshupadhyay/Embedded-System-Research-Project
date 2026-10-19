# Claim and evidence assessment

20 October 2026. This is the USER workstream's contribution synthesis for the
[compiler-explanation plan](../../../docs/superpowers/plans/2026-10-20-fir-compiler-explanation.md).
The arithmetic-fairness comparison and bounded two-binary explanation are
complete. The actual peer accounting passed independent numerical admission;
manual review accepts a **partial** generated-code explanation. See
[final-decision.md](final-decision.md) for the evidence, residual and review.

## Research question and recommended contribution

**For the frozen full-int16 `speech_minphase48` FIR on the pinned Cortex-M0
model, how does giving direct accumulation certified int32 partial sums change
the direct/transposed implementation decision, and what generated-code evidence
can account for the remaining GCC10/GCC15 block1 direct-cost difference?**

The first part is answered by the completed comparison. For the second, proved
extra direct-SP transfers account for all additional RAM traffic and 85.0151%
of the modeled energy increase; the remaining costs and compiler-pass cause
remain unresolved. The useful scope is a reproducible case study of baseline
correction and compiler-dependent costs.
It is not a search for the best possible FIR implementation.

Recommended central claim:

> For one bit-exact 48-tap FIR and a fixed finite stream under a Cortex-M0
> event-cost model, replacing globally wide direct accumulation with two
> certified native-width partial sums changes the tested implementation ranking.
> Corrected direct has lower modeled CPU energy in both GCC10 configurations;
> demand Hcub has lower modeled CPU energy in both GCC15 configurations.
> In this case, a wide final sum does not require every direct partial to be
> wide, and fewer multiplication-graph operations do not establish a lower
> complete-stream modeled cost.

Accepted explanatory addition: for these two block1 direct binaries, GCC15
retains and rotates many history samples through stack slots before testing the
output-loop exit. The extra executed direct-SP loads/stores account for the
entire RAM-traffic delta and most of the modeled cost increase. This identifies
emitted value lifetimes and their event costs, not the responsible compiler pass
or a counterfactual optimization saving.

The original contribution is the **local observation, stronger control and
inspectable evidence** under this exact contract. Range-aware arithmetic,
narrow-partial/wide-reduction accumulation, FIR locality transformations and
Hcub sharing are established techniques. The current work establishes neither
a new algorithm nor substantial field novelty. A useful college empirical paper
is defensible; publication and the evaluator's grade are not implied.

## Evidence contract

- Filter and coefficient identity: frozen `speech_minphase48`, 48 taps; full
  signed-int16 inputs, including −32768; no changed filter or partition search.
- Arithmetic: exact products and partial prefixes; fixed coefficient groups
  `[0,2)` and `[2,48)` have L1 sums 12,778 and 59,731. Conservative absolute
  bounds are 418,709,504 and 1,957,265,408, both within int32. The full bound
  2,375,974,912 exceeds int32. Each partial is converted to int64 **before**
  addition; output is `sat_int16(floor(exact_sum / 32768))`, applied once.
  The C implementation clamps before narrowing and implements negative floor
  without assuming arithmetic signed right shift. This argument and emitted-code
  review support arithmetic validity; finite output tests alone do not prove it.
- Performance observations: 257 saved ADC samples, zero initial history,
  GCC 10.3.1 and GCC 15.2.Rel1, Cortex-M0 Thumb, `-O2`, no LTO, blocks 1/64.
  Recurring stream/call work, input and history movement and the final short
  call are inside the fixed measurement boundary; setup and printing are outside.
- Current explanation: only the two existing **block1 partial-direct binaries**.
  Block64 and transposed rows remain comparison context, not targets of a new
  explanatory measurement. Binary identities and all source hashes are fixed
  by the plan. No new target measurements were made for this synthesis.

The completed [join review](../independent-check/join-review.md) records
artifact/output/history/guard checks, arithmetic review and assembly inspection.
Those are inherited evidence findings, not fresh reruns by this document worker.
This worker read the source kernel and independently recalculated the percentages
below from unrounded totals in the saved
[verification report](../independent-check/verification.json).

## Comparator discipline

For a fixed compiler/block, relative Hcub cost is
`100 * (E_Hcub / E_partial_direct - 1)`; savings use its negative.
Every energy value is a **modeled CPU-energy estimate**, not measured board energy.

| Compiler | Block | Partial direct nJ/output | Demand Hcub nJ/output | Hcub relative cost | Lowest modeled-energy candidate in the compared set |
|---|---:|---:|---:|---:|---|
| GCC10 | 1 | 1036.55 | 1081.44 | +4.33% | Partial direct |
| GCC10 | 64 | 575.81 | 604.62 | +5.00% | Partial direct |
| GCC15 | 1 | 1310.75 | 995.43 | −24.06% | Demand Hcub |
| GCC15 | 64 | 593.59 | 562.55 | −5.23% | Demand Hcub |

If compiler choice is allowed, compare each form's best tested compiler per
block: GCC15 Hcub against GCC10 partial direct. From whole-stream totals,
`100 * (1 - 255825.284195 / 266394.093850) = 3.96735885%` for block1 and
`100 * (1 - 144576.380656 / 147984.280421) = 2.30287957%` for block64.
Thus **24.06%/5.23%** answer the fixed-GCC15 question;
**3.97%/2.30%** answer the selectable-compiler question. The latter are minima
over tested forms/builds, not optimality claims. These small modeled margins have
no calibrated physical uncertainty bound in this study.

At GCC15/block64, the old **32.94%** saving uses `cmsis64_unroll` as its
denominator; the corrected **5.23%** uses `partial_direct32x2`. The library-relative
number remains valid with that comparator named. The entire library gap cannot
be assigned to Hcub sharing: use `trans_const` versus `trans_hcub_demand` to
discuss the incremental effect of this sharing implementation. Ordinary
transposition beats corrected direct only at GCC15/block1. The historical
**12/24** bank finding belongs to the original candidate set; no bank-wide result
with equally narrowed direct controls exists.

## Claim/evidence matrix

| Claim | Evidence available | Status and boundary |
|---|---|---|
| The corrected direct form is valid for the stated full-int16 arithmetic contract. | Fixed group bounds, widening before addition and single quantizer in [kernel.c](../partial-direct/kernel.c); signed-edge/UBSan/output/history/guard and assembly findings in [join review](../independent-check/join-review.md). | Supported for this implementation and contract by combined reasoning and checks. The timed 257 samples do not prove all-stream correctness or represent all input workloads. |
| The stronger baseline changes the local implementation winner. | Four admitted configurations and controls in [comparison.md](../independent-check/comparison.md); unrounded [verification.json](../independent-check/verification.json). | Supported empirical observation: GCC10 direct wins twice, GCC15 Hcub wins twice. Neither universally superior. |
| Lower arithmetic counts can coexist with higher complete-stream modeled cost here. | GCC10/block64 Hcub versus partial direct: instructions 116,139/129,481, MULs 257/2,827, reads 24,689/13,695, writes 20,083/1,848; Hcub costs 5.00% more. | Supported counterexample under the fixed model; it does not establish a general selector or new mechanism. |
| Narrowing direct improves the old wide-direct control materially. | GCC10/block64 `spec_direct` to partial direct: 990.40 to 575.81 nJ/output; writes 25,497 to 1,848. | Supported paired result; it is a baseline correction, not proof of optimal partitioning or best direct code. |
| The two block1 direct builds have substantially different compiled costs. | Frozen totals: instructions 198,670/242,490; reads 29,304/43,182; writes 17,225/36,500; frame bytes 72/240 (GCC10/GCC15). | Supported aggregate observation. Frame size and stack accesses alone do not prove spills, their causes or a compiler bug. |
| Executed stack transfers explain most of the block1 direct cost increase. | Actual two-row accounting, 29 verified evidence hashes, manual path/value-flow inspection and independent binary review in [final decision](final-decision.md). GCC15 executes 54 more direct-SP loads and 75 more stores per call, over 257 calls. | **Supported partial attribution:** all +13,878 reads/+19,275 writes and 59,909.909673 nJ of the 70,469.699925 nJ modeled increase (85.0151%). Residual +10,667 instructions/+131 branches stays unattributed; compiler pass and spill cause remain unproved. |
| Direct/transposed choices trade code, state and stack resources. | Selected-symbol sizes, allocation sizes and compiler frame reports in the saved verification report. Direct state is 98/224 bytes at block1/64; transposed state is 192. | Supported diagnostics. Selected-symbol size is not total image size; `probe_process` frame is not peak stack or measured SRAM high-water usage. |
| The work saves physical energy or generalizes across filters/cores. | No board measurements, physical uncertainty calibration, revised filter bank or held-out workloads. | Unsupported. Full-int16 arithmetic guarantees do not generalize a timing/energy ranking beyond the measured stream/model. |

## Established-method overlap and source-access provenance

**Access for this note is inherited, not fresh.** The source descriptions below
come from the [post-join research assessment](../../fir-post-join-research-assessment.md)
and [positioning note](../independent-check/positioning.md). Their authors recorded
the access stated in this table; this worker read those repository notes, not the
linked full texts. No new literature search or primary-source retrieval was
performed. Links identify the original sources, and overlap judgments are
synthesis of the recorded assessment rather than a priority clearance.

| Primary source | Inherited access and relevant established result | Consequence for this paper |
|---|---|---|
| De Coster et al., *Code Generation for Compiled Bit-True Simulation of DSP Applications* (1998), [manuscript](https://cecs.uci.edu/~papers/compendium94-03/papers/1998/isss98/pdffiles/1_2.pdf), §§2–5 | Recorded full manuscript inspection: finite-word-length semantics, target operators/storage and a FIR example using magnitude analysis to avoid unnecessary overflow handling. | Closest inspected precedent for broad exact-semantics arithmetic specialization. Its DSP56000 simulation/emulation setting differs, but “range-aware exact FIR generation” is too broad a novelty claim. |
| Gačić et al., *Fast Automatic Software Implementations of FIR Filters* (2003), [author manuscript](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf), §§4–5 | Recorded full text: FIR locality/blocking alternatives with identical arithmetic counts and differing runtime; in-register work matters on Pentium 4/UltraSPARC II. | Computation order and register/memory effects are established. Our exact integer contract and local compiler reversal remain artifact-specific observations. |
| D'Alberto et al., *Performance/Energy Optimization of DSP Transforms on the XScale Processor* (2007), [author manuscript](https://users.ece.cmu.edu/~franzf/papers/hipeac07.pdf), §§2.2–4 | Recorded full text: generated fixed-point FIR C, vendor-library comparison, runtime and physically measured energy under platform configurations. | Embedded fixed-point generation and energy comparison are established; the physical experiment supplies no physical validation of our simulator results. |
| Voronenko and Püschel, *Multiplierless Multiple Constant Multiplication* (2007), [author manuscript](https://spiral.ece.cmu.edu/pubs/synth.pdf), §1.2/graph costs | Recorded full text: shared shift/add/subtract graphs; add/subtract objective leaves out other objectives including generated-code register pressure. | Hcub application and the inadequacy of graph counts as a complete software-cost model are not new algorithms or mechanisms. |
| MathWorks, [FIR precision rules](https://www.mathworks.com/help/dsp/ug/fixed-point-precision-rules-for-avoiding-overflow-in-fir-filters.html) | Recorded official documentation inspection: input/coefficient bounds determine overflow-free full precision. | Applying such a bound to a coefficient group is elementary; our prefix safety and C type handling require local proof. |
| Doppler, [HalfbandDecimatorQ15](https://doppler-dsp.github.io/doppler/gallery/hbdecim_q15/) | Recorded first-party documentation: int32 AVX2 accumulation lanes, int64 reduction, round-to-nearest output; code/lane safety not independently validated. | Close narrow-partial/wide-reduction precedent, with different SIMD/halfband/quantization choices. Documentation is not peer-reviewed proof of our construction. |
| Ménard and Sentieys (2004), [publisher abstract](https://link.springer.com/chapter/10.1007/978-3-540-30113-4_16); Rao and Lou (2022), [publisher article](https://www.mdpi.com/2079-9292/11/11/1721) | Respectively abstract only; and indexed abstract/substantial §§1/3 passages after direct retrieval failed. The notes report processor-aware word-length selection and hardware local-sum/multiplication-accumulation co-optimization. | These prevent broad invention claims; access limits preclude asserting detailed algorithmic equivalence to our exact scalar contract. |

This targeted overlap assessment does not show that all closer work has been
found. “Different target” and “no identical experiment found in these notes”
are insufficient to establish substantial novelty or firstness.

## Model and causal acceptance limits

The pinned simulator commit is `c55ea1b1926b792d7aabb7e3495b55a7b69ef134`.
Timing is the saved Arm-table estimate
`instructions + ram_reads + ram_writes + flash_reads + 2*taken_branches + bl`,
assuming zero wait states and single-cycle MUL. Simulator ticks are not hardware
cycles. Energy uses the saved non-MUL/MUL/branch/RAM/flash event weights from
Nikov et al.'s [20 MHz, prefetch-off, zero-wait CPU model](https://arxiv.org/html/2301.12806v1),
as documented in the inherited assessment. Its reported 2.80% MAPE is from its
own workload evaluation, not an error bar or pairwise confidence bound for our
FIR comparisons. No local cycle-accuracy, physical-energy or end-to-end-system
validation is inferred from that paper.

The frozen GCC15-minus-GCC10 block1 delta is 43,820 instructions,
13,878 RAM reads, 19,275 RAM writes and 131 taken branches; MUL, flash reads,
flash writes and BL are unchanged. The timing-estimate delta is 77,235 and the
modeled CPU-energy delta is 70,469.699925 nJ over the stream. These totals define
the total reconciled by the accepted partial explanation. Extra direct-SP
transfers contribute 33,153 instructions, 66,306 estimated cycles and
59,909.909673 modeled nJ. Residuals are 10,667 instructions, 131 branches,
10,929 estimated cycles and 10,559.790252 modeled nJ. The percentage explained
uses the energy-increase denominator; it is not a physical measurement or a
predicted improvement from removing the transfers.

The completed acceptance gates were:

1. Admit exactly the two frozen binaries and raw logs; verify report and evidence
   identities, safe paths, schema and independent reconstruction of every total.
2. Reconcile each of eight counters across `stream_wrapper`, `copy_in`,
   `convolution`, `quantize_store`, `history_copy`, `function_entry_exit` and
   `unattributed`, with each component present once. MUL is a subset of
   instructions; counter categories are not eight disjoint instruction classes.
3. Require exact execution-frequency/control-flow support or a reconciled dynamic
   trace for attributed counts. Static opcode sites times 257 are insufficient
   without proof of all paths/frequencies. Residuals stay `unattributed`;
   zero unsupported counts do not mean the operation was absent.
4. Manually inspect hashed PC ranges and source-value/stack-slot annotations for
   both partial sums, a recurring stack-resident arithmetic value and ABI saves,
   or record what cannot be mapped. “Spill” needs value-flow/compiler support;
   “stack-resident temporary” is the appropriate weaker description otherwise.
5. If diagnostic replay is used, retain logging-only changes and reconcile
   outputs, histories, guards, all events and marker boundaries to the frozen
   runs. It adds explanatory evidence, not replacement performance rows.
6. Keep numerical `consistent` separate from manual causal judgment.
   [final-decision.md](final-decision.md) records partial acceptance. The
   automated report's `manual_causal_review="pending"` remains unchanged by
   design; a consistent mislabeled PC range can pass arithmetic checks.

No diagnostic replay was needed. Both the coordinator and fresh fallback
reviewer enumerated ten syntactic quantizer paths per compiler and found the
same once-per-call SP sequence on every path, excluding GCC10's zero-block-only
store. The repeated history-copy body contains no direct-SP accesses. The
reviewer also compared disassembly bytes with the binary and recomputed saved
outputs and retained history. Those checks support this fixed-fixture frequency
argument; they are not a dynamic trace or a new performance measurement.

## Strongest objection and what would weaken the recommendation

The strongest reviewer objection is: **this corrects an initially weak baseline
using standard arithmetic specialization, then reports ordinary compiler
sensitivity for one selected filter and short stream under an uncalibrated local
cost model. What research insight remains beyond competent implementation?**
The response is the fully disclosed baseline correction, opposite compiler
winners, resource tradeoffs and reproducible evidence, now with a bounded
sample-lifetime/stack-traffic explanation. It makes the case study more
informative without making known mechanisms new. Present the remaining
unattributed costs and keep the paper claim modest.

The recommendation would weaken if artifact or boundary mismatches undermine
comparability; a valid-domain arithmetic counterexample invalidates a candidate;
independent costs fail to reconcile; or plausible component sums lack executable
or value-flow support. An explanation limited to routine stack traffic reduces
the explanatory novelty, though it does not erase the corrected observation.
Closer prior work reproducing the same combination would further narrow
originality. Evidence that the small cross-compiler margins reverse under a
validated physical setup would weaken a physical implementation recommendation;
it would not retroactively change these model results. No such new experiment is
authorized here. If the assignment requires a substantial new algorithm rather
than an empirical study, this paper does not meet that requirement. Stop after
the bounded two-binary explanation rather than expand the benchmark to seek a
more favorable headline.

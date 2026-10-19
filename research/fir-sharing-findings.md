# Exact state width and scheduling in FIR coefficient sharing

20 October 2026. Completed bounded exploratory probe; FIR only, simulator only. [Protocol and review correction](fir-sharing-probe/PROTOCOL.md), [raw results](fir-sharing-probe/results.json), [derived analysis](fir-sharing-probe/analysis.json), [complete comparison](fir-sharing-probe/comparison.md), [source provenance and closest work](fir-sharing-source-provenance.md).

**Subsequent pursuit audit, 20 October:** The recommendation below is now **conditional on a missing direct-arithmetic control**. The headline minimum-phase48 full-range filter permits two exact int32 partial sums followed by one int64 reduction; the current direct/folded controls instead use int64 throughout when the global bound fails. No performance comparison against that narrow-partial control has been run. Existing measurements remain valid for the tested set, but proceeding directly to the paper's central claim was premature. See [the independent pursuit audit and minimal decision gate](fir-sharing-pursuit-audit.md).

## Decision

**Proceed with a narrowly scoped empirical paper about exact state precision, coefficient sharing and compiled streaming cost. Do not build a general optimizer or claim a new FIR algorithm.** The probe found actual positive and negative cases against stronger controls, and the ablations identify distinct causes. That is a firmer contribution candidate than the earlier arithmetic-only selector. This is our assessment of research value, not a guarantee of grading, publication or first-of-kind priority.

Suggested working title: **Exact State Width and Scheduling in Multiplierless FIR Software on Cortex-M0**.

The specific question is: *When can established transposed coefficient sharing outperform direct, symmetry-folded and library FIR software once exact retained-state widths and generated-code costs are included?*

The candidate contribution is the controlled evidence and explanation of this boundary. Hcub, transposition, suffix range analysis and dependency-driven emission are existing techniques. The study does not establish an unresolved compiler defect, a globally optimal schedule, or a transferable selection rule.

## Experiment and correctness

Three existing designs were fixed before target evaluation: speech lowpass48, nonsymmetric minimum-phase speech48, and vibration bandpass192. These are application-motivated synthetic filter designs, not validated production specifications. The original integer coefficients are unchanged. Each stream contains 257 existing ADC11 samples and zero initial history; blocks 1 and 64 include final short calls. The same samples are admitted under both ADC11 and full-int16 guarantees. Repeated guarantees isolate admissibility/width effects, not independent data distributions. Builds use GCC 10.3.1 and 15.2.Rel1, Cortex-M0 Thumb, `-O2`, no LTO.

Every implementation computes the exact integer FIR followed by `clip_int16(floor(sum/32768))`. Controls include safely admitted generic direct/folded implementations, default and unrolled standard/fast CMSIS-DSP v1.14.4, compile-time coefficient-specialized direct/folded kernels, transposed ordinary constant products, independent CSD expressions, and the authors' original Hcub graph with eager and dependency-driven emission. No graph/seed/schedule search used measured costs. State is **volatile SRAM retained between calls**, not nonvolatile checkpoint state.

The 24 primary groups contain **256 measured binaries**. Another **34 target edge binaries** check full-range signed samples. A separate post hoc width ablation adds **four binaries**. All **75,830 target output comparisons** match the arbitrary-precision unfolded reference, with correct retained state and guards. The primary measurement and edge checks account for 74,802 of those comparisons; the post hoc ablation contributes 1,028. There are only 771 distinct primary reference positions and 795 distinct target-edge positions: repeated builds are not independent applications.

Host UBSan checks separately passed **23,862 output comparisons**, mixed block partitions, extrema/sign-aligned inputs, state reconstruction and guards. All ten existing baseline test methods pass. Eight original assembly microchecks pass under the reused timing/event model. The artifact verifier regenerates all emitted sources, reconstructs references/states, checks artifact/dependency hashes, parses saved raw event logs, recomputes costs and verifies complete primary-case accounting. These checks do not formally verify the compiler or ISS.

## Main result: sharing can help, but it is not a universal winner

Transposed kernels have the lowest modeled CPU energy in **12/24** primary groups: dependency-driven Hcub in ten, ordinary constant products in two. Nontransposed controls win the other twelve. Hcub wins occur in one GCC10 group and nine GCC15 groups; the **best transposed family** wins three GCC10 and nine GCC15 groups. These are descriptive counts for this fixed bank, not estimated probabilities. Timing estimates have transposed winners in 10/24 groups, illustrating that close modeled-energy rankings need separate interpretation.

Illustrative GCC15, block64 results, nJ per output:

| Filter / guarantee | Strongest tested nontransposed control | Control | Dependency-driven Hcub | Hcub overhead |
|---|---|---:|---:|---:|
| Speech lowpass48 / ADC11 | Specialized folded | 427.34 | 414.41 | −3.03% |
| Minimum-phase speech48 / full int16 | CMSIS standard, unrolled | 838.85 | 562.55 | −32.94% |
| Vibration bandpass192 / ADC11 | Specialized folded | 1637.40 | 1495.04 | −8.69% |
| Vibration bandpass192 / full int16 | Generic folded int64 | 2941.91 | 3509.43 | +19.29% |

For GCC10, even the short symmetric lowpass favors specialized folding over the best transposed candidate, by 3.42% at block1 and 22.86% at block64. Source-level product sharing therefore supplies neither a compiler-independent recommendation nor a guarantee that a multiplierless kernel is best. All winners are winners **within the tested set**.

## Attribution 1: exact output width does not determine every state width

After processing sample n, transposed state i equals

`z_i[n] = sum_{k=i+1}^{N-1} h[k] * x[n-(k-i-1)]`.

Consequently `M * sum_{k=i+1}^{N-1}|h[k]|` bounds its magnitude for a guaranteed input magnitude M. This follows directly from established linear range analysis; it is not a new theorem. Every state uses a certified 32- or 64-bit type, without intermediate quantization.

The minimum-phase48 full-int16 contract needs a wide output sum, but only **one of its 47 states** requires 64 bits under this sufficient proof; the other 46 fit int32. The state payload is 192 bytes, compared with 376 bytes for uniform int64 states. Direct logical history is 94 bytes; block buffers, alignment and stack are separate costs.

The post-evaluation GCC15 width control holds the graph, coefficients, input, block and output quantizer fixed, widening all transposed states to int64:

| Block64 kernel | Uniform int64 states | Certified mixed-width states | Modeled reduction |
|---|---:|---:|---:|
| Ordinary constant products | 1137.47 nJ/output | 602.87 nJ/output | 47.00% |
| Dependency-driven Hcub | 1157.45 nJ/output | 562.55 nJ/output | 51.40% |

Thus the 32.94% library-relative improvement cannot all be credited to Hcub: ordinary products with the same exact state representation already improve substantially. Hcub's incremental benefit over ordinary transposed products here is **6.69%**. With uniformly wide states, it instead costs approximately 1.76% more than ordinary products. This is an exploratory interaction result, not independent confirmation of a prediction formulated after inspecting it.

The long vibration filter exposes the losing regime: under full-int16, 92 of 191 states require 64 bits and the ABI allocates 1,136 state bytes; under ADC11 all 191 fit int32, allocating 764 bytes. On GCC15/block64 the Hcub family wins under ADC11 and loses under the full-range guarantee even though actual input samples are identical.

## Attribution 2: graph emission order changes target memory cost

Demand-driven emission is cheaper than eager emission in all 24 measured groups, by approximately 0.92–14.23% modeled energy. It computes dependencies as each ascending state update needs them; it is a conventional scheduling control, not a proposed new algorithm.

For GCC15/minimum-phase48/full-int16/block64, the same Hcub graph gives:

| Complete 257-sample stream | Eager | Dependency-driven |
|---|---:|---:|
| Instructions | 117,986 | 106,930 |
| Machine MUL instructions | 257 | 257 |
| SRAM reads | 31,623 | 22,628 |
| SRAM writes | 24,966 | 19,826 |
| Compiler-reported kernel stack | 408 bytes | 344 bytes |
| `probe_process` symbol size | 1,440 bytes | 1,352 bytes |
| Modeled nJ/output | 655.89 | 562.55 |

Disassembly of `probe_process` contains 313 versus 258 static SP-relative LDR/STR instructions. This is a static instruction count, not an independent count of dynamically executed spills. Together with identical state allocation and measured event deltas, it identifies changed compiled temporary/stack traffic as part of the emission-order effect. The experiment does not show the backend's schedule to be optimal.

Ordinary constant products and independent CSD expressions produce **byte-identical target binaries in all 24 groups**. The compiler already recovers that source rewrite. Hcub demand emission beats ordinary transposed products in 21/24 groups, with at most about 8.00% modeled savings and up to 3.41% overhead. Those incremental comparisons, not the full library gap, isolate the established graph/emission choice.

## Memory and code costs remain part of the result

For GCC15/lowpass48/ADC11/block64, specialized folding uses a 1,008-byte process symbol, a 200-byte reported kernel frame and a 224-byte state/block buffer. Demand Hcub uses 1,104 bytes, a 296-byte frame and 188 bytes of retained state. Its modest modeled-energy win is therefore accompanied by code/stack tradeoffs.

For the 192-tap Hcub kernel, moving from ADC11 to full-int16 raises the process symbol from 4,492 to 11,072 bytes and its reported frame from 1,072 to 2,392 bytes. These are compiler symbol/frame diagnostics, not whole-application Flash usage or measured stack high-water marks. [Analysis resources](fir-sharing-probe/analysis.json) retain every primary case. The target link uses the original 64 KiB Flash / 8 KiB SRAM budget.

## Research boundary and next work

[Hcub](https://spiral.ece.cmu.edu/pubs/synth.pdf) already shares constant products and recognizes register pressure as a relevant metric. [SPIRAL's XScale study](https://users.ece.cmu.edu/~franzf/papers/hipeac07.pdf) already generates embedded fixed-point FIR software and optimizes measured runtime/energy. The contribution cannot be FIR generation, multiplier removal, architecture tuning or energy optimization in general.

The narrower evidence distinguishes coefficient sharing from exact suffix-state width and from same-graph emission, while retaining complete stream costs and negative cases. As an example of guidance this can qualify, the [ASN Cortex-M application note](https://www.advsolned.com/implementing-fir-filters-with-the-asn-filter-designer-and-the-arm-cmsis-dsp-software-framework/) favors direct fixed-point realization for its large shared accumulator. Our examples show why wide output accumulation alone need not rule out exact transposed software. They do not refute all direct-form guidance or establish a universal replacement rule. A targeted literature check supports this empirical positioning; exhaustive novelty clearance has not been performed.

**Recommended next work is paper development around these controlled contrasts**, including the closest-work comparison and the exactness/state derivation. The bounded probe is complete. No general optimizer is justified by it. Any future transferable selection claim must be fixed before evaluation on new, independently justified filters; these now-inspected designs cannot serve as fresh validation.

Timing remains an Arm-table zero-wait-state estimate and energy remains the reused [configuration-specific CPU model](https://arxiv.org/html/2301.12806v1), not physical measurements. Especially the small 1–3% rankings lack a pairwise physical uncertainty bound. No claim is made about other cores, multiplier latencies, compiler flags, production filter prevalence or modern CMSIS versions.

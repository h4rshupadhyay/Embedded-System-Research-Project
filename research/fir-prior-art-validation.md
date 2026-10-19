# FIR prior-art validation: exact final-quantizer product skipping

Date: 19 October 2026. Scope: FIR only, fixed coefficients, simulator-only college project. This is a targeted primary-source audit, not an exhaustive priority search.

## Verdict

**The proposed implementation remains a plausible research hypothesis; originality is not established.** A particularly important precedent strengthens the need for a narrow claim: Pillai's 1999 thesis already describes bypassing an entire floating-point MAC, including product evaluation, when finite arithmetic precision makes its contribution ineffective. Therefore even “skip whole products because they cannot affect a finite-precision FIR result” is too broad as a novelty claim. See the primary-source comparison below.

The narrower candidate is a **collective residual certificate for an exact wide-integer FIR followed by a single fixed final quantizer**, organized so that streaming bound maintenance and certificate checks cost less than the omitted work. No inspected source here establishes this specific combination. Absence of an identified duplicate is not evidence sufficient to claim first invention.

The elementary interval stopping rule, coefficient absolute-sum bound, coefficient sorting, rolling maxima, symmetry folding and periodic checking should each be treated as familiar ingredients. A paper would need a distinctive organization, a nontrivial result about its operating limits, and/or convincing new overhead-inclusive evidence. Merely implementing the endpoint equality test is a weak contribution.

## Candidate being compared

Inputs and coefficients are signed 16-bit integers. The exact reference is

`S[n] = Σ h[i] x[n-i]`, `y[n] = clip_int16(floor(S[n]/32768))`.

All products, sums, paired pre-additions and bounds use sufficient width to prevent overflow. After a subset of terms is computed, let its exact sum be `P`, and certify that the collective remaining sum lies in `[L,U]`. Stop only when `Q(P+L) == Q(P+U)`. Monotonicity of the declared quantizer then gives the result for every allowed completion. This proof is an elementary deduction, not an experimentally discovered or claimed novel theorem.

The guarantee concerns the final quantized output; the full unquantized sum need not be reconstructed. It does not apply unchanged to modular wrapping or per-MAC saturation. The same FIR coefficients, input stream, final quantizer and complete output sequence must be used by every comparison.

## Closest primary sources

### 1. Pillai: an older whole-product/MAC bypass mechanism

Rajan V. K. Pillai, [*On Low Power Floating Point Data Path Architectures*, Concordia PhD thesis, April 1999](https://www.collectionscanada.gc.ca/obj/s4/f2/dsk1/tape4/PQDD_0021/NQ47712.pdf), Chapter 8, especially §8.3.3 (PDF page 146, one-based) and §8.5–8.6. The full PDF was downloaded and text-inspected in this audit. The [coauthor's publication list](https://users.encs.concordia.ca/~asim/publications.html) also identifies the related ISCAS 1999 paper, *Power Implications of Precision Limited Arithmetic in Floating Point FIR Filters*.

The thesis uses exponent differences to recognize when a product cannot change the current floating-point MAC result. It says both product evaluation and addition can then be bypassed. FIR examples include 16- and 64-order filters. This is a direct conceptual predecessor to whole-product omission driven by finite-precision insignificance.

Important qualification: §8.3.2 separately discusses multiplicand truncation with possible ULP error; do not label the entire architecture universally IEEE-exact. The described bypass is a local floating-point operation decision. Our candidate instead encloses **all remaining products collectively** under a wide-integer, single-final-quantizer contract. This difference is identifiable, but does not itself establish a substantial contribution.

### 2. Sinha and Chandrakasan: lossless data-dependent FIR precision

Amit Sinha and Anantha P. Chandrakasan, [*Energy Efficient Filtering Using Adaptive Precision and Variable Voltage*, ASIC/SOC 1999](https://citeseerx.ist.psu.edu/document?doi=60a96099691294f33629c9b4237880c3edf7bddc&repid=rep1&type=pdf), [DOI 10.1109/ASIC.1999.806528](https://doi.org/10.1109/ASIC.1999.806528).

The author paper describes distributed-arithmetic FIR hardware adapting to the bit precision required by incoming samples, with voltage adaptation under a throughput constraint. Its introduction explicitly characterizes the approach as preserving accuracy. Therefore lossless, input-dependent FIR computation/energy reduction is established prior work.

Its computation is organized around input bit slices and precomputed coefficient combinations, rather than sequential whole-product evaluation with a collective residual interval checked against the final quantization cell. Our distinction must concern that mechanism and its costs, not simply exactness or input dependence.

Access qualification: primary-paper indexed text, including its abstract/introduction and architecture snippets, was available; repeated direct PDF fetching timed out during this audit. The previous repository audit records full-text inspection. Do not treat the present retrieval as a fresh complete reread.

### 3. Distributed-arithmetic citation chain: incomplete computation is old

Rajeevan Amirtharajah, Thucydides Xanthopoulos and Anantha Chandrakasan, [*Power Scalable Processing Using Distributed Arithmetic*, ISLPED 1999, pp. 170–175](https://cecs.uci.edu/~papers/compendium94-03/papers/1999/islped99/pdffiles/07_1.pdf). Full primary paper inspected, particularly §3 and the FIR matched-filter application in §4.

The paper derives the residual between an MSB-first intermediate result and the final result, and analyzes successive approximation statistically. Its FIR matched-filter application reduces the number of processed input bits, explicitly trading detection performance for power. Thus partial computation, residual analysis and early completion in FIR-related distributed arithmetic are not new broadly. The inspected sections do not give our deterministic collective-residual/final-output-cell certificate. Statistical average error reduction is a different guarantee from equality of every output bit.

### 4. Ludwig: adaptive omission of FIR taps is old, with a different guarantee

J. T. Ludwig, S. H. Nawab and A. P. Chandrakasan, [*Low-Power Digital Filtering Using Approximate Processing*, IEEE JSSC, March 1996](https://dsp-group.mit.edu/wp-content/uploads/2024/11/Ludwig_Low-Power_DFiltering-1996.pdf). Full primary paper inspected.

Its FIR treatment adjusts filter order using signal statistics and explicitly considers adaptation overhead. This changes the effective filter and accepts a controlled quality trade-off. Our proposed contract instead preserves the complete fixed-reference output. “Adaptive tap skipping” alone is consequently an unsuitable novelty claim, and counting decision overhead is already an expected evaluation requirement.

### 5. Production fixed-point FIR contract

[Arm CMSIS-DSP FIR documentation](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html) documents the standard Q15 implementation's 64-bit accumulation and final truncation/saturation, and distinguishes the overflow behavior of the fast Q15 implementation. This supports the choice of a practical reference organization, not novelty. Pin the library version and check source/compiler semantics before using it as an exact executable baseline.

## Mechanism comparison

| Method | Unit of work reduced | Decision information | Numerical target |
|---|---|---|---|
| Pillai floating-point bypass | A local MAC, potentially including its multiplication | Product/current-sum exponent relation | Precision-limited local floating-point result; architecture has additional accuracy qualifications |
| Sinha adaptive precision | Distributed-arithmetic bit-slice cycles | Required precision of input samples | Accuracy-preserving filtering under its representation |
| Amirtharajah FIR matched filter | Distributed-arithmetic iterations | Selected input precision; statistical approximation analysis | Application-quality trade-off |
| Ludwig FIR order adaptation | Filter taps/order | Signal statistics and filtering-quality control | Approximate effective filter |
| Proposed candidate | Entire remaining groups/products for one output | Conservative collective residual interval plus current partial sum | Exactly the stated full integer FIR followed by the same final quantizer |

This table summarizes the cited sources above; the last row is the proposed design rather than a completed result.

## Follow-up: static input-domain residual bounds

A short targeted follow-up examined coefficient-tail bounds precomputed from a guaranteed input domain, followed by the same final-quantizer endpoint test. No explicit duplicate of this entire FIR early-exit mechanism was identified in the inspected primary sources. This limited result does not establish originality.

The bounds themselves are established FIR arithmetic. [MathWorks, *Fixed-Point Precision Rules for Avoiding Overflow in FIR Filters*](https://www.mathworks.com/help/dsp/ug/fixed-point-precision-rules-for-avoiding-overflow-in-fir-filters.html), explicitly derives output endpoints from sums of positive and negative coefficients and input-domain endpoints. [AMD/Xilinx FIR Compiler v6.2, DS795, March 2011, “Output Width and Bit Growth”](https://docs.amd.com/api/khub/documents/bLbPTlafc5j_a_fN6xpo5g/content), uses coefficient absolute sums to size accumulator growth. Neither inspected passage describes the proposed output-level early termination.

Applying the documented range construction to a coefficient tail is straightforward. Let `Hpos` and `Hneg` sum its positive and negative coefficients and let all remaining samples lie in `[a,b]`. Then `L=a*Hpos+b*Hneg` and `U=b*Hpos+a*Hneg`. These can be precomputed when `[a,b]` is a fixed ADC contract, eliminating runtime extrema maintenance and bound multiplications. The ADC domain must be guaranteed by the input representation or checked at a cost; extrema merely observed in a dataset are insufficient.

An equivalent algebraic form uses `H=Hpos+Hneg`, `A=Hpos-Hneg`, `T=(a+b)*H`, `D=(b-a)*A`, giving `L=(T-D)/2` and `U=(T+D)/2`. Both numerators are even for integer inputs/coefficients. This two-multiplication form for variable bounds is an algebraic rearrangement, not a novelty claim. Folded pairs need their correct pre-add domain, e.g. `[2a,2b]`, and zero-padded history must also satisfy the chosen domain.

Treat the static version as a strong inexpensive baseline. A data-adaptive method must justify its extra maintenance against it, as well as against folded full FIR. Switching to static bounds does not independently secure an original contribution; the basic bound plus final-cell test remains an elementary construction. The pilot's correctness counts and real-data performance are documented elsewhere and were not independently reverified by this literature audit.

## What the next pilot must establish

1. Specify one streaming bound implementation rather than treating “tighter bounds” as an unspecified novelty. Account for every magnitude update, group summary, comparison, metadata read and state update.
2. Preserve symmetry. For equal coefficient pairs use a wide pre-addition and compare against a folded full FIR. A certificate must bound those paired terms correctly. Halfband zero coefficients must already be absent from the baseline workload.
3. Compare a shared-window magnitude bound with a concrete tighter alternative, and distinguish the cost of obtaining a bound from the products it saves. An oracle using actual uncomputed products is an opportunity ceiling, not an implementable method.
4. Include dense ordinary amplitudes and quantization-boundary windows. A result confined to low-amplitude streams whose outputs nearly always become zero or minus one needs an explicit application justification.
5. Derive impossibility conditions and report failures. For an unsaturated shift-15 cell, a symmetric residual interval `[-R,R]` can fit only if `2R <= 32767`; equality of endpoint quantizations is still required. This is our direct arithmetic deduction.
6. Evaluate complete target execution before claiming energy efficiency. Python operation counts establish neither embedded timing nor energy. Software simulation supports only the claims justified by its pinned timing/energy model.

## Search boundary and unresolved priority questions

The audit followed the Sinha-to-distributed-arithmetic reference direction, directly inspected the older floating-point bypass thesis and its publication identity, and examined primary FIR arithmetic documentation. Targeted combinations included FIR/finite impulse response with exact early exit, early termination, quantization, remaining/partial sums, residual bounds and product bypass. Search results involving multiplier columns, asynchronous completion or changing filter coefficients were screened by mechanism rather than equated with an output-level residual certificate.

No exact duplicate of the proposed collective certificate was identified in the inspected sources. Citation coverage is incomplete, indexed terminology varies, and this is not a patentability/legal opinion. A responsible proposal states a **testable novelty hypothesis**, names the floating-point bypass precedent, and earns the eventual contribution through a specific method and evidence. If the implementation reduces to the basic triangle-inequality bound plus endpoint comparison and yields little overhead-inclusive benefit, the original-algorithm claim should be withdrawn or reframed.

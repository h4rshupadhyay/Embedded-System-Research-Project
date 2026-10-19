# FIR exact-skipping validation findings

19 October 2026. Initial literature and numerical feasibility study. This is not a completed embedded energy experiment.

## Decision

**Do not yet commit to the current certificate implementation as the final original energy-efficiency project.** Its arithmetic guarantee is sound under the defined contract, and the numerical checks found no mismatches. The novelty case is weaker than the original pitch suggested, and the opportunity on the tested real input leaves a small budget for overhead. Neither a distinctive algorithmic contribution nor net energy savings has been established.

This is not a proof that all exact FIR skipping is useless. It is a reason to revise the mechanism or research question before investing in a full target implementation. The immediate validation study is complete; the full project is not.

## What was investigated

The [method contract](fir-method-contract.md) fixes the reference as exact wide-integer FIR accumulation followed by `clip_int16(floor(S/32768))`. Coefficients and the complete output sequence are unchanged. Symmetric coefficient pairs are folded in both the proposed method and full-FIR baseline; zero coefficients are already removed.

The candidate encloses the uncomputed residual in `[L,U]` and stops only if `Q(P+L)==Q(P+U)`. The investigation compared:

- A maintained whole-window absolute-maximum bound.
- A maintained whole-window min/max bound, simplified to at most two logical multiplications per check.
- Precomputed endpoints for the full int16 input domain.
- For ECG streams, additional endpoints from the original guaranteed ADC domain, including its explicit scaled counterpart.

Natural and coefficient-magnitude orders were evaluated with checks every 1,4,8 groups or a single check leaving 4,8,16 groups. These are exploratory alternatives, not a trained switching algorithm or evidence that per-workload hindsight selection is deployable.

## What the closer literature check changed

The [primary-source audit](fir-prior-art-validation.md) found a particularly relevant predecessor: Pillai's 1999 thesis describes bypassing complete floating-point MACs in FIR filtering when precision makes a product unable to affect the current operation. Its broader architecture includes additional accuracy qualifications, so it is not an equivalent exact fixed-point reference. Nevertheless, **whole-product bypass based on finite-precision insignificance is not a new broad idea**. [Pillai, Chapter 8, especially §8.3.3](https://www.collectionscanada.gc.ca/obj/s4/f2/dsk1/tape4/PQDD_0021/NQ47712.pdf).

Lossless input-dependent FIR precision adaptation is also established by [Sinha and Chandrakasan, 1999](https://doi.org/10.1109/ASIC.1999.806528). Static signed-coefficient range endpoints are standard FIR analysis, explicitly documented by [MathWorks](https://www.mathworks.com/help/dsp/ug/fixed-point-precision-rules-for-avoiding-overflow-in-fir-filters.html).

The narrower collective residual/final fixed-point quantizer mechanism was not duplicated in the inspected sources. This remains a limited search result, not proof of priority. The interval certificate, suffix sums, coefficient ordering, symmetry folding and deque bounds do not independently constitute a strong original contribution. A distinctive low-cost organization or a substantive new empirical result is still needed.

## Reproducible numerical pilot

Run `python research/fir-streaming-pilot.py` from the repository root. This exploratory script writes [JSON results](fir-streaming-pilot.json) and [CSV results](fir-streaming-pilot.csv). It is a throwaway analysis probe, not a production library or an embedded timing implementation.

- Nine exactly symmetric integer filter designs: lowpass and bandpass at 64,128,256 taps; halfband at 63,127,255. Folded baseline products are respectively 32/64/128 and 17/33/65, with halfband zeros already omitted.
- Seventeen streams, each 4,096 samples, with zero initial FIR history. Eleven are synthetic amplitude, transition and diagnostic cases; six are three ECG segments evaluated at two fixed input scales.
- The real input is from SciPy's excerpt of MIT-BIH record 208, MLII, 360 Hz. Segment offsets are 0,36000,72000. Native centered ADC values and those same values multiplied by 16 are separate fixed input contracts; no clipping or signal-dependent scaling is used. These are test FIRs, not validated clinical filters. [SciPy data provenance](https://docs.scipy.org/doc/scipy/reference/generated/scipy.datasets.electrocardiogram.html), [original ADC header](https://physionet.org/files/mitdb/1.0.0/208.hea).
- Seed 20261019; dependency versions, integer coefficients, signal hashes and dataset checksum are saved in the JSON. The dataset checksum is verified before use.
- The initial run was inspected before simplifying the range expression and adding static bounds and the late4 schedule. The refined run is exploratory; its additional alternatives are not independent held-out confirmation.

### Correctness evidence

The refined run evaluated **6,156 configurations and 25,214,976 output comparisons, with zero mismatches** against full unfolded convolution. Those comparisons reuse **626,688 distinct filter/stream/output reference positions**; they are not 25 million independent workloads.

All scheduled residual intervals were checked against the actual residual, and maintained extrema against the actual window. An additional 10,000 checks exhaust small four-sample integer cases for two coefficient sets and an analogous saturating quantizer. Full-scale signed-input diagnostics exercise widening and some saturation cases. Together these support the numerical implementation and the general interval argument. They do not prove a compiled MCU implementation, its timing or its energy model correct.

### Representative work counts

For **128-tap lowpass, magnitude order, one check leaving eight folded groups**, the full folded baseline uses 64 products/output:

| Stream | FIR products omitted | Additional bound multiplications/output | Change in FIR + bound multiplication count |
|---|---:|---:|---:|
| Uniform integers -8…8 | 11.88% | 1 | 10.31% fewer |
| Uniform integers -128…128 | 2.37% | 1 | 0.81% fewer |
| Uniform integers -8192…8192 | 0.00% | 1 | 1.56% more |
| First ECG segment, native ADC scale | 0.74% | 1 | 0.82% more |
| First ECG segment, scale multiplied by 16 | 0.00% | 1 | 1.56% more |

These numbers concern the absolute bound. They differ from the earlier independent-window, unfolded product opportunity calculation because this is a different experiment with symmetry and a different checking schedule. They must not be interpreted as an isolated measurement of the effect of symmetry.

For the same **late8 absolute-bound configuration**, averaging equally across the three native-ADC ECG segments gives:

| Filter | Folded full-FIR products/output | FIR products omitted | Change after bound multiplications |
|---|---:|---:|---:|
| Lowpass 128 taps | 64 | 0.86% | 0.70% more |
| Lowpass 256 taps | 128 | 1.76% | 0.98% fewer |
| Bandpass 256 taps | 128 | 3.78% | 3.00% fewer |
| Halfband 127 taps | 33 | 0.01% | 3.02% more |

The **late4 range-bound** variant improves the native-ADC lowpass128 case: averaged across the same segments, it omits 4.47% of folded FIR products; adding its recurring bound multiplication leaves 2.90% fewer logical multiplications. The signed suffix happens to be zero at that checkpoint, so this case needs one rather than two bound multiplications. At scale ×16 it omits only 0.036%, leaving 1.53% more logical multiplications. This is an exploratory refinement, not a broadly validated winner.

### Why even positive percentages are insufficient

The count above includes only FIR and bound multiplications. It excludes certificate arithmetic, quantization, branches, coefficient-index metadata, memory behavior and rolling-bound maintenance. Logical multiplications of different widths may also have different target costs. This is **not a net-work, cycle or energy metric**.

For example, maintaining the absolute maximum for the first native ECG segment and a 128-sample window required about 1.96 deque value comparisons, 1.03 pushes, 1.03 pops and 1.03 absolute-value evaluations per output, including initialization. Maintaining min and max required about 3.92 comparisons, 2.06 pushes and 2.05 pops. These do not include every index, expiry or loop test, nor their memory accesses. Amortized counts hide per-output bursts. They cannot simply be converted into a multiplication or energy equivalent without a target model.

Frequent checking is also expensive: for lowpass128 on the first native ECG segment, the absolute bound with every8 checking omits only 0.745% of FIR products while performing about eight bound multiplications/output. Including those multiplications alone increases the count by 11.76%.

Static ADC bounds avoid rolling maintenance, but are looser. For magnitude order and late4 checking, they omit no products for lowpass128 on the native ECG segments; lowpass256 and bandpass256 averages are only 0.79% and 1.53%. A zero change in multiplication count still pays for a failed certificate. Static bounds are thus a necessary inexpensive baseline, not evidence that the idea has become practically effective.

## A useful analytical limit

For any interval `[L,U]` to fit in one unsaturated shift-15 cell, its integer width must satisfy `U-L <= 32767`. Endpoint placement must still agree, so this is necessary, not sufficient.

For a shared input domain `[a,b]` and remaining weighted coefficient absolute sum A, the signed-coefficient range bound has width `(b-a)*A`. Therefore:

- A full int16 domain has width 65535. Any nonzero remaining integer coefficient implies A≥1, so a static full-domain certificate cannot terminate an **unsaturated** output early. Saturated outputs are an exception.
- An ADC11 domain has width 2047 and therefore requires A≤16. Many coefficient tails meet this only after almost all products are computed.
- The symmetric absolute bound has width `2*M*A`, recovering the Q15 condition `M*A <= 16383`.

These are elementary deductions from the contract and bounds, not claimed new theorems. They explain the weak high-amplitude results and why a tighter bound must justify its own cost.

## Recommendation and next decision

Keep the exactness argument and the reproducible pilot. **Withdraw any implication that the current elementary method is already a secured original contribution or demonstrated energy optimization.** No MCU cycles or energy values have been measured, and no physical energy claim is supported.

Before selecting this as the final project, the next research step must supply a concrete, distinguishable method that avoids expensive bound maintenance or most failed checks, with a credible operating regime and a comparison against the static and folded baselines. If that method cannot be specified convincingly, select another FIR-specific question rather than expanding this parameter grid. A limits study remains possible, but its originality and relevance would need their own argument.

For the professor: present this as **completed preliminary validation of a candidate**, with the exactness result, the older bypass precedent and the small practical opportunity all visible. Do not present the candidate title as a finalized novel energy-saving algorithm.

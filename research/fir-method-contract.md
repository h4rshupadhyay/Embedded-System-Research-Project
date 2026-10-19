# Candidate FIR method and pilot contract

19 October 2026. This specifies an exploratory numerical feasibility study, not a finished embedded algorithm or an originality claim. It implements the validation plan approved in the conversation. Scope remains fixed-coefficient FIR only, simulator-only research, with publication optional.

## Fixed numerical reference

Inputs and coefficients are signed 16-bit integers. History is initialized to zero. For every incoming sample n, compute the exact integer sum `S[n] = Σ h[i] x[n-i]`, then emit `Q(S[n]) = clip_int16(floor(S[n]/32768))`. Every output is retained. No per-product rounding, per-MAC saturation, wrapping, coefficient changes or signal-dependent input quantization is allowed.

Use signed 64-bit products, pre-additions, sums and bound arithmetic in the numerical probe. Check that `32768 * Σ|h[i]| < 2^63-1`; this protects the full sum and its subsets for the admitted input domain. Certificate endpoint expressions must also fit: the implementation must allow for `|P| + max(|L|,|U|)`, not merely check the final full sum. For these filters the much larger safety margin is recorded through actual coefficient values. Widen before `abs(-32768)` and before paired input addition. Python/NumPy integer floor division defines negative quantization; a future C implementation must implement the same rule explicitly.

Arm's standard Q15 FIR has a compatible broad structure (64-bit accumulation, final truncation and saturation), while its fast Q15 function has different overflow considerations. A future executable library baseline requires a pinned source version and target-output checks. [Arm FIR documentation](https://arm-software.github.io/CMSIS-DSP/latest/group__FIR.html).

## Symmetry-aware baseline

The nine designed filters are exactly symmetric after integer coefficient rounding. For an equal-coefficient pair, compute `h[i] * (x[n-i] + x[n-(N-1-i)])` with a wide pre-addition. A center tap, if present, is a single sample. Omit zero coefficients from both methods. The full folded baseline therefore already uses approximately half the nonzero unfolded products. This is standard FIR engineering, not a new contribution.

Each group j has coefficient c[j], multiplicity m[j] equal to 1 or 2, and exact contribution t[j]. Natural order follows the first-half indices; magnitude order sorts by descending `abs(m[j]*c[j])`, with a stable tie order. The latter is an offline permutation, but a future implementation must pay for its indexing and access behavior.

The probe separately computes an unfolded convolution and verifies that the complete folded sum agrees before considering skipping.

## Dynamic bounds and static baselines

After k groups, let P be their exact sum. Precompute suffix sums for the remaining groups:

- `A[k] = Σ m[j]*abs(c[j])`.
- `Cplus[k] = Σ m[j]*max(c[j],0)`.
- `Cminus[k] = Σ m[j]*min(c[j],0)` (nonpositive).

**Absolute bound:** Maintain M, the maximum absolute sample over the actual N-sample input window. Then `L=-M*A[k]`, `U=M*A[k]`.

**Range bound:** Maintain a and b, the minimum and maximum sample over that same window. Then `L=a*Cplus[k]+b*Cminus[k]` and `U=b*Cplus[k]+a*Cminus[k]`. Paired samples are enclosed by `[2a,2b]`, so the multiplicity factors preserve validity. This can be tighter for a large DC offset with a small local variation, but requires more bound arithmetic and two maintained extrema. Use the cheaper exact form `T=(a+b)*(Cplus+Cminus)`, `D=(b-a)*A`, `L=(T-D)/2`, `U=(T+D)/2`. Both numerators are even because A and the signed coefficient sum have equal parity. This requires at most two logical multiplications per check. Do not reject the range method based on a needlessly expensive four-multiply expression.

Both use a shared whole-window envelope, even when remaining terms cover only part of the window. This conservatism is deliberate: no scan of all uncomputed samples or oracle residual is assumed free. Rolling extrema use monotonic deques. Their amortized behavior does not eliminate worst-case bursts or memory/control cost. The probe counts value comparisons, queue pushes/pops and absolute-value evaluations separately, including initial zero-history setup.

**Static baseline:** Use the same residual formulas with an externally declared input domain, so both endpoint arrays can be precomputed once for each coefficient order. The full int16 domain is `[-32768,32767]`. For native ECG streams, also evaluate the original ADC11 domain `[-1024,1023]`; for streams scaled by 16, its corresponding domain is `[-16384,16368]`. These domains come from the input representation, not from observed extrema or future values. Verify that every admitted sample meets its declared domain. A future implementation needs a trustworthy producer contract or must charge for domain validation. No rolling deque or per-check bound multiplication is needed, but endpoint loads and certificate arithmetic still cost work. This is a baseline and a familiar use of range information, not a novelty claim.

## Certificate and fallback

At a scheduled checkpoint, compute `Q(P+L)` and `Q(P+U)`. If equal, emit that output and stop processing groups for this output. Otherwise continue. If no certificate succeeds, compute all groups and emit Q of their sum. Always update the ordinary FIR input history and bound state for the next sample, even after an early exit.

Proof: every actual residual r lies in `[L,U]`; hence `P+L <= P+r <= P+U`. Monotonicity of the declared quantizer places `Q(P+r)` between the equal endpoint values. This establishes exactness under the numerical assumptions. It does not establish any energy benefit or novel theorem.

The fixed schedules are: every 1, 4 or 8 groups (including k=0 but excluding the unnecessary completed-sum certificate); and a single late check at `max(0,G-d)` for d=4,8,16 and G nonzero folded groups. A failed late check simply finishes the full FIR. A primary illustrative configuration is magnitude order, absolute bound, single late8 check; all alternatives are reported. No best-per-signal switching policy or training on these results is claimed. The initial pilot used the direct range expression and d=8,16; the cheaper range expression, static baselines and late4 schedule were added after inspecting that run. The refined run is exploratory, not a held-out confirmatory experiment.

## Costs and what the pilot can establish

Report executed FIR products and folded pre-additions, certificate checks and logical bound multiplications. The absolute bound uses one logical multiplication per check when the suffix is nonzero. The optimized range formula uses at most two; a zero signed suffix is elided. Static endpoints require no recurring bound multiplications. Compiler strength reduction and the target cost of wider multiplies are unresolved.

The metric `logical_multiplications_reduction_percent` compares `(executed folded FIR products + bound multiplications)` with the folded full-FIR product count. It excludes deque operations, endpoint arithmetic, quantization, branching, metadata, memory behavior and state handling; those are not all interchangeable with multiplication. It is a partial work diagnostic, **not net runtime or net energy**. A positive value merely leaves room to pay other costs. A negative value is an additional warning, not a universal impossibility proof across architectures.

The analysis computes full products/partial sums and actual residuals off-line to validate all certificates. That diagnostic work is not part of the hypothetical execution counts. Only an actual target implementation can validate whether those counts can be realized efficiently.

## Workloads and primary-source data provenance

Use Hamming-window lowpass (cutoff 0.10 relative to Nyquist), bandpass (0.20–0.35), and halfband (cutoff 0.50) FIRs. Lowpass/bandpass lengths are 64,128,256; halfband lengths 63,127,255. These are test designs, not validated application-specific clinical filters. [SciPy firwin documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.firwin.html).

Synthetic streams have 4,096 samples and fixed seed 20261019: uniform and two-tone amplitudes 8,128,8192; quiet/active/quiet; noisy DC; and constant, impulse and full-scale boundary diagnostics. No application-performance claim follows from synthetic labels.

Real input uses 4,096-sample segments at offsets 0,36000,72000 in SciPy's ECG excerpt, without cherry-picking by skipping result. The excerpt is from MIT-BIH record 208, MLII, sampled at 360 Hz. SciPy converts raw ADC values to mV by `(raw-1024)/200`. The probe instead preserves centered integer ADC values `raw-1024`, and separately evaluates that same stream multiplied by 16 without clipping. Each scaling is fixed for both algorithms; comparing their savings does not imply changing scale is a lossless optimization. [SciPy dataset documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.datasets.electrocardiogram.html), [SciPy dataset repository](https://github.com/scipy/dataset-ecg), [original record header](https://physionet.org/files/mitdb/1.0.0/208.hea).

Downloaded file SHA-256: `f20ad3365fb9b7f845d0e5c48b6fe67081377ee466c3a220b7f69f35c8958baf`. The script checks this checksum, records library versions, integer coefficient arrays and input hashes. One ECG record is not diverse application validation. No inference about diagnosis or clinical suitability is made.

## Validation and research boundary

Verify every proposed output against unfolded exact convolution. Validate maintained extrema against actual windows and verify each scheduled bound encloses the actual residual. Exhaust all length-four windows over {-2,-1,0,1,2} for two small coefficient sets and a smaller analogous saturating quantizer to exercise sign, boundary and saturation cases. These checks supplement the arithmetic argument; they are not a machine-checked proof for compiled code or simulator semantics.

The existing ingredients, including the residual certificate itself, are elementary. The accompanying [prior-art validation](fir-prior-art-validation.md) identifies older FIR lossless precision adaptation and whole floating-point MAC bypass. The numerical pilot can expose a potentially useful operating regime or reject a weak initial design; it cannot by itself establish an original algorithm. The next implementation decision depends on that evidence.

# FIR sharing probe: source provenance and usage

20 October 2026. Independent source check for the bounded speech_lp48, speech_minphase48 and vibration_bp192 probe. This note records generator provenance and correctness controls; it does not claim a new FIR algorithm.

## Hcub acquisition and attribution

The [official author software page](https://spiral.ece.cmu.edu/mcm/software.html) lists Hcub, BHM, RAG-n and optimal SCM implementations, but its January 2006 archive link returned HTTP 404. The newer [official SPIRAL generator page](https://spiral.ece.cmu.edu/mcm/gen.html) links the [14 January 2009 source archive](https://spiral.ece.cmu.edu/mcm/dl/synth-jan-14-2009.tar.gz); the web tool recognized gzip content but cannot inspect it. This exact URL was sent to the coordinator for download. The archive has now been downloaded and inspected; the unchanged source CLI was built and exercised. See the verified acquisition/build record below.

The generator page states GNU GPL availability and attribution to Yevgen Voronenko, SPIRAL project, Carnegie Mellon University, copyright 2006–2009. The inspected archive specifies GPL version 2 or later. Cite Voronenko and Püschel, [*Multiplierless Multiple Constant Multiplication*, ACM TALG 3(2), 2007](https://spiral.ece.cmu.edu/pubs/synth.pdf), for Hcub. Preserve the downloaded license and provenance if code is retained/distributed; the generated-code header separately specifies a BSD style output license (not a precise SPDX variant).

## Controls and graph pitfalls

Hcub shares shift/add/subtract intermediates across constants multiplying **one input**. It is a heuristic, not an optimal MCU-cycle generator. Per-constant CSD is a useful unshared control; it is not equivalent to Hcub. The paper's `45x` example also shows that CSD need not be optimal even for a single constant. Count shifts, negations, wide operations, coefficient loads and memory traffic on the target, not just adders. [Primary algorithm paper, §§1–2](https://spiral.ece.cmu.edu/pubs/synth.pdf).

The official web interface uses integer/fixed-point constants, produces pseudocode plus a DAG, and offers depth/randomization/NOFS options. Set fractional bits to zero for the existing quantized integer coefficients. Its web cap is 20 constants and 25 converted bits; that is not evidence of a source CLI limit. Avoid partitioning a larger filter merely to fit the form. NOFS minimizes intermediate-constant sum for hardware; it does not certify optimal register allocation or scalar execution. [Official interface](https://spiral.ece.cmu.edu/mcm/gen.html).

Derived correctness requirements for any imported graph:

- Preserve original coefficient order, signs, repeated coefficients, zeros, powers of two and final output shifts when mapping unique odd fundamentals back to FIR taps.
- Check every node algebraically as `c*x`; exact right shifts must divide the pre-shift integer expression. Do not replace them with lossy intermediate quantizers.
- Prove ranges of **shifted operands before addition**, not only the final odd fundamental. A subtraction can cancel large intermediates. Use safe unsigned operations with specified interpretation or proved-safe multiplication/widening; signed left shifts of negative values are unsuitable portable C.
- Save command, source checksum, options, seed and emitted graph. A nondeterministic tie choice must not become an unexplained experimental factor.
- Reconstruct product outputs independently with arbitrary-precision arithmetic. Algebraic node checks are stronger than a few random samples; sample tests still check the emitted target implementation.

These are deductions from exact graph semantics, not claims that Hcub itself supplies these checks.

## Exact direct/transposed FIR mapping

For integer products and states, define `p_i[n]=h_i*x[n]`. Direct FIR computes `s[n]=sum_i h_i*x[n-i]`. An equivalent transposed recurrence, with old state values `z_i` read before their replacement, is

```
s[n]      = p_0[n] + z_0(old)
z_i(new)  = p_(i+1)[n] + z_(i+1)(old)   for 0 <= i < N-2
z_(N-2)(new) = p_(N-1)[n]
```

All states initially equal zero. With this indexing, an ascending in-place state-update loop preserves the required old `z_(i+1)` values; a descending loop does not. `N=1` is a separate stateless case. Unrolling the recurrence proves equality with direct convolution; apply the project's quantizer only to `s[n]`. Every state needs its own exact suffix-sum range certificate. Arbitrarily narrowing states to Q15 changes the algorithm.

The [ASN first-party Cortex-M note](https://www.advsolned.com/implementing-fir-filters-with-the-asn-filter-designer-and-the-arm-cmsis-dsp-software-framework/) prints both direct and transposed difference equations; their integer-exact equivalence under unrounded states is our algebraic deduction. [FloPoCo's official `IntFIRTransposed` interface](https://flopoco.org/operators_5.0.git.html) confirms existing integer-coefficient shift-add transposed FIR generation with full output precision by default. Neither reference supplies our measured MCU result.

## Strong baseline needed for attribution

The existing [kernels.c](fir-baseline/kernels.c) loads coefficients through a runtime pointer. Beating that alone does not isolate coefficient sharing. Include a direct kernel whose coefficients/tap count are compile-time constants, allowing ordinary compiler strength reduction and constant folding; include exact symmetry folding only where valid and an otherwise identical transposed kernel using ordinary constant multiplications. Match state layout, accumulation widths, unrolling and quantizer when isolating graph effects.

Keep the strongest valid CMSIS standard/fast Q15 controls, including documented loop unrolling and full state maintenance. [Pinned Arm standard source](https://raw.githubusercontent.com/ARM-software/CMSIS-DSP/v1.14.4/Source/FilteringFunctions/arm_fir_q15.c) preserves Q30 products in a 64-bit accumulator, then drops 15 fractional bits and saturates; its license is Apache-2.0. The fast variant requires the project's no-overflow admission proof. Compare complete streaming execution on both compilers, including final short blocks, and report graph-only counts separately from measured machine events. Compiler-generated per-constant shift-add sequences can already remove multipliers; only the incremental gain from cross-constant sharing should be attributed to MCM.


## Verified local CLI and output (20 October 2026)

See [vendor/BUILD.md](fir-sharing-probe/vendor/BUILD.md) for the archive checksum, compatibility flags, unchanged-source check and licensing details. The source is retained under [vendor/synth-jan-14-2009](fir-sharing-probe/vendor/synth-jan-14-2009/README).

```bash
make acm CXXFLAGS='-O2 -std=gnu++98 -include cstdlib -include algorithm' CFLAGS=-O2
./acm 3 5 7 -b 15 -seed 1 -nofs -gc
```

Run from the extracted source directory. `acm` is the README-recommended generator; `synth` is intended mainly for cost analysis. These are not interchangeable for final signs/output shifts. Default algorithm is Hcub. `-nofs` is deterministic; no depth limit was requested. Original source files remain byte-identical; no algorithm edits occurred. Compiler flags compensate for missing standard includes and the old C++ dialect.

The resulting syntax includes `t4 = shl(t0, 2); /* 4*/` and `t1 = sub(t4, t0); /* 3*/`. Input is `t0`; header lines map output registers to requested coefficients. Operations are listed in execution order; zero shifts can print bare copies. Source `chains_util.cpp::op::output` also supports `add`, `shr`, `neg`, `cmul` and fused forms, so a parser must reject unhandled forms rather than silently skip them.

Raw examples for all three actual filters are saved under `vendor/`; [examples-manifest.json](fir-sharing-probe/vendor/examples-manifest.json) records unique positive odd targets, commands, hashes and algebraic verification. The target counts are 23 (speech_lp48), 45 (speech_minphase48), and 52 (vibration_bp192), with 45/90/103 assignment statements respectively. All returned successfully. Every assignment and declared output was independently checked as a coefficient times `t0`, requiring exact divisibility for right shifts. **speech_minphase48 contains `shr` operations**; the others include copies. This verifies graph algebra, not native-word range safety or generated target execution. Reattach signs and powers of two from the original coefficient array after importing the odd graph.

## Bounded assessment after the measured probe

20 October 2026. Read the saved protocol/results without rerunning target binaries. Independently regrouping `results.json` confirms 256 primary rows, 24 groups and 10 modeled-energy wins for `trans_hcub_demand`, two for `trans_const`, and 12 for nontransposed candidates. Repeated compiler/block/domain groups are not 24 independent application filters. Correctness totals and edge checks remain the runner's reported evidence.

**The useful empirical question is now concrete:** when does an established exact transposed sharing graph outperform strong direct/symmetry/library software once persistent suffix-state widths and the graph's live values are charged? The minimum-phase case sharpens it: an output needing wide exact accumulation does not imply every persistent state needs that width. Its same-layout ordinary-constant control also wins substantially against the library, so crediting the full library-relative gain to Hcub would be wrong. In GCC15/full-int16/block64, saved modeled energies are 562.55 nJ/output (demand Hcub), 602.87 (ordinary constants and CSD), 655.89 (eager Hcub), and 838.85 (CMSIS64 unrolled). These matched controls separate structural/width effects from incremental sharing and emission-order effects; they do not establish an optimal schedule.

The closest inspected software studies do **not make the broad question new**. [Gačić et al. 2003](https://spiral.ece.cmu.edu/pub-spiral/pubfile/fir.pdf) already generate architecture-adapted FIR software with blocking. [D’Alberto et al. 2007](https://users.ece.cmu.edu/~franzf/papers/hipeac07.pdf), §§2.2–4, explicitly generate fixed-point FIR software, use GCC 3.4.2 on XScale, compare 8/16-tap filters with IPP, and optimize measured runtime/physical energy. Their described FIR alternatives include blocking, Karatsuba and frequency-domain methods. The inspected account does not supply the present guaranteed-range, suffix-state-width and fixed-Hcub-graph emission comparisons. That bounded difference supports distinct empirical scope, not a claim that no other literature studied it.

A particularly useful practical comparison is the [ASN 2020 Cortex-M note](https://www.advsolned.com/implementing-fir-filters-with-the-asn-filter-designer-and-the-arm-cmsis-dsp-software-framework/): it favors direct form for fixed point because one large accumulator accommodates overflow. Our exact heterogeneous-state examples can **qualify that implementation guidance**: wide final accumulation need not force uniformly wide transposed state. This does not refute a mathematical claim or show ASN's own generator could not be extended. Hcub, exact width reduction and demand-driven graph emission remain established mechanisms.

**Contribution positioning:** a reproducible case study of the boundary between coefficient sharing and exact persistent-state cost on the specified small-core/compiler model, with positive and negative cases and causal controls. This is more substantive than simply adding another selector row because it isolates a previously untested representation tradeoff in this project. It can support the college paper as original empirical work; a substantial field-level algorithm claim remains unsupported.

What remains for the *bounded* argument is the targeted uniform64-state ablation already being conducted, plus attribution of the large same-graph schedule gap through relevant disassembly/stack and memory events. Report code/state/stack costs alongside speed, and retain the long-filter full-range losses prominently. If a general transferable rule is claimed later, these three inspected filters cannot validate it; that would require an independently specified rule and fresh justified designs. No additional broad benchmark expansion is necessary merely to publish this case study honestly. Finishing these explanations does not require inventing an optimizer or claiming novelty from the improved percentages.

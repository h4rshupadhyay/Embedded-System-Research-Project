# Completed partial-direct comparison and decision

20 October 2026. Final join of the [fixed plan](../../../docs/superpowers/plans/2026-10-20-fir-baseline-check.md).
One frozen 48-tap filter, full-int16 guarantee, groups `[0,2)` and `[2,48)`,
GCC 10.3.1/GCC 15.2.Rel1, blocks 1/64, `-O2`, no LTO, 257 saved samples.
No filter, partition search, optimizer or additional performance workload was added.

## Result and research decision

**The arithmetic-fairness correction changes the winner. Partial direct wins
both GCC 10 configurations; demand Hcub wins both GCC 15 configurations.**
Ordinary mixed-width transposition beats partial direct only with GCC 15,
block 1. A universal transposed advantage is unsupported. Continue as a bounded
empirical study of baseline fairness, arithmetic width and compiler-dependent
representation costs. A new FIR algorithm or substantial field novelty remains
unestablished; the professor remains the final evaluator.

| Compiler | Block | Partial direct nJ/output | Ordinary transposed cost relative to partial direct | Demand Hcub cost relative to partial direct | Lowest modeled-energy variant in the compared set |
|---|---:|---:|---:|---:|---|
| GCC 10 | 1 | 1036.55 | +0.89% | +4.33% | Partial direct |
| GCC 10 | 64 | 575.81 | +5.18% | +5.00% | Partial direct |
| GCC 15 | 1 | 1310.75 | −20.66% | −24.06% | Demand Hcub |
| GCC 15 | 64 | 593.59 | +1.56% | −5.23% | Demand Hcub |

Relative cost is `100 * (E_variant / E_partial_direct - 1)`; negative means
the transposed variant costs less. These are modeled CPU-energy estimates,
not board measurements. Estimated-cycle winners agree with these four energy
winners. See the generated [comparison](comparison.md) and
[verification report](verification.json) for all controls and resource metrics.

The old 32.94% Hcub benefit versus unrolled CMSIS at GCC 15/block64 remains a
correct library-relative measurement, but the benefit versus this stronger
direct control is 5.23%. The original 12/24 bank result describes the original
candidate set and must not be presented as a result with equally narrowed direct
controls throughout the bank. No revised bank-wide experiment was run.

## Evidence admission and arithmetic review

The delivered runner found the existing simulator and both compilers with
identical recorded binary hashes and version strings. It generated four timed
binaries and two separate 361-sample signed-edge binaries. Its saved-evidence
verification passed 1,750 output comparisons, retained history and guards.
The independent checker then admitted all four performance rows, rechecked
1,028 new output comparisons and reverified the 24 historical rows/6,168 outputs.
A separate invocation of its arbitrary-precision reference and transcript
decoder also matched all 722 edge outputs, retained histories and guards.

The final expanded peer host suite passed all three tests with UBSan and
nonrecovering undefined-behavior checks on this Linux host. The log is
[join-host-tests.txt](join-host-tests.txt). It includes positive and negative
full-scale sums outside int32, signed extremes, exact sums around negative
quantization boundaries, saturation, mixed partitions and a short final call.

Manual inspection of `partial-direct/kernel.c` confirms the literal frozen
coefficients and the two fixed groups. Their coefficient L1 sums are 12,778
and 59,731; multiplying by 32,768 gives prefix/product bounds 418,709,504 and
1,957,265,408. Each fits int32. The full bound 2,375,974,912 does not.
Both completed partials are converted to int64 before addition. The combined
sum fits int64 and is quantized once. Clamping precedes the narrowing conversion;
negative division implements floor without relying on signed right shift in C.
The original chronological input-history organization and forward history copy
are retained, including block64's final one-sample call.

Ruling: accept the delivered `compiler_flags.compile` field as an explicit
alternative to the checker's `flags` field, with the same optimization, CPU,
Thumb and no-LTO admission rules. This resolves a schema difference without
changing peer code/results or inventing metadata. A regression test first
reproduced the rejection, then passed after the adapter; it also rejects added
LTO, `-O3` and Cortex-M3 flags. All 27 checker tests pass. If this mapping were
wrong, incompatible compilation could be ranked as comparable; the saved
`commands.json` files were additionally inspected to resolve that risk here.

## Emitted-code review

All four `probe_process.disasm` files contain native 32-bit partial arithmetic,
two sign extensions (`asrs ..., #31`) and one low-word `adds`/high-word `adcs`
reduction before the final saturation/quantization branches. There are no
calls from these `probe_process` bodies to arithmetic helpers. The compiler
uses both shifts/adds and native multiplies for constant products; source
operation counts alone do not describe their cost.

| Build | First partial sign extension | Second partial sign extension | Wide reduction (`adds`, `adcs`) | Compiler-reported frame bytes |
|---|---|---|---|---:|
| gcc10-b1 | `0x0800037a` | `0x08000390` | `0x0800039e`, `0x080003a0` | 72 |
| gcc10-b64 | `0x0800041e` | `0x08000434` | `0x08000442`, `0x08000444` | 72 |
| gcc15-b1 | `0x0800047e` | `0x08000492` | `0x0800049e`, `0x080004a0` | 240 |
| gcc15-b64 | `0x0800043c` | `0x08000450` | `0x0800045c`, `0x0800045e` | 232 |

The saved commands compile each kernel/fixture/startup separately for Cortex-M0
Thumb with `-O2`, no LTO and the appropriate `BLOCK`; the linker and marker
assembly match the existing fixture. Setup and printing stay outside the region.
The runner's `assembly_review_status` records its automatic generation stage;
this note supplies the subsequent manual review rather than editing that record.

Narrowing direct arithmetic materially reduces its frame and recurring traffic
relative to the old wide-direct implementation. For GCC 10/block64, direct RAM
writes fall from 25,497 to 1,848; its modeled energy/output falls from 990.40
to 575.81. Demand Hcub has fewer instructions (116,139 versus 129,481) and
multiplies (257 versus 2,827) but more RAM reads (24,689 versus 13,695) and
writes (20,083 versus 1,848), and costs 5.00% more modeled energy.

Compiler sensitivity remains after the correction. The identical partial-direct
source at block1 has 242,490 instructions/43,182 reads/36,500 writes with GCC 15,
versus 198,670/29,304/17,225 with GCC 10. The emitted bodies contain substantial
stack traffic, and frame reports rise from 72 to 240 bytes. This supports a
generated-code resource explanation; it does not identify every spill's cause,
prove an optimal schedule, or establish a compiler defect.

At block64, partial direct allocates 224 bytes of state versus 192 for the
transposed forms; at block1 it allocates 98 versus 192. Direct frames are lower
in all four cases; selected-symbol code size is lower than ordinary transposition
in all four. Hcub's code can be smaller or larger depending on configuration.
Frames are static diagnostics, not peak-stack measurements, and selected-symbol
sizes exclude fixture code and possible other helpers.

## Reproduction and limits

```bash
FIR_UBSAN=1 python3 -m unittest discover -s research/fir-sharing-probe/partial-direct -p 'test_*.py' -v
python3 -m unittest discover -s research/fir-sharing-probe/independent-check -p 'test_*.py' -v
python3 research/fir-sharing-probe/partial-direct/run.py --verify
python3 research/fir-sharing-probe/independent-check/check.py --peer-results research/fir-sharing-probe/partial-direct/results.json
```

The new six-case raw build tree is preserved in
`partial-direct-target-evidence.tar.gz` alongside this note. Restore it with
`tar -xzf research/fir-sharing-probe/independent-check/partial-direct-target-evidence.tar.gz -C research/fir-sharing-probe/partial-direct`.
Historical verification still requires the original ignored historical build
artifacts. The archive contains sources, commands, binary/ELF, disassembly,
raw stdout/events, stack reports, maps and size reports; each is covered by
the peer result's artifact manifest. The archive checksum is in
`partial-direct-target-evidence.sha256`.

Final verification also passed all ten baseline tests. Regenerating the three
independent reports into a temporary directory reproduced the saved files
byte-for-byte. Extracting the archive into a temporary directory verified all
102 artifact hashes across the six new cases; the archive's own checksum passed.

A fresh read-only reviewer independently confirmed row admission, all 722 edge
outputs/history/guards, bounds, flags, assembly addresses, resource figures and
archive integrity, with no important or critical findings. Its only formatting
observation was the pre-existing four-space indentation of the original audit's
first heading; that user edit was preserved.

This completes the fixed fairness gate, not an exhaustive implementation search
or fresh held-out validation. The finite stream begins with zero history and
does not establish steady-state application behavior. Timing assumes zero wait
states and single-cycle MUL; energy uses the existing 20 MHz/prefetch-off model.
No physical accuracy/error-bound claim follows. The established-method overlap
in [positioning.md](positioning.md) still applies. A useful college empirical
project is feasible; publication-level novelty is not demonstrated by this gate.

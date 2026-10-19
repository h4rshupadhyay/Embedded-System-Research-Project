# Saved BLOCK=1 assembly and source-value flow

20 October 2026. Scope: `partial_direct32x2`, `speech_minphase48`, GCC10/GCC15,
`-O2`, Cortex-M0 Thumb, no LTO, the same 257 saved samples and zero initial
history. This note analyzes the existing binaries; it does not describe a new
optimization experiment or a physical measurement.

The clearest difference is GCC15's storage of a sliding window of history
samples across output-loop iterations. Its prelude loads 36 samples before the
arithmetic loop, and its loop tail updates many saved samples before testing
whether another output is needed. With `b=1`, these updates still execute, but
there is no next output in that call. GCC10 loads almost every sample where it
is used and carries only one sample into the next output iteration. Both retain
32-bit partial arithmetic and perform the same final 64-bit reduction.

Exact control flow for this fixture establishes that the additional direct
SP-relative loads and stores account for the entire RAM-read/write delta.
That accounting does **not** identify the compiler pass responsible, prove that
every stack temporary is a register-allocation spill, or prove that the larger
frame itself causes the instruction difference.

## Evidence and notation

Paths below are relative to `research/fir-sharing-probe/partial-direct/`.
`G10` and `G15` mean `build/target/gcc10-b1/` and `build/target/gcc15-b1/`.
Each address names the compiler's `probe_process` unless another function is
specified. Address ranges are inclusive unless written `[start,end)`.
`h_i` denotes the signed 16-bit value `s->history[j+i]` during the convolution
loop; initial preload descriptions use `j=0`. Stack offsets use the stable SP
after the local allocation. `ip`, `sl`, and `fp` are r12, r10, and r11.

The source contract is `kernel.c:29` (copy-in), `:30–80` (two partials),
`:81` (widen before addition), `:18–24` (floor/saturating quantizer), and
`:84–85` (forward history copy). `kernel.h` makes the block-one state 98 bytes;
`BLOCK` sizes the state but does not replace the function's runtime `b`
parameter with a compile-time constant. The saved commands compile `kernel.c`
and `firmware.c` separately and contain no LTO option.

Verified SHA256 identities:

| Input | SHA256 |
|---|---|
| `results.json` | `eb53d3e556a6f8444742856b8c45a7d3236f443fed6cc0312010b2840095dc4f` |
| `kernel.c` | `5832b52eaf1d5eb76e8087d47307feeccf74809cc0f22b288d111505851501cd` |
| `G10/firmware.bin` | `07fd7023d12ead52fee14a266c647627d664f37c18c234a0b41e2f226f143a6a` |
| `G15/firmware.bin` | `114041b0f03a20c34a9c8a37b147116dff9f74c3c321bd2af4d7709d710e3470` |

All 17 archived artifact hashes per case were checked against the frozen
`results.json`, including the source copies, commands, full and extracted
disassemblies, maps, stack reports, raw stdout/stderr, ELF and binary. The saved
compiler versions are GCC 10.3.1 20210621 and Arm GNU Toolchain 15.2.Rel1,
GCC 15.2.1 20251203. These identify the saved builds; the compilers were not
invoked during this analysis.

The maps place `probe_process` at `0x08000024`, with section sizes `0x40c`
(1036 bytes) and `0x55c` (1372 bytes). Those sizes include literal pools and
padding. G10 has coefficient/limit literals at `0x08000418–0x0800042c`;
G15 has coefficients at `0x080004b4–0x080004c0` and limits at
`0x08000578–0x0800057c`. They are data, not executed arithmetic instructions.

## The two partials and the final reduction

Both bodies compute
`partial0 = 3526*h_47 + 9252*h_46` and
`partial1 = sum(coefficients[2:48] * h_45..h_0)` in native 32-bit registers.
Their absolute bounds are 418,709,504 and 1,957,265,408, respectively, so each
completed partial fits signed int32 for the full int16 input guarantee. The
sum need not fit int32; the emitted sign extensions and carry addition preserve
the wider result. Neither body contains a call to an arithmetic helper.

| Source value | GCC10 flow | GCC15 flow |
|---|---|---|
| `partial1` seed | `r7=s+66+2*j`; `0x08000074–0x0800007a` loads `h_45`, multiplies by literal 12990 into r2 | `[sp,#40]` initially receives `h_45` at `0x08000052/56`; `0x0800016a–0x08000172` multiplies it by 12990 and combines with the previously formed `10395*h_44` |
| `partial1` running value | Moves among r2/r0/r3 through `0x0800008c–0x0800035a`; `0x0800035a` has all terms except `-39*h_0` | Moves among r6/r8/ip/r2/r3 through `0x08000172–0x08000466`; `0x08000466` has all terms except `-39*h_0` |
| `partial0` | `0x0800035c–0x08000376`: `h_47*3526` plus `h_46*9252`; completed r3 stored to `[sp,#8]` at `0x08000378`; ASRS #31 at `0x0800037a`, high word stored to `[sp,#12]` | `0x08000464–0x08000478`: `[sp,#52]` supplies `h_46`, `[sp,#36]` supplies `h_47`; completed r3 stored to `[sp,#56]` at `0x0800047c`; ASRS #31 at `0x0800047e`, high word stored to `[sp,#60]` |
| Completed `partial1` | `sl=h_0`; `0x0800037e–0x0800038e` forms `-39*h_0` modulo 2^32 and adds it into r0; ASRS #31 at `0x08000390`; low/high stored to `[sp,#0]/[sp,#4]` | `[sp,#128]=h_0` loaded at `0x0800047a`; `0x08000482–0x0800048e` completes r3; low/high stored to `[sp,#64]/[sp,#68]`, ASRS #31 at `0x08000492` |
| `exact_sum` low/high | Reload p0 to r2/r3 and p1 to r4/r5 at `0x08000396–0x0800039c`; ADDS/ADCS at `0x0800039e/0x080003a0` | Reload p1 to r4/r5 and p0 to r2/r3 at `0x08000496–0x0800049c`; ADDS/ADCS at `0x0800049e/0x080004a0` |

The final `ADDS` establishes the low-word carry; the immediately following
`ADCS` adds the two sign words plus that carry. The accumulator high word is
then tested for saturation. These are two sign extensions of completed partials,
not a chain of 48 wide multiply/accumulates.

Annotated excerpt 1 — GCC10, the complete partial-to-wide interface. The omitted
instructions at `0x0800037e–0x0800038c` form `-39*h_0` in r3; r0 already holds
the other 45 terms of partial1.

```asm
08000376  adds r3, r2, r3       ; partial0 = 3526*h_47 + 9252*h_46
08000378  str  r3, [sp, #8]     ; p0 low
0800037a  asrs r3, r3, #31      ; p0 signed high word
0800037c  str  r3, [sp, #12]
          ...                  ; r3 = -39*h_0, r0 retains p1 prefix
0800038e  adds r0, r3, r0       ; completed partial1
08000390  asrs r3, r0, #31      ; p1 signed high word
08000392  str  r3, [sp, #4]
08000394  str  r0, [sp, #0]     ; p1 low
08000396  ldr  r2, [sp, #8]
08000398  ldr  r3, [sp, #12]
0800039a  ldr  r4, [sp, #0]
0800039c  ldr  r5, [sp, #4]
0800039e  adds r2, r2, r4       ; exact_sum low, sets carry
080003a0  adcs r3, r5           ; exact_sum high, consumes carry
080003a2  cmp  r3, #0           ; start quantizer
```

The four low/high temporary stores and four reloads also exist in GCC15.
Thus the presence of stack materialization at the widening interface is shared
by the two builds, and cannot alone explain their traffic difference. The
source has no explicit stack objects for these pairs; the disassembly proves
their contents and lifetimes but does not distinguish compiler expansion,
allocation, or later rewriting as the reason for the materialization.

## History lifetimes and representative stack-resident values

GCC10 initializes `r8=h_0` at `0x08000058–0x0800005e`. At `0x0800015c` it
copies that value to sl for the final `-39*h_0` term. At `0x08000352/58`, the
load of `h_1` is also placed in r8, so a subsequent iteration can use it as its
new `h_0`. Most other samples are loaded near their arithmetic use. The bases
are `r7=s+66+2*j` and `r1=s+2+2*j` (`0x0800006e/70`); the loop advances them
at `0x080003ba/0x080003bc`.

GCC15 preloads 36 signed samples at `0x0800004c–0x0800011c`: indices
`{0,1,2,4,5,6,...,44,45,46}`. These are three samples from every four-sample
group. They occupy registers and stack slots. The loop fetches the 12 remaining
samples `{3,7,...,43,47}` while doing arithmetic. At j=0, this is still 48
sample loads in total, exactly as in GCC10. The stack/register values are
rotated for a possible next j; they persist for much longer than a product's
immediate evaluation. This pattern establishes loop-carried sample reuse in
the emitted code without naming a particular GCC optimization pass.

Representative lifetimes:

| GCC15 slot/value | Definition and arithmetic use | Recurrence or reuse |
|---|---|---|
| `[sp,#40] = h_45` | `0x08000050/52/56` loads history[45] and stores it; `0x0800016c/6e` consumes it in `12990*h_45` | `0x080004d4/4d8` moves the old value to ip, which will be the next iteration's `h_44`; `0x080004da/4de` copies old `[sp,#52]=h_46` into this slot for next `h_45` |
| `[sp,#36]`, `[sp,#52]` | `0x08000058–0x0800005c` initially stores history[46] to #36; `0x0800014e/150` copies it to #52 for the 9252 product at `0x08000464–0x08000474` | `0x08000156/166` loads fresh `h_47` and replaces #36; `0x0800046e/476` consumes it in the 3526 product; the next loop head would copy it to #52 |
| `[sp,#80] = h_42` at iteration start | Set at `0x0800006a–0x0800006e`; read at `0x08000170`, preserved in sl at `0x08000174`, then used in the `-4294*h_42` chain at `0x0800017a–0x080001a4` | Fresh `h_43` from `0x08000178` replaces #80 at `0x08000180`, preparing next iteration's `h_42`; old sl is copied to `[sp,#4]` at `0x080004e6/4e8`, preparing next `h_41` |
| `[sp,#128] = h_0` | Initialized at `0x0800010e–0x08000112`; survives until the `-39*h_0` product, load at `0x0800047a` | `[sp,#32]=h_1` is copied into #128 at `0x08000522/524`, before exit is tested |
| `[sp,#152] = output pointer` | Initial r4 saved at `0x0800013a`; loaded at `0x080004c6` for output store at `0x080004ca` | Incremented at `0x080004ce`, saved at `0x080004f0`; compared with `[sp,#184]` at `0x0800052a/52c` |

Offsets do not have permanent source identities: G15 `[sp,#48]` initially
contains history[44] (`0x08000054`), is loaded into ip via `0x08000138/146`,
then is overwritten with history[17] at `0x0800014a`. That later value is read
for `-431*h_17` at `0x08000358–0x08000372`. Calling every access to offset 48
one variable or one spill would be incorrect.

Annotated excerpt 2 — GCC15, selected sample rotations in the loop tail.
The omitted spans contain other rotations/pointer updates and no branch.
All quantizer exits converge at `0x080004c6`, so the tail executes for every
output, including the last output of the call.

```asm
080004c6  ldr  r3, [sp, #152]   ; y+j
080004c8  ldr  r4, [sp, #172]   ; saved sample used by another rotation
080004ca  strh r2, [r3, #0]     ; output
          ...
080004d4  ldr  r2, [sp, #40]    ; old h_45
080004d6  str  r0, [sp, #84]    ; old h_37 becomes next h_36
080004d8  mov  ip, r2           ; next h_44 = old h_45
080004da  ldr  r2, [sp, #52]    ; old h_46
080004dc  str  r7, [sp, #72]    ; old h_13 becomes next h_12
080004de  str  r2, [sp, #40]    ; next h_45 = old h_46
          ...
08000522  ldr  r4, [sp, #32]    ; old h_1
08000524  str  r4, [sp, #128]   ; next h_0 = old h_1
08000526  ldr  r4, [sp, #176]   ; old h_2
08000528  str  r4, [sp, #32]    ; next h_1 = old h_2
0800052a  ldr  r4, [sp, #184]   ; output end pointer
0800052c  cmp  r4, r3
0800052e  beq  0x08000532       ; b=1: leave after all these rotations
08000530  b    0x0800014e       ; only if another output remains
```

This is stack-resident sample/control state, not merely a larger accumulator.
No claim is made that all stores in the tail are provably eliminable by a
particular compiler pass. Their execution on the final iteration and their
source-value roles are directly visible.

## ABI saves and frame allocation

Both functions use the same entry sequence at `0x08000024–0x0800002e`:
push r4–r7/lr (20 bytes), move r8/r9/sl/fp through low registers/lr, then push
those four values (16 bytes). These are identifiable preserved-register saves,
not arithmetic spills. The local allocation is 36 bytes at G10
`0x08000030`, versus 204 bytes at G15 `0x08000032`. Hence 36+36=72 and
36+204=240, exactly the respective `kernel.su` reports.

G10 `0x080003e2–0x080003ee` and G15 `0x0800054a–0x08000556` deallocate
locals, restore high registers from the first pop, then restore r4–r7 and return
through pc. Each call has nine saved and nine restored words in both binaries.
The greater SP subtraction allocates address space; it does not itself write
204 bytes. The extra executed stores are separately visible in the body.

G10 also stores r4/r5 into local `[sp,#0]/[sp,#4]` at
`0x0800006a/6c`, although these local words are overwritten with partial1 at
`0x08000392/394` before their later loads. At these stores r4 still contains
the caller's r4, while r5 contains the caller's r8 copied at `0x0800002c`.
The entry pushes already preserve both values. These two local stores have no demonstrated arithmetic use
on the positive-b path; they must still be counted as executed stores. The
assembly alone does not explain why the compiler retained them.

## Constant lowering, quantization, and non-arithmetic work

Both compilers use four flash coefficient literals: 12990, 2471, 1994, 3526.
Examples: G10 `0x08000078/7a`, G15 `0x0800016a/6e` load/multiply 12990;
G10 `0x08000360/362`, G15 `0x08000472/476` load/multiply 3526. Seven further
products use immediate constants and native MUL: 200, 242, 53, 209, 212, 170,
and 76. Both bodies have eleven MULs on the single output path, consistent with
the raw dynamic total 2827 = 11*257. Native multiplication count does not
explain the difference.

Shift/add/sub chains implement other coefficients. For 9252, G10
`0x08000368–0x08000374` and G15 `0x08000468–0x08000474` implement
`4*(1+256)*(1+8)*h_46`. For 10395, G10 `0x08000080–0x0800008a` and G15
`0x08000158–0x08000168` implement `63*33*5*h_44`. The latter shows additional
high/low register moves in G15 despite the same coefficient arithmetic.

Several negative coefficients use wrapping 32-bit shifts. For example the
G10 `0x08000382–0x0800038c` and G15 `0x08000482–0x0800048c` sequence for
`-39*h_0` has coefficient
`(((2^27-1)*4-1)*8+1) = 2^32-39`, equivalent to -39 modulo 2^32.
Intermediates of these *machine* chains need not fit signed int32. This does
not imply signed-overflow undefined behavior in the C source: the source
product and partial-prefix bounds fit, and the emitted machine instructions
provide the correct final 32-bit bit pattern.

The quantizers have matching high/low comparisons for ±2^30. G10 starts at
`0x080003a2`, with upper-bound code `0x080003f0–0x080003fa` and lower-bound
code `0x0800040a–0x08000414`. G15 starts at `0x080004a2`, with counterparts
`0x08000558–0x08000562` and `0x0800056c–0x08000576`. For an in-range sum,
G10 ASRS #15 at `0x080003b0` is followed by SXTH; G15 ASRS #15 at
`0x080004c4` feeds the halfword store without that SXTH. Both implement the
floor quantizer. G15's `0x080004b0` branches over the coefficient pool to
`0x080004c4`; the negative in-range path arrives directly via
`0x08000572`. Therefore this extra branch is path-dependent, not once per
static site or once per call regardless of sign.

The saved input's exact sums range from -29,858,685 to 32,325,916. There are
131 nonnegative and 126 negative sums, and no saturated sum. Thus this fixture
exercises the ordinary quantizer paths, not the full saturation behavior.
Those signs come from the arbitrary-precision source reference and the saved
input; output words alone would not distinguish all boundary conditions.

| Work | GCC10 addresses | GCC15 addresses | Observation |
|---|---|---|---|
| Copy-in | `0x0800003a–0x08000056` | `0x0800003a–0x0800004a` | One source halfword copied to history[47] for b=1; G10 reloads destination base from `[sp,#20]` inside this loop |
| Output store and loop tail | `0x080003b4–0x080003c2` | `0x080004c6–0x08000530` | G15 has extensive sample rotations; G10 advances pointers and compares |
| History-copy setup/body | `0x080003c4–0x080003e0` | `0x08000532–0x08000548` | Both advance a source pointer by 2 and store 47 halfwords forward; no new convolution occurs here |
| Stream wrapper | `process_stream:0x08000480–0x080004a2` | `process_stream:0x080005d0–0x080005f0` | Both pass r3=1 on every call and advance input/output pointers by 2 through 514 bytes |

The wrapper differs by one setup instruction: G10 loads storage base and adds
8 at `0x0800048c`; G15 loads the state address directly. Both push/pop six
words and read four flash literals once. There are 257 calls to probe_process,
plus one measured call to process_stream, matching 258 BLs. The final call is
also one sample; there is no partial block with a different b in this fixture.

## Static sites versus exact dynamic traffic

The raw logs are aggregate event logs, not per-PC traces. Static site counts
alone cannot assign dynamic traffic. Here the following additional facts make
the direct-SP traffic count exact for this particular fixture:

1. `process_stream` sets r3 to 1 at G10 `0x08000492` / G15 `0x080005e0`,
   and loops exactly 257 times over a 514-byte input span.
2. The b=0 paths at G10 `0x080003fc–0x08000408` and G15
   `0x08000564–0x0800056a` are never reached. In particular, the G10
   stack store at `0x08000406` is a static site with zero executions.
3. Copy-in executes once. The arithmetic/output loop executes once because
   its pointer advances by two to the stored end pointer. The prelude and
   unconditional tail each execute once. The loop backedges at G10
   `0x080003c2` and G15 `0x08000530` are not taken/executed on this path.
4. No quantizer side path contains an SP-relative load/store. All paths join
   before the common output tail. History copy runs 47 iterations but contains
   no SP-relative accesses in either compiler; its setup accesses run once.
5. Both functions keep SP fixed between allocation and deallocation; there
   are no calls or indirect branches inside the arithmetic body.

Therefore every remaining direct-SP site runs exactly once per call. This is
an exact-control-flow deduction from the saved wrapper and bodies, not a
dynamic trace or an assumption that every static site is executed 257 times.

| Diagnostic / proved frequency | GCC10 | GCC15 | Difference |
|---|---:|---:|---:|
| Static direct-SP instruction sites | 19 | 147 | 128 |
| Direct-SP LDRs actually executed per b=1 call | 9 | 63 | 54 |
| Direct-SP STRs actually executed per b=1 call | 9 | 84 | 75 |
| Direct-SP reads across 257 calls | 2313 | 16191 | 13878 |
| Direct-SP writes across 257 calls | 2313 | 21588 | 19275 |

For example, the G15 prelude `[0x0800004c,0x0800014e)` contains 129
instructions, with one direct-SP load and 39 direct-SP stores. The tail after
the output store and before the loop compare, `[0x080004cc,0x0800052c)`,
contains 48 instructions, with 18 direct-SP loads and 22 direct-SP stores.
These are bounded regions with once-per-call frequency in this fixture.
They mix sample handling and control values; the counts should not be renamed
"spills" or treated as a complete count of any single source-level operation.

The complete RAM traffic independently reconciles as follows. Per call, both
compilers read 48 signed history samples for convolution, read one input
halfword, read 47 halfwords for history copy, and pop nine saved words. Both
write one copied input, one output, 47 history halfwords, and push nine words.
The wrapper contributes six reads and six writes once for its push/pop. Under
the saved simulator's observed per-transfer RAM event accounting:

```text
G10 reads  = 257*(48 + 1 + 47 + 9 +  9) + 6 = 29304
G15 reads  = 257*(48 + 1 + 47 + 9 + 63) + 6 = 43182
G10 writes = 257*( 1 + 1 + 47 + 9 +  9) + 6 = 17225
G15 writes = 257*( 1 + 1 + 47 + 9 + 84) + 6 = 36500
```

The final term inside each parenthesis is the direct-SP load/store count.
This demonstrates the memory-event contribution of emitted stack accesses.
It does not assign every instruction delta to stack accesses: arithmetic
register moves, address setup, literal-pool branches, and quantizer code also
differ. The analyzer's component totals must use its declared PC boundaries;
the illustrative regions above are not an alternative component partition.

The independently read raw totals, after the existing runner removes the one
closing-marker instruction, are:

| Counter | GCC10 | GCC15 | G15 minus G10 |
|---|---:|---:|---:|
| Instructions | 198670 | 242490 | 43820 |
| MUL | 2827 | 2827 | 0 |
| RAM reads | 29304 | 43182 | 13878 |
| RAM writes | 17225 | 36500 | 19275 |
| Flash data reads | 1032 | 1032 | 0 |
| Flash writes | 0 | 0 | 0 |
| Taken branches | 13622 | 13753 | 131 |
| BL | 258 | 258 | 0 |

The measurement boundary is visible in `measured`: G10 marker stores are
`0x08000666/0x0800066c`, with measured BL at `0x08000668`; G15 marker stores
are `0x080007aa/0x080007b0`, with BL at `0x080007ac`. Raw stderr reports
198671/242491 instructions; `run.py:raw_events` subtracts the closing-marker
instruction and its fetch. The marker setup/push precedes measurement, and its
return/pop follows it. Initialization and O:/H:/G:/M: printing in `main` are
outside this region. The addresses printed in marker messages are simulator
PC state, not a substitute for the actual marker-store instruction addresses.

## Supported interpretation, competing hypotheses, and limits

- **Supported:** both kernels implement the same two narrow partials and wide
  final reduction. GCC15's additional direct-SP transfers fully account for the
  RAM-event difference for the saved block-one execution. Representative added
  storage carries history samples and output-loop control across iterations.
- **Supported:** GCC15 pays initialization and rotation costs for a window of
  samples even though each call processes only one output. The lack of LTO and
  the runtime b argument explain why the emitted function retains a general
  loop; they do not prove which optimization chose its sample-reuse scheme.
- **Plausible, unproven compiler cause:** moving sample loads out of the loop
  and preserving their values increases simultaneous lifetimes, contributing
  to stack storage and extra high/low register moves on this target. Proving a
  particular pass, heuristic, or register-allocation decision needs compiler
  intermediate dumps or controlled compiler analysis not present here.
- **Competing cause:** scheduling and target instruction constraints also
  affect register moves and stack materialization. The source-value evidence
  does not establish whether allocation pressure, an earlier lowering decision,
  or their interaction produced each individual temporary.
- **Rejected as an explanation of the difference:** additional native MULs,
  extra ABI saved registers, or a restoration of wide per-tap arithmetic. The
  saved bodies/counters show eleven MULs, the same nine saved words, and only
  the final wide reduction in both builds.
- **Unresolved:** the reason for G10's two overwritten local stores, the exact
  pass origins of all G15 sample slots, and whether another schedule would be
  preferable under other workloads. No defect, optimality, general GCC version
  ranking, or new FIR algorithm follows from this evidence.

Checks performed for this note: frozen hashes and all 34 case artifacts;
manual commands/map/frame inspection; raw-counter parsing using the existing
runner; all 514 saved outputs against its arbitrary-precision reference,
retained histories, guards and 98-byte states; direct inspection of source and
full/extracted disassemblies; and an in-memory linear symbolic propagation of
the first arithmetic iteration. The latter recovered exactly the two source
coefficient groups at G10 `0x08000376/0x0800038e` and G15
`0x08000478/0x0800048e`, using modulo-2^32 machine arithmetic. It was a
read-only corroborating check, not a committed analyzer or a simulator trace.
No binary was rebuilt, no optimization flags changed, and no new performance
run was made. Analyzer/test integration and independent review are coordinator
tasks, not claimed complete by this note.

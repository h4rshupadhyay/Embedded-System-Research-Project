# GCC10 versus GCC15 block1 partial-direct code: evidence and accounting

## Fixed comparison

This audit uses only the two saved `speech_minphase48` / `partial_direct32x2`
BLOCK=1 binaries for the first 257 frozen `adc_raw` samples, zero initial
history, the fixed `[0,2)` and `[2,48)` groups, Cortex-M0 Thumb, `-O2`, and
no LTO. It does not create a new performance row or change the measurement
boundary. Costs below are Arm-table cycle and CPU-energy model estimates, not
hardware measurements.

The design, original sharing result, partial-direct result, kernel source and
six-case evidence archive match all five SHA256 values in the shared plan. The
two block1 binaries match the plan's SHA256 values. After restoring the
versioned archive, all 102 listed artifact hashes across six cases match the
partial-direct result; only the two block1 cases enter this audit. Their
saved `O:`, `H:`, `G:`, and `M:` records independently match arbitrary-precision
convolution, the retained 47 chronological samples, state/output guards and
98-byte state allocation.

The saved raw stderr reports 198,671 and 242,491 executed instructions. The
fixture's closing GPIO marker contributes one instruction inside those raw
counts, so the established ROI contains 198,670 and 242,490 instructions.
Setup and result printing remain outside the ROI. The other event counts are
read directly from the saved raw logs; raw simulator ticks are diagnostic only.

| Event or estimate | GCC10 | GCC15 | GCC15 minus GCC10 |
|---|---:|---:|---:|
| Instructions | 198,670 | 242,490 | +43,820 |
| MUL | 2,827 | 2,827 | 0 |
| RAM reads | 29,304 | 43,182 | +13,878 |
| RAM writes | 17,225 | 36,500 | +19,275 |
| Flash data reads | 1,032 | 1,032 | 0 |
| Flash writes | 0 | 0 | 0 |
| Taken branches | 13,622 | 13,753 | +131 |
| BL | 258 | 258 | 0 |
| Arm-table zero-wait cycles | 273,733 | 350,968 | +77,235 |
| Modeled CPU energy (nJ, complete stream) | 266,394.093850 | 336,863.793775 | +70,469.699925 |

The cycle delta reconstructs as `43,820 + 13,878 + 19,275 + 2×131 =
77,235`. The energy delta reconstructs from the frozen model as
`0.964258×43,820 + 1.109833×13,878 + 0.650563×19,275 +
2.091986×131 = 70,469.699925 nJ`. Neither aggregate arithmetic identifies
the source of each access. The identical MUL and Flash-data-read totals do
not imply identical product lowering or literal-use locations.

## Generated-code observations and attribution

The compiler-reported `probe_process` frame rises from 72 to 240 bytes.
This is a static frame report, not peak physical stack use. Both emitted
functions retain 32-bit partial arithmetic, sign-extend each completed
partial, and perform one `adds`/`adcs` wide reduction; the exact addresses and
representative source-value paths are in [assembly-notes.md](assembly-notes.md).
The static assembly is evidence of the generated instruction choices. It does
not provide execution frequencies for all basic blocks or prove that a stack
temporary was an allocator spill.

The saved wrapper passes `b=1` on all 257 calls. The assembly's direct
SP-relative LDR/STR sites lie on once-per-call paths, apart from GCC10's
`0x08000406` store on the unused `b=0` path. The quantizer alternatives rejoin
before the stack-heavy tail, and the 47-iteration history-copy loop contains
no direct-SP sites. This establishes the following **control-flow deduction**
without a per-PC execution trace:

| Executed direct-SP transfer | GCC10 per call | GCC15 per call | Stream delta |
|---|---:|---:|---:|
| LDR | 9 | 63 | +13,878 |
| STR | 9 | 84 | +19,275 |

The two deltas exactly match the saved RAM-event deltas. They also contribute
33,153 executed instructions, 66,306 Arm-table cycles, and 59,909.909673 nJ
of modeled CPU energy. The remaining aggregate deltas are 10,667
instructions, 131 taken branches, 10,929 cycles, and 10,559.790252 nJ;
their specific generated-code causes remain unresolved. These cycle and energy
figures apply the frozen event-cost model to the accounted events; they are
not measured target power. The direct-SP observation explains traffic, not
which compiler pass placed the values on the stack.

The [component accounting](accounting.json) assigns only MUL instructions
and these path-proved direct-SP instructions to nonresidual components. Other
events, including ABI push/pop and source history loads/stores, remain in
`unattributed` where their per-component execution has not been fully mapped.
Zero events in a named component mean no demonstrated assignment, not an
absent operation. The component sums reconcile to each saved ROI total;
[assembly-notes.md](assembly-notes.md) supplies the PC ranges, value flow and
full independent RAM-traffic reconciliation. The static site annotations in
`evidence/` are diagnostics and are not multiplied into dynamic counts outside
the proved block1 paths.

| Accounted component, GCC15 minus GCC10 | Instructions | RAM reads | RAM writes | Taken branches |
|---|---:|---:|---:|---:|
| Stream wrapper | 0 | 0 | 0 | 0 |
| Copy-in direct-SP sites | -1,028 | -514 | -514 | 0 |
| Convolution arithmetic and direct-SP sites | +33,667 | +13,878 | +19,789 | 0 |
| Quantize/store direct-SP sites | +257 | +257 | 0 | 0 |
| History-copy setup direct-SP sites | +257 | +257 | 0 | 0 |
| Function entry/exit | 0 | 0 | 0 | 0 |
| Unattributed | +10,667 | 0 | 0 | +131 |
| **Total** | **+43,820** | **+13,878** | **+19,275** | **+131** |

MUL, Flash reads/writes and BL have zero GCC15-minus-GCC10 delta in every
component. These phase labels follow the declared PC boundaries in the
hashed site classifications; they do not certify the source-level reason for
each stack-resident value. In particular, the GCC15 loop-tail sample rotation
is classified with convolution, while the source history-copy setup starts
later at `0x08000532`.

## Limits and handoff

The saved aggregate logs do not contain per-PC execution histories. Optional
replay would require the same binary bytes, a logging-only isolated simulator,
and exact output/event reconciliation before treating any trace as evidence.
The pinned Arm GCC, objdump and simulator executables were unavailable on this
host; no live replay or new target measurement was performed. Any such target
measurement remains pending. The accepted dynamic totals here come only from
the versioned saved evidence and its verified binary identities.
No alternative compiler flags, new kernels, physical energy data or optimizer
were introduced. The narrower conclusion is about this frozen case and
the two saved compiler outputs, not a compiler defect or a universal FIR rule.

The requested worker routing was `gpt-6-sol` with high effort for analyzer and
`gpt-6-astra` with high effort for assembly, followed by a fresh
`gpt-6-astra` high-effort read-only review. The collaboration interface did
not expose an independent runtime model/effort attestation, so actual routing
beyond the accepted requests remains unverified. The worker outputs, test
results, and review handling are recorded in [review.md](review.md).

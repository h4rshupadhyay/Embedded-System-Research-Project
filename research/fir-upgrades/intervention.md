# Bounded block-1 intervention

**Status: all eight declared rows admitted; assembly interpretation pending
independent review.** The only performance condition is the original 257-sample
`speech_minphase48` ADC fixture with `BLOCK=1`; the two general rows reproduce
the saved firmware binaries and full corrected event vectors exactly. The two
literal-1 specializations and four 361-sample signed-edge correctness runs
were admitted from their saved outputs and raw event streams. The specialization
is defined only for the precondition `b=1`.

| Compiler | General energy (nJ) | Literal-1 energy (nJ) | General minus specialized (nJ) | Stack peak general → specialized (bytes) |
| --- | ---: | ---: | ---: | ---: |
| GCC10 | 266394.09385 | 242800.957748 | 23593.136102 | 144 → 92 |
| GCC15 | 336863.793775 | 230943.514627 | 105920.279148 | 312 → 88 |

The reconstructed compiler gap is `G_general = 70469.699925 nJ` and
`G_specialized = -11857.443121 nJ`, so `G_general - G_specialized =
82327.143046 nJ`. Both strict numeric comparisons hold: GCC15 specialized
energy is below GCC15 general energy, and `G_specialized < G_general`.
The stronger conjunction remains **pending independent assembly review**;
these measurements alone do not identify removed preparation traffic or
establish compiler-pass causation.

The separate edge stream is a correctness check, not a second performance
claim. All eight rows retain the fixed 98-byte state allocation. Their full
raw counters, traces, binary/input bindings, memory layout, instruction sets,
and conservative stack chains are independently rederived by `--verify`.
The final saved audit reports 4 performance rows, 4 correctness rows,
`comparability: admitted`, and no tool execution during verification. The
independent historical general anchors match both binary SHA-256 values and
all ten corrected event counters exactly. One initial GCC10 attempt was kept
after a tool-path admission rejection and reused after correcting the path
basename rule; each of the eight scientific identities has exactly one
attempt directory.

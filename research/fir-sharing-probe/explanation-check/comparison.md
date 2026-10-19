# GCC10/GCC15 block1 explanation check

Frozen `partial_direct32x2`, `speech_minphase48`, 257 samples, full-int16, `-O2`, no LTO. Values below are reconstructed from the original raw simulator logs and frozen result, with the closing marker instruction excluded.

Peer accounting status: **pending**; 0 peer rows checked. Manual causal review: **pending**. The checker tests arithmetic and file identity, not whether PC labels establish a cause.

| Counter | GCC10 | GCC15 | GCC15 − GCC10 |
|---|---:|---:|---:|
| instructions | 198670 | 242490 | 43820 |
| mul | 2827 | 2827 | 0 |
| ram_reads | 29304 | 43182 | 13878 |
| ram_writes | 17225 | 36500 | 19275 |
| flash_reads | 1032 | 1032 | 0 |
| flash_writes | 0 | 0 | 0 |
| taken_branches | 13622 | 13753 | 131 |
| bl | 258 | 258 | 0 |

Estimated zero-wait cycles: 273733 / 350968; delta **77235**.
Modeled CPU nJ: 266394.093850 / 336863.793775; delta **70469.699925 nJ**.

These are simulator/model aggregates, not measured wall time or board energy. Static frame, symbol and stack-address sites are diagnostics, not dynamic event counts.

| Compiler | Block | Lowest modeled CPU-energy candidate |
|---|---:|---|
| gcc10 | 1 | partial_direct32x2 |
| gcc10 | 64 | partial_direct32x2 |
| gcc15 | 1 | trans_hcub_demand |
| gcc15 | 64 | trans_hcub_demand |

Within GCC15/block1, demand Hcub uses 24.06% less modeled energy than GCC15 partial direct. When selecting the lower-cost compiler for each variant, GCC15 demand Hcub saves 3.97% at block1 and 2.30% at block64 relative to GCC10 partial direct. These denominators describe different comparisons.

The real peer `accounting.json` has not been delivered. Fixture tests are illustrative and do not verify a generated-code explanation.

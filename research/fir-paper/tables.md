# Derived results tables

All reported energy margins use unrounded whole-stream modeled totals. Display values are rounded to two decimal places.

| Compiler | Block | Variant | Cycles/output | Energy (nJ) |
|---|---:|---|---:|---:|
| gcc10 | 1 | cmsis64_unroll | 1585.11 | 395063.83 |
| gcc10 | 1 | spec_direct | 1606.11 | 396560.23 |
| gcc10 | 1 | partial_direct32x2 | 1065.11 | 266394.09 |
| gcc10 | 1 | trans_const | 1106.11 | 268764.73 |
| gcc10 | 1 | trans_hcub_demand | 1150.11 | 277931.05 |
| gcc10 | 64 | cmsis64_unroll | 924.32 | 232826.38 |
| gcc10 | 64 | spec_direct | 1029.33 | 254531.60 |
| gcc10 | 64 | partial_direct32x2 | 583.31 | 147984.28 |
| gcc10 | 64 | trans_const | 630.64 | 155655.84 |
| gcc10 | 64 | trans_hcub_demand | 636.40 | 155387.80 |
| gcc15 | 1 | cmsis64_unroll | 1550.11 | 386316.70 |
| gcc15 | 1 | spec_direct | 1798.11 | 440002.64 |
| gcc15 | 1 | partial_direct32x2 | 1365.63 | 336863.79 |
| gcc15 | 1 | trans_const | 1100.11 | 267277.85 |
| gcc15 | 1 | trans_hcub_demand | 1062.11 | 255825.28 |
| gcc15 | 64 | cmsis64_unroll | 851.98 | 215583.48 |
| gcc15 | 64 | spec_direct | 1074.65 | 262936.10 |
| gcc15 | 64 | partial_direct32x2 | 612.39 | 152553.70 |
| gcc15 | 64 | trans_const | 627.57 | 154936.72 |
| gcc15 | 64 | trans_hcub_demand | 593.49 | 144576.38 |

## H_R cell margins

| Compiler | Block | Hcub vs partial-direct energy (%) | Passes strict superiority |
|---|---:|---:|---|
| gcc10 | 1 | 4.33 | no |
| gcc10 | 64 | 5.00 | no |
| gcc15 | 1 | -24.06 | yes |
| gcc15 | 64 | -5.23 | yes |

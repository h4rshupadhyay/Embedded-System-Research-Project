# Missing-direct-baseline comparison

Filter `speech_minphase48`; full-int16 guarantee; 257 frozen ADC samples; `-O2`, Cortex-M0 Thumb, no LTO. Costs include recurring state, stream, call and final short-block work. All costs below are estimates, not physical measurements.

Each historical row was independently checked against raw output/history/guards, event counters, artifact hashes, ELF symbols and compiler stack reports. The peer result remains pending until four complete rows pass the same checks.

| Compiler | Block | Variant | Status | Cycles/output | Modeled nJ/output | Kernel+coefficient symbol bytes | State bytes | Wrapper frame bytes |
|---|---:|---|---|---:|---:|---:|---:|---:|
| gcc10 | 1 | cmsis64_unroll | verified historical | 1585.11 | 1537.21 | 1494 | 112 | 8 |
| gcc10 | 1 | spec_direct | verified historical | 1606.11 | 1543.04 | 1736 | 98 | 440 |
| gcc10 | 1 | trans_const | verified historical | 1106.11 | 1045.78 | 1540 | 192 | 272 |
| gcc10 | 1 | trans_hcub_demand | verified historical | 1150.11 | 1081.44 | 1504 | 192 | 344 |
| gcc10 | 1 | partial_direct32x2 | pending | — | — | — | — | — |
| gcc10 | 64 | cmsis64_unroll | verified historical | 924.32 | 905.94 | 1494 | 236 | 8 |
| gcc10 | 64 | spec_direct | verified historical | 1029.33 | 990.40 | 1720 | 224 | 440 |
| gcc10 | 64 | trans_const | verified historical | 630.64 | 605.66 | 1540 | 192 | 272 |
| gcc10 | 64 | trans_hcub_demand | verified historical | 636.40 | 604.62 | 1504 | 192 | 344 |
| gcc10 | 64 | partial_direct32x2 | pending | — | — | — | — | — |
| gcc15 | 1 | cmsis64_unroll | verified historical | 1550.11 | 1503.18 | 1450 | 112 | 8 |
| gcc15 | 1 | spec_direct | verified historical | 1798.11 | 1712.07 | 1872 | 98 | 608 |
| gcc15 | 1 | trans_const | verified historical | 1100.11 | 1039.99 | 1532 | 192 | 272 |
| gcc15 | 1 | trans_hcub_demand | verified historical | 1062.11 | 995.43 | 1352 | 192 | 344 |
| gcc15 | 1 | partial_direct32x2 | pending | — | — | — | — | — |
| gcc15 | 64 | cmsis64_unroll | verified historical | 851.98 | 838.85 | 1450 | 236 | 8 |
| gcc15 | 64 | spec_direct | verified historical | 1074.65 | 1023.10 | 1884 | 224 | 608 |
| gcc15 | 64 | trans_const | verified historical | 627.57 | 602.87 | 1532 | 192 | 272 |
| gcc15 | 64 | trans_hcub_demand | verified historical | 593.49 | 562.55 | 1352 | 192 | 344 |
| gcc15 | 64 | partial_direct32x2 | pending | — | — | — | — | — |

gcc10, block 1: strongest historical nontransposed energy control `cmsis64_unroll`; cycle control `cmsis64_unroll`.
gcc10, block 64: strongest historical nontransposed energy control `cmsis64_unroll`; cycle control `cmsis64_unroll`.
gcc15, block 1: strongest historical nontransposed energy control `cmsis64_unroll`; cycle control `cmsis64_unroll`.
gcc15, block 64: strongest historical nontransposed energy control `cmsis64_unroll`; cycle control `cmsis64_unroll`.

Code-size metric matches the historical selected-symbol diagnostic: `probe_process`, named kernel/library functions, `quant*`, and `h.0`/`reversed.0` coefficient symbols when present. It excludes fixture code and can exclude other compiler-generated helpers; it is not total image size. The full included symbol map is in `verification.json`.

Wrapper frame is `probe_process` alone, not peak stack. Callee frames (including library/kernel frames) are recorded separately in `kernel_function_frames` in `verification.json`. Static compiler reports do not establish maximum live stack or physical SRAM high-water usage.

Decision remains conditional. These already-inspected cases are a missing-control check, not fresh held-out validation. A surviving benefit/tradeoff still needs an emitted-code explanation and the prior-art distinctions in [positioning.md](positioning.md). An erased benefit requires revising the headline; no peer values are inferred.

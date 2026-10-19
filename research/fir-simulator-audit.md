# FIR simulator and energy-model audit

19 October 2026. Primary documentation and source inspection; no simulator/baseline source edited and no hardware validation performed in this audit.

## Decision for the first experiment

**Use the pinned modified Thumbulator for correctness and scoped target instruction/event counts. Do not label its printed raw `ticks` as verified STM32F051 cycles.** Source inspection found concrete timing discrepancies. A separate, explicit Arm zero-wait-state trace timing calculation is possible, but it would be our documented timing estimate—not an independently reproduced Nikov hardware-validated model. Until such a calculation is implemented and checked, report events and diagnostic raw ticks separately.

The original [David Welch Thumbulator README](https://github.com/dwelch67/thumbulator/) explicitly disclaims necessary cycle accuracy to any real Arm core; its memory-bus assumptions are unsuitable grounds for a Cortex-M0 timing claim. The relevant research fork is [PicoPET/thumbulator-stm32f0x](https://github.com/PicoPET/thumbulator-stm32f0x), not an arbitrary repository carrying the Thumbulator name.

## Exact source inspected

Local clean checkout: `/tmp/esproj-thumbulator-research-20261019`, origin `https://github.com/PicoPET/thumbulator-stm32f0x.git`, commit and `teamplay-D4.5` tag both resolve to:

`c55ea1b1926b792d7aabb7e3495b55a7b69ef134`.

Pin this identity in artifacts. The [README](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/README.md) calls it cycle accurate; the implementation details below prevent adopting that description uncritically for the raw tick output.

### Raw tick problems

- [`exmemwb.c`, lines 381–390](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/exmemwb.c#L381): each instruction handler returns `insnTicks`; the main counter simply adds these. This is distinct from retired instruction count.
- [`exmemwb_mem.c`, line 140](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/exmemwb_mem.c#L140) contains `return 1 + numLoaded + takenBranch ? TIMING_PC_UPDATE : 0;`. C precedence tests the entire sum, so ordinary POP returns the constant `TIMING_PC_UPDATE` (2), regardless of how many registers it restores. This is a source-level finding, not a runtime microtest result.
- [`exmemwb.h`, lines 118–121](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/exmemwb.h#L118) sets branch cost to 2, branch-link to 3 and memory cost to 2. [`exmemwb_branch.c`](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/exmemwb_branch.c#L81) uses those constants for taken branches; conditional not-taken returns 1.
- [`sim_main.c`, lines 279–287](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/sim_main.c#L279) counts branch-fetch stalls separately. [`sim_support.c`, lines 622–628 and 640 onward](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/sim_support.c#L622) likewise counts arbitration conflicts/prefetch behavior. These counters are not automatically charged to `cycleCount` there.

These errors can affect relative implementation rankings: routines with different function calls, register saves/restores and loop branch counts need not share a constant timing offset. Simply correcting POP parentheses does not establish full timing accuracy.

### What can be configured and counted

[`sim_main.c`, lines 115–165](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/sim_main.c#L115) exposes single-word (`-pw`) and three-word-buffer (`-pb`) prefetch modes plus reporting flags. The inspected CLI has **no wait-state or frequency selection**. [`sim_support.c`, line 92](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/sim_support.c#L92) defaults prefetch to NONE. [`sim_support.h`, lines 6–12](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/sim_support.h#L6) allows 64 KiB RAM and 1 MiB Flash and defines `CPU_FREQ=48000000`; that constant does not prove 48 MHz Flash timing is modeled, nor enforce a particular STM32F051 package's capacity.

[`exmemwb_arith.c`, lines 248–265](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/exmemwb_arith.c#L248) explicitly models STM32F0 MULS as one cycle. Never substitute the generic core's optional 32-cycle multiplier silently. [`sim_support.c`, lines 188–209 and 304–322](https://github.com/PicoPET/thumbulator-stm32f0x/blob/c55ea1b1926b792d7aabb7e3495b55a7b69ef134/sim_support.c#L188) reports memory/branch/dependency events; per-opcode statistics provide multiplication counts. Counts must use the same start/stop region and enable state; setup, reference comparisons and output printing must not contaminate kernel statistics.

## Primary timing evidence and the missing reconstruction

Nikov et al., [*Accurate Energy Modelling on the Cortex-M0 Processor for Profiling and Static Analysis*](https://arxiv.org/html/2301.12806), §2.4, says the execution-time model **derived from event counts** matches hardware when prefetch is disabled or wait states are zero; with prefetch enabled and one wait state its reported timing MAPE is 1.55%. This is their evaluated model claim, not permission to equate our checkout's raw tick counter with that derived model. The paper does not give the explicit event-to-cycle reconstruction equation. The inspected repository tree contains no postprocessing timing implementation. The linked [Bristol dataset record](https://research-information.bris.ac.uk/en/datasets/stm32f0discovery-cortexm0-energy-model-data/) was located, but its data-server download could not be fetched during this audit. The equation/mapping therefore remains unresolved.

The same paper's platform discussion excludes off-core peripherals from its CPU model and identifies ten frequency/prefetch/wait-state combinations. Its Table 2 gives configuration-specific energy coefficients. For `[20 MHz, prefetch OFF, wait states 0]`, the coefficients for `[non-MUL instructions, MUL, taken branches, RAM reads, RAM writes, Flash data reads]` are `[0.964258, 1.652455, 2.091986, 1.109833, 0.650563, 0.633621]` nJ/event. These are not interchangeable with another coefficient set.

## An explicit zero-wait-state timing alternative

[Arm Cortex-M0 TRM DDI0432C, §3.3, Table 3.1](https://support.arm.com/documentation/ddi0432/c/programmers-model/instruction-set-summary?lang=en) gives timing assuming zero wait states. Relevant checks are:

| Instruction | Arm table cycles | Inspected raw handler |
|---|---:|---:|
| Ordinary integer ALU | 1 | Typically 1 |
| MULS | 1 or 32, implementation option | 1 |
| Ordinary LDR/STR | 2 | 2 |
| Conditional branch not taken / taken | 1 / 3 | 1 / 2 |
| B or BX | 3 | 2 |
| BL | 4 | 3 |
| PUSH, N total registers | 1+N | 1+N |
| POP without PC, N registers | 1+N | 2 |
| POP with PC, N low registers | 4+N | 2 |

An instrumented assembly microtest should independently count each row's dynamic instructions and compare the corresponding **declared trace model** to these expected costs, including several POP register lists and taken/not-taken loops. This is documentation-based verification, not hardware validation. Do not approximate every memory instruction as one memory event: LDM/STM/PUSH/POP transfer several registers with different timing. Account for BL's 32-bit encoding as one architectural instruction. A corrected trace model must be reviewed for every opcode emitted by the actual FIR binaries, especially helper calls and returns.

For a first controlled model, keep code in Flash and state in SRAM, with a declared zero-wait-state/no-prefetch configuration such as 20 MHz. This is a proposed model configuration, not a working option already supplied by the CLI. [ST AN4088](https://www.st.com/resource/en/application_note/an4088-migrating-between-stm32f1-and-stm32f0-series-microcontrollers-stmicroelectronics.pdf) documents STM32F0 at 48 MHz using one Flash wait state and prefetch, so labeling a zero-wait-state calculation as 48 MHz target behavior would be misleading.

## The six EnergyAnalyzer coefficients

Wegener et al., [*EnergyAnalyzer*, WCET 2023](https://arxiv.org/html/2305.14968), §4.1, supplies the following CPU energy model in nJ:

`E = 0.972565030*nonMUL + 0.652871770*RAM_reads + 1.031341343*RAM_writes + 1.037625441*Flash_data_reads + 1.354953706*taken_branches + 2.274650563*MUL`.

The source reports 2.8% MAPE against its physical training/validation measurements. That is not an error guarantee for this FIR study. Its text does not unambiguously assign this exact coefficient set to one of Nikov's ten configurations; the weights also differ from Nikov's Table 2. Therefore do not silently call these “20 MHz zero-wait-state weights” or use them to validate timing. Events overlap intentionally: loads/branches are also non-MUL instructions; they receive the base instruction coefficient and their additional event coefficient. Flash data reads exclude instruction fetches. This is a CPU/model estimate, not measured board energy or a certified upper bound.

## Reporting recommendation

For now publish correctness checks, scoped target architectural instruction counts, per-opcode counts and memory/branch events. Keep raw ticks in diagnostics with the known defects. Add cycles only with a fully specified independently checked reconstruction; add energy only with an explicit compatible configuration/model and matching counter semantics. Preserve original and any instrumented simulator hashes, linker map, compiler flags and region definitions. A failed timing audit is useful experimental provenance; hiding it would undermine the FIR comparison.

## Reviewed follow-up: proposed explicit architectural timing calculation

For a restricted whitelist of instructions, the root agent proposes

`C_arch_0ws = NI + Rram + Wram + Rflash + 2*Btaken + Nbl`.

Here `NI` is the architectural instruction count including MUL, `R/W` count data-transfer events, `Btaken` includes every actual control transfer (including POP-to-PC and return BX), and `Nbl` counts BL as one architectural instruction despite its 32-bit encoding. Require zero Flash writes and no peripheral accesses in the region; programming Flash is not an ordinary SRAM-like store. A byte or halfword transfer contributes one event, just as a word transfer does; multiple-register instructions contribute one event per transferred register.

**The formula agrees algebraically with the cited Arm zero-wait-state table for the stated whitelist:** one-cycle ordinary ALU/MUL/NOP/extension/shift instructions, ordinary loads/stores, LDM/STM/PUSH/POP, B/Bcc/BX/BLX/BL, and marked ALU writes to PC. In particular POP-to-PC gets `1+(Nlow+1)+2=4+Nlow`, and BL gets `1+2+1=4`. This is a reviewed proposal, not a claim that its instrumentation or microtests have already passed.

Source checks support the counter interpretation: `alu_write_pc` in `exmemwb.h` marks a taken transfer; `bl()` increments its dedicated count; subword stores use `simLoadData_internal(...,falseRead=1)`, whose implementation suppresses the emulation-internal read from architectural memory counters. Do not apply the formula to arbitrary Thumb code: reject unhandled MRS/MSR, barriers, sleep/event-wait operations, exceptions, peripheral accesses or other instructions with different timing, unless explicit rules are separately added. Inspect every opcode executed by library helpers as well as the FIR loop, and ensure all counters cover precisely the same region. No dependency or prefetch corrections are implicitly included.

This may be reported after successful microchecks as **an Arm-table-based architectural zero-wait-state timing estimate**, with no claim of STM32-specific hardware validation or reproduction of Nikov's unpublished reconstruction. Independently, a selected Nikov Table 2 energy equation can be applied to matching verified event semantics and the stated configuration; it does not depend on the broken raw tick counter. Keep timing and energy provenance separate.

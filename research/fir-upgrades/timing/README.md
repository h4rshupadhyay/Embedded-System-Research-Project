# Corrected Arm-table timing, version 2

This is the current manuscript's timing source. The historical inventories,
first paper, calculators and archive preserve version 1's cycle proxy for
reproducibility. Those cycle fields omit one cycle per return-by-POP and are
superseded here. Do not use the frozen v1 calculators for new timing claims.

For the checked scalar instruction subset, zero waits and single-cycle MUL:

`cycles = NI + RAM_reads + RAM_writes + Flash_data_reads + 2*taken_branches + BL + POP_PC`

Arm DDI 0432C §3.3 Table 3-1 assigns `POP {...,PC}` 4+N cycles, with N
including PC. The old expression supplies only 3+N. The saved counter named
`PUSH/POP PC/LR` is incremented by the pinned simulator's POP handler when
PC is restored; it is not a combined push-LR/pop-PC count. Other allowed
ALU/extend/shift operations use one cycle; loads/stores and multiple transfers
use their event counts, taken branches add two, and BL adds one further cycle.
MRS/MSR, barriers, waits, Flash writes and other unmodeled instructions are
rejected. This is a table-based estimate, not hardware timing validation.

Rebuild or verify the report from the repository root:

```sh
python3 research/fir-upgrades/timing_correction.py
python3 research/fir-upgrades/timing_correction.py --verify
python3 -m pytest -q research/fir-upgrades/test_timing_correction.py
```

The tool reads only saved evidence. It checks pinned source inventories,
raw stderr, disassembly and binary hashes; reconstructs events and the POP-PC
counter; checks the linked scalar subset; and reproduces the frozen energy
totals. No compiler, simulator, graph generator or firmware is executed.
It is usable on a relocated tree containing these sources and the saved
evidence. It is separate from the historical archive's own verification.

`corrected-timing.json` retains the old and corrected totals and corrected
per-output values for 20 original, 280 admitted panel and four intervention
identities. These are reporting identities, not 304 new experiments; original
general controls and intervention anchors overlap. Eight unavailable panel
identities remain explicit. All energies are unchanged. The twelve original
event-analysis cycle differences, 680 known within-condition panel pair
orderings, and two intervention cycle reductions are unchanged by the
correction. Other historical cycle comparisons require these corrected totals.

The original `pop_pc` microsequence gives an independent regression:
BL4 + B3 + PUSH(1+2) + POP-PC(4+2) = 16 cycles. The frozen v1 microcheck
expects 15; that historical check validates the old formula, not Arm's table.
The current regression expects 16. Four intervention rows each add 258
cycles; for example GCC15 general changes from 350,968 to 351,226.

Source: [Arm Cortex-M0 Technical Reference Manual, DDI 0432C](https://documentation-service.arm.com/static/5e8e294afd977155116a6a5b).

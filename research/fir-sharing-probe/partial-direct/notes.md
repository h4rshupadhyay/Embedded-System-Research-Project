# Fixed partial-direct control: handoff status

The kernel implements only `speech_minphase48` with the frozen zero-based groups
`[0,2)` and `[2,48)`. It uses the same unrolled direct history, streaming call,
and single quantizer organization as `spec_direct`. The frozen design and
sharing-results SHA256 values match the handoff and were not changed.

## Arithmetic certificate

For every signed-int16 input, `|x| <= 32768`. The first group's coefficient L1
sum is 12,778, so every prefix is bounded by 418,709,504. The second group's
L1 sum is 59,731, so every prefix is bounded by 1,957,265,408. Every individual
product is bounded by its group's prefix bound. All fit signed int32. The full
bound is 2,375,974,912, so the completed partials are each converted to int64
*before* their addition. That addition fits int64. `quant` clamps before its
int32 conversion and implements negative floor division without relying on
implementation-defined right shifts. It quantizes once, after exact reduction.

The state is `int16_t history[48+BLOCK]` (98 bytes for BLOCK=1, 224 bytes for
BLOCK=64). The first 47 elements returned by `probe_get_state` are the
chronological retained samples. Initialization zeros the entire allocation.

## Host evidence

Tests were written before `kernel.c`. The initial command
`python -m unittest discover -s research/fir-sharing-probe/partial-direct -p test_kernel.py -v`
failed in `setUpClass` because `kernel.c` did not yet exist, as expected.

After implementation, Ubuntu GCC 13.3.0 passed the three tests with
`FIR_UBSAN=1 python3 -m unittest discover -s research/fir-sharing-probe/partial-direct -p test_kernel.py -v`.
This builds with `-fsanitize=undefined -fno-sanitize-recover=undefined` and
`UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. Output: `Ran 3 tests in
0.672s`, `OK`. The kernel source did not change after this run. Subsequently
the negative-floor test gained explicit exact sums `-32769`, `-32768`,
`-32767`, `-1`, `0`, and `1`; the final expanded suite passed all three tests
with Windows MinGW GCC 6.3.0, without UBSan (`Ran 3 tests in 0.471s`, `OK`).
The final expanded suite still needs a repeat UBSan run once Ubuntu works.

The tests cover coefficient-sign-aligned full-scale windows with positive
and negative complete sums outside int32, signed extrema, initial zeros,
saturation, arbitrary-precision output equality, every retained-history
snapshot, state/output guards, mixed `1/64/3/16` partitions, and the
64/64/64/64/1 short final call. A separate host compile checked the generated
target fixture for both BLOCK values with `-Wall -Wextra -Werror`.

## Target evidence pending

`run.py --check` reports the pinned Thumbulator binary and both Arm compilers
absent from this checkout. An attempt to reproduce the environment in WSL
verified the official Ubuntu GCC 10.3.1 executable's SHA256 as
`702dfc4dd0b34ee43ecd164a6db6ada4b5583d8945b17bbea3ebe223db765480`.
The Windows C: volume then ran out of free space while Ubuntu expanded its
virtual disk. WSL mounted read-only and later failed to start, so no target
binary or event trace was produced. The temporary download under
`/tmp/fir-partial-tools` could not be removed while WSL was unavailable.
No target event counts, modeled cycles/energy, code size, stack diagnostics,
or assembly observations are claimed. `results.json` has no measured rows;
its four pending configurations are identifiers only. Native-width partial
adds and final wide-reduction lowering remain to be checked in each target
`probe_process.disasm` after the environment is restored.

From a pinned Linux environment, use the original baseline simulator and
compilers or set `FIR_SIMULATOR`, `FIR_GCC10`, and `FIR_GCC15` to their paths.
The runner verifies their hashes/versions against the frozen sharing result.
Run `python3 research/fir-sharing-probe/partial-direct/run.py --check`, then
`python3 research/fir-sharing-probe/partial-direct/run.py`, then the same
command with `--verify`. It compiles four timed configurations and two
separate signed-edge correctness binaries. It uses the baseline simulator's
event parser and cost functions; raw ISS ticks remain diagnostic. Each case's
source, ELF/binary, map, disassembly, stack reports, size, raw stdout/stderr,
and hashes are saved under this directory's ignored `build/target/`.
After a target run, inspect the four `probe_process.disasm` files and record
their actual partial-add and reduction lowering before treating the result as
complete. Archive `build/target/` separately with any shared results because
Git ignores generated binaries and raw logs. No historical matrix needs rerun.

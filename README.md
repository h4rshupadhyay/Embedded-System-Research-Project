# Embedded software energy research

A reproducible Cortex-M0 FIR profiling harness, an explicitly synthetic supply
model, and the literature record for the next research direction.

**Current result:** the added regulator-history predictor provided **zero
implementation-selection savings in 207 primary simulated conditions**. Both
predictors chose the virtual circuit's lowest-energy implementation every time.
The recommendation is to stop this particular model as a route to a selection
contribution. This does not validate or reject the physical hypothesis: supply
parameters and per-job power profiles are uncalibrated.

Start with the [bounded-study findings](docs/research/BOUNDED_STUDY_FINDINGS.md)
and [canonical result](results/bounded_energy_study/SUMMARY.md).

## Current research tracks

| Track | Status | Read |
|---|---|---|
| A: energy-estimator reliability on unfamiliar code | Conditional replication/evaluation candidate; feasibility first | [Literature check](docs/research/CANDIDATE_A_LITERATURE_CHECK.md) |
| B: state, buffer and call-contract testing of DSP libraries | Peer investigation; needs a comparative benchmark framing | [Literature check](docs/research/CANDIDATE_B_LITERATURE_CHECK.md) |

Neither track has established novelty. The [combined literature verdict](docs/research/CANDIDATES_LITERATURE_VERDICT.md)
explains the existing work, possible remaining questions and stopping conditions.
The complete [research index](docs/research/README.md) distinguishes current
assessments from earlier notes.

## Repository map

| Location | Contents |
|---|---|
| `fir.c`, `fir.h`, `main.c` | Corrected streaming Q15 kernels and bare-metal harness |
| `startup.s`, `stm32f051.ld`, `flags.mk`, `Makefile` | Cortex-M0 startup, memory layout and build configuration |
| `run_sim_pilot.py` | Correctness-gated compiled profiling of marked FIR calls |
| `energy_model.py`, `run_energy_hypothesis.py` | Averaged-buck reference, steady baseline and fitted history predictor |
| `run_bounded_energy_study.py`, `configs/` | Fixed broader workload study and model configurations |
| `tests/` | Integer-reference, sanitizer, simulator and energy-model checks |
| `patches/` | Changes required for the external Thumbulator source |
| `results/` | Canonical profiles, reports and frozen study provenance |
| `docs/research/` | Literature checks, protocols and findings |
| `run_experiments.py`, `analyze_rankings.py`, root CSVs | Historical sweep and ranking workflow |

The simulator executable, external source checkout, firmware binaries, Python
caches and additional runs under `results/local/` are local build/run artifacts
and are ignored by Git. Canonical evidence is versioned.

## Setup

Run commands from the repository root. The recorded environment uses Python 3.10
and the versions in [requirements-model.txt](requirements-model.txt).

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-model.txt
```

Host checks need GCC with AddressSanitizer and UBSan. Generating profiles or
running the broader study additionally needs `make`, `git`, `arm-none-eabi-gcc`,
`arm-none-eabi-objcopy`, and the patched simulator. Building the simulator needs
host GCC and OpenSSL development libraries. Missing Arm tools cause explicit
integration-test skips; runners that require them fail with a clear error.

### Build the simulator

The recorded upstream revision is `c55ea1b1926b792d7aabb7e3495b55a7b69ef134`
from the `teamplay-D4.5` branch. Apply the patch once to a clean checkout:

```bash
git clone https://github.com/PicoPET/thumbulator-stm32f0x.git
git -C thumbulator-stm32f0x checkout c55ea1b1926b792d7aabb7e3495b55a7b69ef134
git -C thumbulator-stm32f0x apply ../patches/thumbulator_stm32f0x.patch
make -C thumbulator-stm32f0x board
cp thumbulator-stm32f0x/sim_main ./thumbulator
```

The patch adds multiply-counter accounting, marked-interval reports, simulated
console output and finite-program termination support. The executable is rebuilt
locally; its hash is recorded in each simulator profile.

## Run checks and experiments

```bash
make test

# Keep additional runs separate from the versioned evidence.
mkdir -p results/local
make pilot PILOT_OUTPUT=results/local/pilot.json
make energy-model MODEL_OUTPUT=results/local/energy_run
make bounded-study STUDY_OUTPUT=results/local/bounded_run STUDY_WORKERS=2
```

Use a new output filename or directory for each run: the runners refuse to
replace existing reports. A supplied pilot can be evaluated without the Arm
toolchain; generating a pilot or broader-study profiles requires it.

For a different workload or model configuration:

```bash
python3 run_sim_pilot.py --taps 7 --block 5 --jobs 3 --opt O3 \
    --period-cycles 100000 --output results/local/tail_pilot.json
python3 run_energy_hypothesis.py --profile results/local/tail_pilot.json \
    --config configs/energy_model.json --output-dir results/local/tail_energy
```

The [model documentation](docs/research/ENERGY_MODEL.md) gives equations, units,
fit/evaluation separation and limitations. The [broader-study protocol](docs/research/BOUNDED_STUDY_PROTOCOL.md)
fixes the workload grid and continuation criterion. The original workload is a
replay control excluded from the 207 primary conditions.

For ordinary firmware builds and disassembly:

```bash
make
make OPT=-O3 N_TAPS=32 M_BLOCK=128 N_JOBS=4
make size
make disasm ELF=fir_unrolled.elf
```

## Evidence boundaries

The three kernels consume the same supplied input history. Their arithmetic
wraps modulo 2^32 and returns bits 15–30 as signed Q15, without saturation; see
[fir.h](fir.h). This differs from saturated library kernels and must not be used
as a universal CMSIS-DSP reference.

The pilot verifies compiled output-stream checksums against independent integer
convolution and records C1–C6/cycles for marked calls. Preparation, copying,
checksum and console output are outside each interval. Marker/call overhead is
included. Logical release periods and idle durations are projected metadata;
sleep and wake execution are not simulated.

The supply experiment reconstructs flat active power per job from published
event weights and inserts assumed wake/sleep demand. It is a bidirectional
averaged-buck model, not an identified STM32 internal LDO, package-inductance
model or SPICE transistor simulation. Reference energies and supply parameters
are synthetic; deterministic results do not provide measurement confidence
intervals. The proposed [physical protocol](docs/research/HYPOTHESIS_TEST_PROTOCOL.md)
remains unexecuted.

LeakSanitizer is disabled in the sanitizer fixture because the original sandbox
used ptrace; AddressSanitizer bounds checks and UBSan remain enabled.

## Historical workflow

[experiment_results.csv](experiment_results.csv), [rank_flip_analysis.csv](rank_flip_analysis.csv)
and [historical findings](docs/research/FINDINGS.md) predate the FIR correctness
fixes. Their reversals involved unequal computations, and the observed cycle-gap
margin is not a validated threshold.

The legacy scripts are retained for traceability. They use whole-program totals
and write the root CSVs; rerunning them on current firmware does not reproduce
the old experiment. `analyze_rankings.py` additionally requires pandas. Prefer
the checked runners above for new work.

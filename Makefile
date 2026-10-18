# ============================================================
# Makefile — Build and simulate Q15 FIR filter variants
#
# Usage:
#   make                         Build all three variants at -O2 (default)
#   make VARIANT=DIRECT OPT=-O3  Build one specific variant
#   make clean                   Remove generated ELF files
#   make install-deps            Install Python analysis dependencies
# ============================================================

include flags.mk
.DEFAULT_GOAL := all

# ── Configurable parameters (override on command line) ─────────────
OPT     ?= -O2
N_TAPS  ?= 16
M_BLOCK ?= 64

LDFLAGS  = -T stm32f051.ld -nostartfiles
SRCS     = startup.s main.c fir.c
PREFIX   = arm-none-eabi-

CC       = $(PREFIX)gcc
SIZE     = $(PREFIX)size
OBJDUMP  = $(PREFIX)objdump

# ── Derived targets ────────────────────────────────────────────────
ELF_DIRECT   = fir_direct.elf
ELF_CIRCULAR = fir_circular.elf
ELF_UNROLLED = fir_unrolled.elf

# Always rebuild the small firmware images: command-line dimensions/OPT are
# part of the experiment even when source timestamps have not changed.
.PHONY: all clean install-deps disasm size test pilot energy-model bounded-study $(ELF_DIRECT) $(ELF_CIRCULAR) $(ELF_UNROLLED)

test:
	python3 -m unittest discover -s tests -v

PILOT_OUTPUT ?= sim_pilot.json
N_JOBS ?= 4
pilot:
	python3 run_sim_pilot.py --jobs $(N_JOBS) --taps $(N_TAPS) --block $(M_BLOCK) \
	    --opt $(patsubst -%,%,$(OPT)) --output $(PILOT_OUTPUT)

MODEL_OUTPUT ?= results/energy_hypothesis
energy-model:
	python3 run_energy_hypothesis.py --output-dir $(MODEL_OUTPUT)

STUDY_OUTPUT ?= results/bounded_energy_study
STUDY_WORKERS ?= 2
bounded-study:
	python3 run_bounded_energy_study.py --output-dir $(STUDY_OUTPUT) --workers $(STUDY_WORKERS)

all: $(ELF_DIRECT) $(ELF_CIRCULAR) $(ELF_UNROLLED)
	@echo ""
	@$(SIZE) $^

$(ELF_DIRECT): $(SRCS) fir.h stm32f051.ld flags.mk
	$(CC) $(CFLAGS) $(OPT) -DVARIANT_DIRECT \
	      -DN_TAPS=$(N_TAPS) -DM_BLOCK=$(M_BLOCK) -DN_JOBS=$(N_JOBS) \
	      $(SRCS) $(LDFLAGS) -o $@

$(ELF_CIRCULAR): $(SRCS) fir.h stm32f051.ld flags.mk
	$(CC) $(CFLAGS) $(OPT) -DVARIANT_CIRCULAR \
	      -DN_TAPS=$(N_TAPS) -DM_BLOCK=$(M_BLOCK) -DN_JOBS=$(N_JOBS) \
	      $(SRCS) $(LDFLAGS) -o $@

$(ELF_UNROLLED): $(SRCS) fir.h stm32f051.ld flags.mk
	$(CC) $(CFLAGS) $(OPT) -DVARIANT_UNROLLED \
	      -DN_TAPS=$(N_TAPS) -DM_BLOCK=$(M_BLOCK) -DN_JOBS=$(N_JOBS) \
	      $(SRCS) $(LDFLAGS) -o $@

# Show disassembly of a chosen ELF (e.g.: make disasm ELF=fir_direct.elf)
ELF ?= fir_direct.elf
disasm:
	$(OBJDUMP) -d $(ELF) | less

# Show section sizes
size:
	$(SIZE) $(ELF_DIRECT) $(ELF_CIRCULAR) $(ELF_UNROLLED)

clean:
	rm -f *.elf *.o *.map

install-deps:
	pip3 install --user numpy scipy pandas matplotlib

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

.PHONY: all clean install-deps disasm size

all: $(ELF_DIRECT) $(ELF_CIRCULAR) $(ELF_UNROLLED)
	@echo ""
	@$(SIZE) $^

$(ELF_DIRECT): $(SRCS) fir.h stm32f051.ld flags.mk
	$(CC) $(CFLAGS) $(OPT) -DVARIANT_DIRECT \
	      -DN_TAPS=$(N_TAPS) -DM_BLOCK=$(M_BLOCK) \
	      $(SRCS) $(LDFLAGS) -o $@

$(ELF_CIRCULAR): $(SRCS) fir.h stm32f051.ld flags.mk
	$(CC) $(CFLAGS) $(OPT) -DVARIANT_CIRCULAR \
	      -DN_TAPS=$(N_TAPS) -DM_BLOCK=$(M_BLOCK) \
	      $(SRCS) $(LDFLAGS) -o $@

$(ELF_UNROLLED): $(SRCS) fir.h stm32f051.ld flags.mk
	$(CC) $(CFLAGS) $(OPT) -DVARIANT_UNROLLED \
	      -DN_TAPS=$(N_TAPS) -DM_BLOCK=$(M_BLOCK) \
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

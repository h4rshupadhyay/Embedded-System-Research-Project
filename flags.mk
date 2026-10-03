# ============================================================
# flags.mk — Mandatory compiler control flags
# Target: ARM Cortex-M0 (Armv6-M), bare-metal
# ============================================================

# Target Architecture: ARM Cortex-M0 (Armv6-M)
CPU_FLAGS = -mcpu=cortex-m0 -mthumb -mfloat-abi=soft

# Determinism & Alignment Controls
# -fno-builtin        : Prevents GCC from auto-substituting loops with libc
#                       calls (e.g. memcpy, memset), keeping code structure intact
# -falign-loops=4     : Enforces 32-bit Flash word alignment for loops,
#                       eliminating alignment noise across word boundaries
# -falign-functions=4 : Enforces 32-bit Flash word alignment for functions
EXTRA_FLAGS = -fno-builtin -falign-loops=4 -falign-functions=4 -Wall -Wextra

CFLAGS = $(CPU_FLAGS) $(EXTRA_FLAGS)

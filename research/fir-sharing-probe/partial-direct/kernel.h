#ifndef PARTIAL_DIRECT_KERNEL_H
#define PARTIAL_DIRECT_KERNEL_H

#include <stdint.h>

#ifndef BLOCK
#error "Compile with BLOCK=1 or BLOCK=64"
#endif
#if BLOCK != 1 && BLOCK != 64
#error "BLOCK must be 1 or 64"
#endif

#define TAPS 48
typedef struct { int16_t history[TAPS + BLOCK]; } ProbeState;

void probe_init(ProbeState *state);
void probe_process(ProbeState *state, const int16_t *input,
                   int16_t *output, uint32_t block_size);
int64_t probe_get_state(ProbeState *state, uint32_t index);
unsigned probe_state_bytes(void);

#endif

#include <stdint.h>
#define TAPS 48
typedef struct { int16_t history[49]; } ProbeState;
void probe_init(ProbeState *);
void probe_process(ProbeState * restrict,const int16_t * restrict,int16_t * restrict,uint32_t);
int64_t probe_get_state(ProbeState *,uint32_t);
unsigned probe_state_bytes(void);

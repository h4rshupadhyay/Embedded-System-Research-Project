#include <stdint.h>
#include "dsp/filtering_functions.h"
#define TAPS 48
typedef struct {
int16_t history[112];
arm_fir_instance_q15 instance;
} ProbeState;
void probe_init(ProbeState *);
void probe_process(ProbeState *,const int16_t *,int16_t *,uint32_t);
int64_t probe_get_state(ProbeState *,uint32_t);
unsigned probe_state_bytes(void);

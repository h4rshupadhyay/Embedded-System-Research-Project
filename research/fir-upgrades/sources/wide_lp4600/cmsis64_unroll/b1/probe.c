#include "probe.h"
#include "kernels.h"
void probe_init(ProbeState *s) {
for(unsigned i=0;i<sizeof(*s);++i) ((unsigned char *)s)[i]=0;
s->instance.numTaps=TAPS; s->instance.pState=s->history;
static const int16_t reversed[TAPS]={16,-25,2,35,-36,-21,73,-28,-87,105,49,-184,58,216,-221,-149,390,-45,-484,352,413,-695,-120,946,-388,-963,1016,635,-1595,67,1923,-1069,-1822,2209,1190,-3289,-24,4157,-1617,-4822,3693,5685,-6318,-8469,9322,23073,17073,4834};
s->instance.pCoeffs=reversed;
}
unsigned probe_state_bytes(void) {return sizeof(ProbeState);}
int64_t probe_get_state(ProbeState *s,uint32_t i) {
return s->history[i];
}
void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b) {
arm_fir_q15(&s->instance,x,y,b);
}

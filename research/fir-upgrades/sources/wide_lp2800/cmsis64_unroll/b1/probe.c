#include "probe.h"
#include "kernels.h"
void probe_init(ProbeState *s) {
for(unsigned i=0;i<sizeof(*s);++i) ((unsigned char *)s)[i]=0;
s->instance.numTaps=TAPS; s->instance.pState=s->history;
static const int16_t reversed[TAPS]={-88,-112,21,162,113,-108,-239,-77,229,302,-5,-373,-340,135,535,340,-317,-703,-293,550,871,190,-838,-1035,-24,1188,1194,-216,-1615,-1359,539,2155,1563,-958,-2881,-1902,1467,3978,2673,-1965,-5924,-4984,1523,9954,15246,14755,9828,4135};
s->instance.pCoeffs=reversed;
}
unsigned probe_state_bytes(void) {return sizeof(ProbeState);}
int64_t probe_get_state(ProbeState *s,uint32_t i) {
return s->history[i];
}
void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b) {
arm_fir_q15(&s->instance,x,y,b);
}

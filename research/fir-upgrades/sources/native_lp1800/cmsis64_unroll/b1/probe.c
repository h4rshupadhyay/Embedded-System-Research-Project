#include "probe.h"
#include "kernels.h"
void probe_init(ProbeState *s) {
for(unsigned i=0;i<sizeof(*s);++i) ((unsigned char *)s)[i]=0;
s->instance.numTaps=TAPS; s->instance.pState=s->history;
static const int16_t reversed[TAPS]={-13,-66,-86,-52,27,108,140,90,-29,-156,-218,-161,2,197,317,278,76,-206,-424,-448,-231,148,512,665,491,28,-528,-905,-878,-394,377,1099,1403,1068,139,-1054,-2011,-2254,-1530,76,2160,4145,5493,5890,5336,4107,2630,1355};
s->instance.pCoeffs=reversed;
}
unsigned probe_state_bytes(void) {return sizeof(ProbeState);}
int64_t probe_get_state(ProbeState *s,uint32_t i) {
return s->history[i];
}
void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b) {
arm_fir_q15(&s->instance,x,y,b);
}

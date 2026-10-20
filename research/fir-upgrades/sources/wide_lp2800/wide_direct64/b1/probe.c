#include "probe.h"
void probe_init(ProbeState *s){for(unsigned i=0;i<sizeof(*s);++i)((unsigned char*)s)[i]=0;}
unsigned probe_state_bytes(void){return sizeof(ProbeState);}
int64_t probe_get_state(ProbeState*s,uint32_t i){return s->history[i];}
static int16_t quant(int64_t s){if(s>=1073741824LL)return 32767;if(s<=-1073741824LL)return -32768;int32_t q=(int32_t)s;return (int16_t)(q>=0?q/32768:-1-(-(q+1))/32768);}
void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b){
for(uint32_t j=0;j<b;++j)s->history[47+j]=x[j];
for(uint32_t j=0;j<b;++j){
int64_t sum=0;
sum+=(int32_t)(4135)*s->history[j+47];
sum+=(int32_t)(9828)*s->history[j+46];
sum+=(int32_t)(14755)*s->history[j+45];
sum+=(int32_t)(15246)*s->history[j+44];
sum+=(int32_t)(9954)*s->history[j+43];
sum+=(int32_t)(1523)*s->history[j+42];
sum+=(int32_t)(-4984)*s->history[j+41];
sum+=(int32_t)(-5924)*s->history[j+40];
sum+=(int32_t)(-1965)*s->history[j+39];
sum+=(int32_t)(2673)*s->history[j+38];
sum+=(int32_t)(3978)*s->history[j+37];
sum+=(int32_t)(1467)*s->history[j+36];
sum+=(int32_t)(-1902)*s->history[j+35];
sum+=(int32_t)(-2881)*s->history[j+34];
sum+=(int32_t)(-958)*s->history[j+33];
sum+=(int32_t)(1563)*s->history[j+32];
sum+=(int32_t)(2155)*s->history[j+31];
sum+=(int32_t)(539)*s->history[j+30];
sum+=(int32_t)(-1359)*s->history[j+29];
sum+=(int32_t)(-1615)*s->history[j+28];
sum+=(int32_t)(-216)*s->history[j+27];
sum+=(int32_t)(1194)*s->history[j+26];
sum+=(int32_t)(1188)*s->history[j+25];
sum+=(int32_t)(-24)*s->history[j+24];
sum+=(int32_t)(-1035)*s->history[j+23];
sum+=(int32_t)(-838)*s->history[j+22];
sum+=(int32_t)(190)*s->history[j+21];
sum+=(int32_t)(871)*s->history[j+20];
sum+=(int32_t)(550)*s->history[j+19];
sum+=(int32_t)(-293)*s->history[j+18];
sum+=(int32_t)(-703)*s->history[j+17];
sum+=(int32_t)(-317)*s->history[j+16];
sum+=(int32_t)(340)*s->history[j+15];
sum+=(int32_t)(535)*s->history[j+14];
sum+=(int32_t)(135)*s->history[j+13];
sum+=(int32_t)(-340)*s->history[j+12];
sum+=(int32_t)(-373)*s->history[j+11];
sum+=(int32_t)(-5)*s->history[j+10];
sum+=(int32_t)(302)*s->history[j+9];
sum+=(int32_t)(229)*s->history[j+8];
sum+=(int32_t)(-77)*s->history[j+7];
sum+=(int32_t)(-239)*s->history[j+6];
sum+=(int32_t)(-108)*s->history[j+5];
sum+=(int32_t)(113)*s->history[j+4];
sum+=(int32_t)(162)*s->history[j+3];
sum+=(int32_t)(21)*s->history[j+2];
sum+=(int32_t)(-112)*s->history[j+1];
sum+=(int32_t)(-88)*s->history[j+0];
y[j]=quant(sum);}
for(uint32_t j=0;j<47;++j)s->history[j]=s->history[b+j];
}

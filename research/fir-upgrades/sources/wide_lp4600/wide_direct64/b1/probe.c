#include "probe.h"
void probe_init(ProbeState *s){for(unsigned i=0;i<sizeof(*s);++i)((unsigned char*)s)[i]=0;}
unsigned probe_state_bytes(void){return sizeof(ProbeState);}
int64_t probe_get_state(ProbeState*s,uint32_t i){return s->history[i];}
static int16_t quant(int64_t s){if(s>=1073741824LL)return 32767;if(s<=-1073741824LL)return -32768;int32_t q=(int32_t)s;return (int16_t)(q>=0?q/32768:-1-(-(q+1))/32768);}
void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b){
for(uint32_t j=0;j<b;++j)s->history[47+j]=x[j];
for(uint32_t j=0;j<b;++j){
int64_t sum=0;
sum+=(int32_t)(4834)*s->history[j+47];
sum+=(int32_t)(17073)*s->history[j+46];
sum+=(int32_t)(23073)*s->history[j+45];
sum+=(int32_t)(9322)*s->history[j+44];
sum+=(int32_t)(-8469)*s->history[j+43];
sum+=(int32_t)(-6318)*s->history[j+42];
sum+=(int32_t)(5685)*s->history[j+41];
sum+=(int32_t)(3693)*s->history[j+40];
sum+=(int32_t)(-4822)*s->history[j+39];
sum+=(int32_t)(-1617)*s->history[j+38];
sum+=(int32_t)(4157)*s->history[j+37];
sum+=(int32_t)(-24)*s->history[j+36];
sum+=(int32_t)(-3289)*s->history[j+35];
sum+=(int32_t)(1190)*s->history[j+34];
sum+=(int32_t)(2209)*s->history[j+33];
sum+=(int32_t)(-1822)*s->history[j+32];
sum+=(int32_t)(-1069)*s->history[j+31];
sum+=(int32_t)(1923)*s->history[j+30];
sum+=(int32_t)(67)*s->history[j+29];
sum+=(int32_t)(-1595)*s->history[j+28];
sum+=(int32_t)(635)*s->history[j+27];
sum+=(int32_t)(1016)*s->history[j+26];
sum+=(int32_t)(-963)*s->history[j+25];
sum+=(int32_t)(-388)*s->history[j+24];
sum+=(int32_t)(946)*s->history[j+23];
sum+=(int32_t)(-120)*s->history[j+22];
sum+=(int32_t)(-695)*s->history[j+21];
sum+=(int32_t)(413)*s->history[j+20];
sum+=(int32_t)(352)*s->history[j+19];
sum+=(int32_t)(-484)*s->history[j+18];
sum+=(int32_t)(-45)*s->history[j+17];
sum+=(int32_t)(390)*s->history[j+16];
sum+=(int32_t)(-149)*s->history[j+15];
sum+=(int32_t)(-221)*s->history[j+14];
sum+=(int32_t)(216)*s->history[j+13];
sum+=(int32_t)(58)*s->history[j+12];
sum+=(int32_t)(-184)*s->history[j+11];
sum+=(int32_t)(49)*s->history[j+10];
sum+=(int32_t)(105)*s->history[j+9];
sum+=(int32_t)(-87)*s->history[j+8];
sum+=(int32_t)(-28)*s->history[j+7];
sum+=(int32_t)(73)*s->history[j+6];
sum+=(int32_t)(-21)*s->history[j+5];
sum+=(int32_t)(-36)*s->history[j+4];
sum+=(int32_t)(35)*s->history[j+3];
sum+=(int32_t)(2)*s->history[j+2];
sum+=(int32_t)(-25)*s->history[j+1];
sum+=(int32_t)(16)*s->history[j+0];
y[j]=quant(sum);}
for(uint32_t j=0;j<47;++j)s->history[j]=s->history[b+j];
}

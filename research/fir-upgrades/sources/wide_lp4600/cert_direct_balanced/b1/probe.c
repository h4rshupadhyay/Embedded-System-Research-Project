#include "probe.h"
void probe_init(ProbeState *s){for(unsigned i=0;i<sizeof(*s);++i)((unsigned char*)s)[i]=0;}
unsigned probe_state_bytes(void){return sizeof(ProbeState);}
int64_t probe_get_state(ProbeState*s,uint32_t i){return s->history[i];}
static int16_t quant(int64_t s){if(s>=1073741824LL)return 32767;if(s<=-1073741824LL)return -32768;int32_t q=(int32_t)s;return (int16_t)(q>=0?q/32768:-1-(-(q+1))/32768);}
void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b){
for(uint32_t j=0;j<b;++j)s->history[47+j]=x[j];
for(uint32_t j=0;j<b;++j){
int32_t partial0=0;
partial0+=(int32_t)(4834)*s->history[j+47];
partial0+=(int32_t)(17073)*s->history[j+46];
partial0+=(int32_t)(23073)*s->history[j+45];
partial0+=(int32_t)(9322)*s->history[j+44];
int32_t partial1=0;
partial1+=(int32_t)(-8469)*s->history[j+43];
partial1+=(int32_t)(-6318)*s->history[j+42];
partial1+=(int32_t)(5685)*s->history[j+41];
partial1+=(int32_t)(3693)*s->history[j+40];
partial1+=(int32_t)(-4822)*s->history[j+39];
partial1+=(int32_t)(-1617)*s->history[j+38];
partial1+=(int32_t)(4157)*s->history[j+37];
partial1+=(int32_t)(-24)*s->history[j+36];
partial1+=(int32_t)(-3289)*s->history[j+35];
partial1+=(int32_t)(1190)*s->history[j+34];
partial1+=(int32_t)(2209)*s->history[j+33];
partial1+=(int32_t)(-1822)*s->history[j+32];
partial1+=(int32_t)(-1069)*s->history[j+31];
partial1+=(int32_t)(1923)*s->history[j+30];
partial1+=(int32_t)(67)*s->history[j+29];
partial1+=(int32_t)(-1595)*s->history[j+28];
partial1+=(int32_t)(635)*s->history[j+27];
partial1+=(int32_t)(1016)*s->history[j+26];
partial1+=(int32_t)(-963)*s->history[j+25];
partial1+=(int32_t)(-388)*s->history[j+24];
partial1+=(int32_t)(946)*s->history[j+23];
partial1+=(int32_t)(-120)*s->history[j+22];
partial1+=(int32_t)(-695)*s->history[j+21];
partial1+=(int32_t)(413)*s->history[j+20];
partial1+=(int32_t)(352)*s->history[j+19];
partial1+=(int32_t)(-484)*s->history[j+18];
partial1+=(int32_t)(-45)*s->history[j+17];
partial1+=(int32_t)(390)*s->history[j+16];
partial1+=(int32_t)(-149)*s->history[j+15];
partial1+=(int32_t)(-221)*s->history[j+14];
partial1+=(int32_t)(216)*s->history[j+13];
partial1+=(int32_t)(58)*s->history[j+12];
partial1+=(int32_t)(-184)*s->history[j+11];
partial1+=(int32_t)(49)*s->history[j+10];
partial1+=(int32_t)(105)*s->history[j+9];
partial1+=(int32_t)(-87)*s->history[j+8];
partial1+=(int32_t)(-28)*s->history[j+7];
partial1+=(int32_t)(73)*s->history[j+6];
partial1+=(int32_t)(-21)*s->history[j+5];
partial1+=(int32_t)(-36)*s->history[j+4];
partial1+=(int32_t)(35)*s->history[j+3];
partial1+=(int32_t)(2)*s->history[j+2];
partial1+=(int32_t)(-25)*s->history[j+1];
partial1+=(int32_t)(16)*s->history[j+0];
int64_t sum=(int64_t)partial0+(int64_t)partial1;
y[j]=quant(sum);}
for(uint32_t j=0;j<47;++j)s->history[j]=s->history[b+j];
}

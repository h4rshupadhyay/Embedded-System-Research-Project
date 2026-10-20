#include "probe.h"
void probe_init(ProbeState *s){for(unsigned i=0;i<sizeof(*s);++i)((unsigned char*)s)[i]=0;}
unsigned probe_state_bytes(void){return sizeof(ProbeState);}
int64_t probe_get_state(ProbeState*s,uint32_t i){return s->history[i];}
static int16_t quant(int64_t s){if(s>=1073741824LL)return 32767;if(s<=-1073741824LL)return -32768;int32_t q=(int32_t)s;return (int16_t)(q>=0?q/32768:-1-(-(q+1))/32768);}
void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b){
for(uint32_t j=0;j<b;++j)s->history[47+j]=x[j];
for(uint32_t j=0;j<b;++j){
int64_t sum=0;
sum+=(int32_t)(1355)*s->history[j+47];
sum+=(int32_t)(2630)*s->history[j+46];
sum+=(int32_t)(4107)*s->history[j+45];
sum+=(int32_t)(5336)*s->history[j+44];
sum+=(int32_t)(5890)*s->history[j+43];
sum+=(int32_t)(5493)*s->history[j+42];
sum+=(int32_t)(4145)*s->history[j+41];
sum+=(int32_t)(2160)*s->history[j+40];
sum+=(int32_t)(76)*s->history[j+39];
sum+=(int32_t)(-1530)*s->history[j+38];
sum+=(int32_t)(-2254)*s->history[j+37];
sum+=(int32_t)(-2011)*s->history[j+36];
sum+=(int32_t)(-1054)*s->history[j+35];
sum+=(int32_t)(139)*s->history[j+34];
sum+=(int32_t)(1068)*s->history[j+33];
sum+=(int32_t)(1403)*s->history[j+32];
sum+=(int32_t)(1099)*s->history[j+31];
sum+=(int32_t)(377)*s->history[j+30];
sum+=(int32_t)(-394)*s->history[j+29];
sum+=(int32_t)(-878)*s->history[j+28];
sum+=(int32_t)(-905)*s->history[j+27];
sum+=(int32_t)(-528)*s->history[j+26];
sum+=(int32_t)(28)*s->history[j+25];
sum+=(int32_t)(491)*s->history[j+24];
sum+=(int32_t)(665)*s->history[j+23];
sum+=(int32_t)(512)*s->history[j+22];
sum+=(int32_t)(148)*s->history[j+21];
sum+=(int32_t)(-231)*s->history[j+20];
sum+=(int32_t)(-448)*s->history[j+19];
sum+=(int32_t)(-424)*s->history[j+18];
sum+=(int32_t)(-206)*s->history[j+17];
sum+=(int32_t)(76)*s->history[j+16];
sum+=(int32_t)(278)*s->history[j+15];
sum+=(int32_t)(317)*s->history[j+14];
sum+=(int32_t)(197)*s->history[j+13];
sum+=(int32_t)(2)*s->history[j+12];
sum+=(int32_t)(-161)*s->history[j+11];
sum+=(int32_t)(-218)*s->history[j+10];
sum+=(int32_t)(-156)*s->history[j+9];
sum+=(int32_t)(-29)*s->history[j+8];
sum+=(int32_t)(90)*s->history[j+7];
sum+=(int32_t)(140)*s->history[j+6];
sum+=(int32_t)(108)*s->history[j+5];
sum+=(int32_t)(27)*s->history[j+4];
sum+=(int32_t)(-52)*s->history[j+3];
sum+=(int32_t)(-86)*s->history[j+2];
sum+=(int32_t)(-66)*s->history[j+1];
sum+=(int32_t)(-13)*s->history[j+0];
y[j]=quant(sum);}
for(uint32_t j=0;j<47;++j)s->history[j]=s->history[b+j];
}

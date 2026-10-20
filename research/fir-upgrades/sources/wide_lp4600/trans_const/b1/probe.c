#include "probe.h"
#include "kernels.h"
void probe_init(ProbeState *s) {
for(unsigned i=0;i<sizeof(*s);++i) ((unsigned char *)s)[i]=0;
}
unsigned probe_state_bytes(void) {return sizeof(ProbeState);}
int64_t probe_get_state(ProbeState *s,uint32_t i) {
switch(i) {
case 0:return s->z0;
case 1:return s->z1;
case 2:return s->z2;
case 3:return s->z3;
case 4:return s->z4;
case 5:return s->z5;
case 6:return s->z6;
case 7:return s->z7;
case 8:return s->z8;
case 9:return s->z9;
case 10:return s->z10;
case 11:return s->z11;
case 12:return s->z12;
case 13:return s->z13;
case 14:return s->z14;
case 15:return s->z15;
case 16:return s->z16;
case 17:return s->z17;
case 18:return s->z18;
case 19:return s->z19;
case 20:return s->z20;
case 21:return s->z21;
case 22:return s->z22;
case 23:return s->z23;
case 24:return s->z24;
case 25:return s->z25;
case 26:return s->z26;
case 27:return s->z27;
case 28:return s->z28;
case 29:return s->z29;
case 30:return s->z30;
case 31:return s->z31;
case 32:return s->z32;
case 33:return s->z33;
case 34:return s->z34;
case 35:return s->z35;
case 36:return s->z36;
case 37:return s->z37;
case 38:return s->z38;
case 39:return s->z39;
case 40:return s->z40;
case 41:return s->z41;
case 42:return s->z42;
case 43:return s->z43;
case 44:return s->z44;
case 45:return s->z45;
case 46:return s->z46;
default:return 0;}
}

static int16_t quant(int64_t s) {
    if (s >= 1073741824LL) return 32767;
    if (s <= -1073741824LL) return -32768;
    int32_t q=(int32_t)s;
    return (int16_t)(q>=0 ? q/32768 : -1-(-(q+1))/32768);
}

void probe_process(ProbeState * restrict s,const int16_t * restrict x,int16_t * restrict y,uint32_t b) {
for(uint32_t j=0;j<b;++j) {
int32_t t0=x[j];
int64_t out=(int64_t)((int32_t)(4834)*t0)+s->z0;
y[j]=quant(out);
s->z0=(int64_t)((int32_t)(17073)*t0)+s->z1;
s->z1=(int64_t)((int32_t)(23073)*t0)+s->z2;
s->z2=(int32_t)((int32_t)(9322)*t0)+s->z3;
s->z3=(int32_t)((int32_t)(-8469)*t0)+s->z4;
s->z4=(int32_t)((int32_t)(-6318)*t0)+s->z5;
s->z5=(int32_t)((int32_t)(5685)*t0)+s->z6;
s->z6=(int32_t)((int32_t)(3693)*t0)+s->z7;
s->z7=(int32_t)((int32_t)(-4822)*t0)+s->z8;
s->z8=(int32_t)((int32_t)(-1617)*t0)+s->z9;
s->z9=(int32_t)((int32_t)(4157)*t0)+s->z10;
s->z10=(int32_t)((int32_t)(-24)*t0)+s->z11;
s->z11=(int32_t)((int32_t)(-3289)*t0)+s->z12;
s->z12=(int32_t)((int32_t)(1190)*t0)+s->z13;
s->z13=(int32_t)((int32_t)(2209)*t0)+s->z14;
s->z14=(int32_t)((int32_t)(-1822)*t0)+s->z15;
s->z15=(int32_t)((int32_t)(-1069)*t0)+s->z16;
s->z16=(int32_t)((int32_t)(1923)*t0)+s->z17;
s->z17=(int32_t)((int32_t)(67)*t0)+s->z18;
s->z18=(int32_t)((int32_t)(-1595)*t0)+s->z19;
s->z19=(int32_t)((int32_t)(635)*t0)+s->z20;
s->z20=(int32_t)((int32_t)(1016)*t0)+s->z21;
s->z21=(int32_t)((int32_t)(-963)*t0)+s->z22;
s->z22=(int32_t)((int32_t)(-388)*t0)+s->z23;
s->z23=(int32_t)((int32_t)(946)*t0)+s->z24;
s->z24=(int32_t)((int32_t)(-120)*t0)+s->z25;
s->z25=(int32_t)((int32_t)(-695)*t0)+s->z26;
s->z26=(int32_t)((int32_t)(413)*t0)+s->z27;
s->z27=(int32_t)((int32_t)(352)*t0)+s->z28;
s->z28=(int32_t)((int32_t)(-484)*t0)+s->z29;
s->z29=(int32_t)((int32_t)(-45)*t0)+s->z30;
s->z30=(int32_t)((int32_t)(390)*t0)+s->z31;
s->z31=(int32_t)((int32_t)(-149)*t0)+s->z32;
s->z32=(int32_t)((int32_t)(-221)*t0)+s->z33;
s->z33=(int32_t)((int32_t)(216)*t0)+s->z34;
s->z34=(int32_t)((int32_t)(58)*t0)+s->z35;
s->z35=(int32_t)((int32_t)(-184)*t0)+s->z36;
s->z36=(int32_t)((int32_t)(49)*t0)+s->z37;
s->z37=(int32_t)((int32_t)(105)*t0)+s->z38;
s->z38=(int32_t)((int32_t)(-87)*t0)+s->z39;
s->z39=(int32_t)((int32_t)(-28)*t0)+s->z40;
s->z40=(int32_t)((int32_t)(73)*t0)+s->z41;
s->z41=(int32_t)((int32_t)(-21)*t0)+s->z42;
s->z42=(int32_t)((int32_t)(-36)*t0)+s->z43;
s->z43=(int32_t)((int32_t)(35)*t0)+s->z44;
s->z44=(int32_t)((int32_t)(2)*t0)+s->z45;
s->z45=(int32_t)((int32_t)(-25)*t0)+s->z46;
s->z46=(int32_t)((int32_t)(16)*t0);
}
}

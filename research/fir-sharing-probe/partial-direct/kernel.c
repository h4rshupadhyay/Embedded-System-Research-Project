#include "kernel.h"

/* The fixed coefficients are literal values from selection-design.json.
 * L1(0:2)=12778 and L1(2:48)=59731. Multiplying either by 32768 bounds
 * every partial prefix (and every product) below INT32_MAX. */

void probe_init(ProbeState *s) {
    for (unsigned i = 0; i < sizeof(*s); ++i)
        ((unsigned char *)s)[i] = 0;
}

unsigned probe_state_bytes(void) { return sizeof(ProbeState); }

int64_t probe_get_state(ProbeState *s, uint32_t i) {
    return s->history[i];
}

static int16_t quant(int64_t sum) {
    if (sum >= 1073741824LL) return 32767;
    if (sum <= -1073741824LL) return -32768;
    /* Here conversion is in range. This expression implements floor for
     * negative C operands without assuming arithmetic right shift. */
    int32_t q = (int32_t)sum;
    return (int16_t)(q >= 0 ? q / 32768 : -1 - (-(q + 1)) / 32768);
}

void probe_process(ProbeState * restrict s, const int16_t * restrict x,
                   int16_t * restrict y, uint32_t b) {
    for (uint32_t j = 0; j < b; ++j) s->history[TAPS - 1 + j] = x[j];
    for (uint32_t j = 0; j < b; ++j) {
        int32_t partial0 = 0;
        int32_t partial1 = 0;
        partial0 += (int32_t)(3526) * s->history[j+47];
        partial0 += (int32_t)(9252) * s->history[j+46];
        partial1 += (int32_t)(12990) * s->history[j+45];
        partial1 += (int32_t)(10395) * s->history[j+44];
        partial1 += (int32_t)(2471) * s->history[j+43];
        partial1 += (int32_t)(-4294) * s->history[j+42];
        partial1 += (int32_t)(-4508) * s->history[j+41];
        partial1 += (int32_t)(200) * s->history[j+40];
        partial1 += (int32_t)(3429) * s->history[j+39];
        partial1 += (int32_t)(1761) * s->history[j+38];
        partial1 += (int32_t)(-1730) * s->history[j+37];
        partial1 += (int32_t)(-2295) * s->history[j+36];
        partial1 += (int32_t)(242) * s->history[j+35];
        partial1 += (int32_t)(1994) * s->history[j+34];
        partial1 += (int32_t)(759) * s->history[j+33];
        partial1 += (int32_t)(-1299) * s->history[j+32];
        partial1 += (int32_t)(-1240) * s->history[j+31];
        partial1 += (int32_t)(524) * s->history[j+30];
        partial1 += (int32_t)(1284) * s->history[j+29];
        partial1 += (int32_t)(131) * s->history[j+28];
        partial1 += (int32_t)(-1033) * s->history[j+27];
        partial1 += (int32_t)(-565) * s->history[j+26];
        partial1 += (int32_t)(635) * s->history[j+25];
        partial1 += (int32_t)(755) * s->history[j+24];
        partial1 += (int32_t)(-219) * s->history[j+23];
        partial1 += (int32_t)(-737) * s->history[j+22];
        partial1 += (int32_t)(-122) * s->history[j+21];
        partial1 += (int32_t)(578) * s->history[j+20];
        partial1 += (int32_t)(341) * s->history[j+19];
        partial1 += (int32_t)(-352) * s->history[j+18];
        partial1 += (int32_t)(-431) * s->history[j+17];
        partial1 += (int32_t)(127) * s->history[j+16];
        partial1 += (int32_t)(413) * s->history[j+15];
        partial1 += (int32_t)(53) * s->history[j+14];
        partial1 += (int32_t)(-326) * s->history[j+13];
        partial1 += (int32_t)(-166) * s->history[j+12];
        partial1 += (int32_t)(209) * s->history[j+11];
        partial1 += (int32_t)(212) * s->history[j+10];
        partial1 += (int32_t)(-97) * s->history[j+9];
        partial1 += (int32_t)(-207) * s->history[j+8];
        partial1 += (int32_t)(10) * s->history[j+7];
        partial1 += (int32_t)(170) * s->history[j+6];
        partial1 += (int32_t)(45) * s->history[j+5];
        partial1 += (int32_t)(-121) * s->history[j+4];
        partial1 += (int32_t)(-71) * s->history[j+3];
        partial1 += (int32_t)(75) * s->history[j+2];
        partial1 += (int32_t)(76) * s->history[j+1];
        partial1 += (int32_t)(-39) * s->history[j+0];
        int64_t exact_sum = (int64_t)partial0 + (int64_t)partial1;
        y[j] = quant(exact_sum);
    }
    for (uint32_t j = 0; j < TAPS - 1; ++j)
        s->history[j] = s->history[b + j];
}

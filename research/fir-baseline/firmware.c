/* Bare-metal research fixture. Only process_stream is inside the marked region. */
#include "kernels.h"
#include "case_data.h"
static int16_t state[TAPS-1+BLOCK];
static int16_t source[SAMPLES];
static int16_t output[SAMPLES];
extern void measured(void);

void process_stream(void)
{
    for (uint32_t offset=0; offset<SAMPLES; offset+=BLOCK) {
        uint32_t size=SAMPLES-offset;
        if (size>BLOCK) size=BLOCK;
        KERNEL(state, coefficients, source+offset, output+offset, TAPS, size);
    }
}

static void put(char c)
{
    *(volatile uint32_t *)0xe0000000=(uint32_t)c;
}

static void hex16(int16_t value)
{
    uint32_t v=(uint16_t)value;
    for (int shift=12; shift>=0; shift-=4) {
        uint32_t digit=(v>>shift)&15;
        put((char)(digit<10 ? '0'+digit : 'a'+digit-10));
    }
}

int main(void)
{
    /* Input-buffer preparation is fixture setup; all per-call state work is measured. */
    for (uint32_t i=0; i<SAMPLES; ++i) source[i]=input_data[i];
    measured();
    put('O'); put(':');
    for (uint32_t i=0; i<SAMPLES; ++i) hex16(output[i]);
    put('\n'); put('H'); put(':');
    for (uint32_t i=0; i<TAPS-1; ++i) hex16(state[i]);
    put('\n');
    return 0;
}

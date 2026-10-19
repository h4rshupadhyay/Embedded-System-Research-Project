/* Held-out experiment fixture; preparation and canary checks are outside ROI. */
#include <stdint.h>
#if defined(CMSIS_KERNEL)
#include "dsp/filtering_functions.h"
#else
#include "kernels.h"
#endif
#include "case_data.h"

/* Extra CMSIS state slot plus two guard halfwords on both sides. */
static int16_t storage[TAPS+BLOCK+4] __attribute__((aligned(4)));
static int16_t source[SAMPLES];
static int16_t destination[SAMPLES+4] __attribute__((aligned(4)));
#define state (storage+2)
#define output (destination+2)
#if defined(CMSIS_KERNEL)
static arm_fir_instance_q15 instance;
#endif
extern void measured(void);

void process_stream(void)
{
    for (uint32_t offset=0; offset<SAMPLES; offset+=BLOCK) {
        uint32_t size=SAMPLES-offset;
        if (size>BLOCK) size=BLOCK;
#if defined(CMSIS_KERNEL)
        CMSIS_KERNEL(&instance, source+offset, output+offset, size);
#else
        KERNEL(state, coefficients, source+offset, output+offset, TAPS, size);
#endif
    }
}

static void put(char c) { *(volatile uint32_t *)0xe0000000=(uint32_t)c; }
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
    for (uint32_t i=0; i<SAMPLES; ++i) source[i]=input_data[i];
    storage[0]=storage[1]=storage[TAPS+BLOCK+2]=storage[TAPS+BLOCK+3]=23130;
    destination[0]=destination[1]=destination[SAMPLES+2]=destination[SAMPLES+3]=23130;
#if defined(CMSIS_KERNEL)
    instance.numTaps=TAPS;
    instance.pState=state;
    instance.pCoeffs=cmsis_coefficients;
#endif
    measured();
    put('O'); put(':');
    for (uint32_t i=0; i<SAMPLES; ++i) hex16(output[i]);
    put('\n'); put('H'); put(':');
    for (uint32_t i=0; i<TAPS-1; ++i) hex16(state[i]);
    put('\n'); put('G'); put(':');
    hex16(storage[0]); hex16(storage[1]);
    hex16(storage[TAPS+BLOCK+2]); hex16(storage[TAPS+BLOCK+3]);
    hex16(destination[0]); hex16(destination[1]);
    hex16(destination[SAMPLES+2]); hex16(destination[SAMPLES+3]);
    put('\n');
    return 0;
}

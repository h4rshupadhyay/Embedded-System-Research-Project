/* Pinned CMSIS-DSP fixture, matching generic firmware's measurement boundary.
 * This bank is symmetric, so h in lag order equals CMSIS's reversed order. */
#include "dsp/filtering_functions.h"
#include "case_data.h"
static q15_t state[TAPS-1+BLOCK];
static q15_t source[SAMPLES];
static q15_t output[SAMPLES];
static arm_fir_instance_q15 instance;
extern void measured(void);

void process_stream(void)
{
    for (uint32_t offset=0; offset<SAMPLES; offset+=BLOCK) {
        uint32_t size=SAMPLES-offset;
        if (size>BLOCK) size=BLOCK;
        CMSIS_KERNEL(&instance, source+offset, output+offset, size);
    }
}

static void put(char c) { *(volatile uint32_t *)0xe0000000=(uint32_t)c; }
static void hex16(q15_t value)
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
    instance.numTaps=TAPS;
    instance.pState=state;
    instance.pCoeffs=coefficients;
    measured();
    put('O'); put(':');
    for (uint32_t i=0; i<SAMPLES; ++i) hex16(output[i]);
    put('\n'); put('H'); put(':');
    for (uint32_t i=0; i<TAPS-1; ++i) hex16(state[i]);
    put('\n');
    return 0;
}

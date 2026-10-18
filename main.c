#include "fir.h"

/* ====================================================================
 * main.c — Bare-metal testbench for Q15 FIR filter variants.
 *
 * Workload dimensions are injected at compile time:
 *   -DN_TAPS=<n>   : number of filter taps  (default: 16)
 *   -DM_BLOCK=<m>  : number of output samples (default: 64)
 *
 * Active variant is selected by exactly one of:
 *   -DVARIANT_DIRECT
 *   -DVARIANT_CIRCULAR
 *   -DVARIANT_UNROLLED
 * ==================================================================== */

#ifndef N_TAPS
#define N_TAPS 16
#endif

#ifndef M_BLOCK
#define M_BLOCK 64
#endif

#ifndef N_JOBS
#define N_JOBS 1
#endif

#if N_TAPS < 1 || N_TAPS > 65535 || M_BLOCK < 1 || M_BLOCK > 65535 || N_JOBS < 1
#error "Positive dimensions are required; taps and block must fit uint16_t"
#endif

#if (defined(VARIANT_DIRECT) + defined(VARIANT_CIRCULAR) + defined(VARIANT_UNROLLED)) != 1
#error "Select exactly one FIR variant"
#endif

/* ------------------------------------------------------------------ */
/* Static buffers in SRAM (.bss / .data)                               */
/* input_signal has N_TAPS guard samples prepended so that pointer     */
/* arithmetic in circular and unrolled variants stays in bounds.       */
/* ------------------------------------------------------------------ */
q15_t input_signal[M_BLOCK + N_TAPS];   /* length = M + N              */
q15_t filter_taps[N_TAPS];              /* FIR coefficients            */
q15_t output_buffer[M_BLOCK];           /* results land here           */
volatile uint32_t workload_checksum;

/* Same deterministic stream for every variant, including nonzero history. */
static q15_t stream_sample(uint32_t index)
{
    uint32_t bits = (index * UINT32_C(100)) & UINT32_C(0xffff);
    return (q15_t)((int32_t)(bits ^ UINT32_C(0x8000)) - 32768);
}

#ifdef SIM_PROFILE
/* Thumbulator TeamPlay trace triggers, not a physical GPIO setup. */
static void mark_active(uint32_t value)
{
    __asm__ volatile ("" ::: "memory");
    *(volatile uint32_t *)UINT32_C(0x48000818) = value;
    __asm__ volatile ("" ::: "memory");
}

static void report_hex(uint32_t value)
{
    const char *digits = "0123456789abcdef";
    for (int shift = 28; shift >= 0; shift -= 4)
        *(volatile uint32_t *)UINT32_C(0xe0000000) = digits[(value >> shift) & 15];
}
#endif

uint32_t run_workload(void)
{
    /* ---- Initialise input signal: ramp × 100 (wraps in Q15 range) ---- */
    for (int i = 0; i < M_BLOCK + N_TAPS; i++) {
        input_signal[i] = stream_sample((uint32_t)i);
    }

    /* ---- Initialise coefficients: 1000, 990, 980, … (low-pass like) ---- */
    for (int i = 0; i < N_TAPS; i++) {
        uint32_t bits = (UINT32_C(1000) - (uint32_t)i * 10) & UINT32_C(0xffff);
        filter_taps[i] = (q15_t)((int32_t)(bits ^ UINT32_C(0x8000)) - 32768);
    }

    uint32_t checksum = UINT32_C(2166136261);
    for (uint32_t job = 0; job < N_JOBS; ++job) {
        if (job != 0) {
            /* Carry N_TAPS samples; the kernels require only N_TAPS-1. */
            for (uint32_t i = 0; i < N_TAPS; ++i)
                input_signal[i] = input_signal[M_BLOCK + i];
            for (uint32_t i = 0; i < M_BLOCK; ++i)
                input_signal[N_TAPS + i] = stream_sample(N_TAPS + job * M_BLOCK + i);
        }

#ifdef SIM_PROFILE
        mark_active(1);
#endif

    /* ---- Dispatch to selected FIR variant ---- */
    /*
     * All three variants receive &input_signal[N_TAPS] as the base
     * pointer so that backward accesses (x[n-k]) never underrun the
     * allocated buffer.
     */
#if defined(VARIANT_DIRECT)
    fir_direct_q15(&input_signal[N_TAPS], filter_taps,
                   output_buffer, M_BLOCK, N_TAPS);

#elif defined(VARIANT_CIRCULAR)
    fir_circular_q15(&input_signal[N_TAPS], filter_taps,
                     output_buffer, M_BLOCK, N_TAPS);

#elif defined(VARIANT_UNROLLED)
    fir_unrolled4_q15(&input_signal[N_TAPS], filter_taps,
                      output_buffer, M_BLOCK, N_TAPS);

#endif

#ifdef SIM_PROFILE
        mark_active(UINT32_C(0x10000));
#endif
        for (uint32_t i = 0; i < M_BLOCK; ++i)
            checksum = (checksum ^ (uint16_t)output_buffer[i]) * UINT32_C(16777619);
    }
    return checksum;
}

int main(void)
{
    workload_checksum = run_workload();
#ifdef SIM_PROFILE
    const char *label = "FIR_RESULT ";
    while (*label)
        *(volatile uint32_t *)UINT32_C(0xe0000000) = *label++;
    report_hex(N_JOBS);
    *(volatile uint32_t *)UINT32_C(0xe0000000) = ' ';
    report_hex(workload_checksum);
    *(volatile uint32_t *)UINT32_C(0xe0000000) = '\n';
#endif

    /* Spin forever — expected termination in simulator via cycle limit */
    while (1) { }
    return 0;
}

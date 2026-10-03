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

/* ------------------------------------------------------------------ */
/* Static buffers in SRAM (.bss / .data)                               */
/* input_signal has N_TAPS guard samples prepended so that pointer     */
/* arithmetic in circular and unrolled variants stays in bounds.       */
/* ------------------------------------------------------------------ */
q15_t input_signal[M_BLOCK + N_TAPS];   /* length = M + N              */
q15_t filter_taps[N_TAPS];              /* FIR coefficients            */
q15_t output_buffer[M_BLOCK];           /* results land here           */

int main(void)
{
    /* ---- Initialise input signal: ramp × 100 (wraps in Q15 range) ---- */
    for (int i = 0; i < M_BLOCK + N_TAPS; i++) {
        input_signal[i] = (q15_t)(i * 100);
    }

    /* ---- Initialise coefficients: 1000, 990, 980, … (low-pass like) ---- */
    for (int i = 0; i < N_TAPS; i++) {
        filter_taps[i] = (q15_t)(1000 - i * 10);
    }

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

#else
#  error "No FIR variant selected. Define VARIANT_DIRECT, VARIANT_CIRCULAR, or VARIANT_UNROLLED."
#endif

    /* Spin forever — expected termination in simulator via cycle limit */
    while (1) { }
    return 0;
}

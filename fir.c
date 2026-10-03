#include "fir.h"

/* ====================================================================
 * fir.c — Three Q15 fixed-point FIR filter implementations.
 *
 * Accumulator convention:
 *   Q15 × Q15 → Q30 product; shift right by 15 to return to Q15.
 *   int32_t accumulator is wide enough to hold the sum of up to
 *   2^17 such products without overflow (covers N_TAPS up to ~4096).
 * ==================================================================== */

/* ------------------------------------------------------------------
 * 1. Direct-Loop FIR
 *    - Innermost access pattern: random index arithmetic (n-k)
 *    - Branch: conditional guard (n >= k) avoids negative index
 *    - Trade-off: index guard adds extra compare/branch per inner iter
 * ------------------------------------------------------------------ */
void fir_direct_q15(const q15_t *x, const q15_t *h, q15_t *y,
                    uint16_t block_size, uint16_t num_taps)
{
    for (uint16_t n = 0; n < block_size; n++) {
        int32_t acc = 0;
        for (uint16_t k = 0; k < num_taps; k++) {
            if (n >= k) {
                acc += (int32_t)x[n - k] * h[k];
            }
        }
        y[n] = (q15_t)(acc >> 15);
    }
}

/* ------------------------------------------------------------------
 * 2. Circular-Buffer FIR (Pointer Decrement)
 *    - Inner loop walks px backwards; ph forwards — pure pointer ops.
 *    - No index arithmetic or conditional guard in the inner loop.
 *    - Caller must pass x = &input[N_TAPS] so px-- stays in bounds.
 * ------------------------------------------------------------------ */
void fir_circular_q15(const q15_t *x, const q15_t *h, q15_t *y,
                      uint16_t block_size, uint16_t num_taps)
{
    for (uint16_t n = 0; n < block_size; n++) {
        int32_t acc = 0;
        const q15_t *px = &x[n];   /* points to most-recent sample */
        const q15_t *ph = h;

        for (uint16_t k = 0; k < num_taps; k++) {
            acc += (int32_t)(*px--) * (*ph++);
        }
        y[n] = (q15_t)(acc >> 15);
    }
}

/* ------------------------------------------------------------------
 * 3. Loop-Unrolled FIR (4× Manual Unrolling)
 *    - Processes four MAC operations per loop iteration.
 *    - Reduces loop-overhead instructions (branch, counter update).
 *    - Tail loop handles remaining taps when num_taps % 4 != 0.
 *    - NOTE: x[n - k - j] may index below x[0] for small n; caller
 *      must guarantee x = &input[N_TAPS] to keep accesses in bounds.
 * ------------------------------------------------------------------ */
void fir_unrolled4_q15(const q15_t *x, const q15_t *h, q15_t *y,
                       uint16_t block_size, uint16_t num_taps)
{
    for (uint16_t n = 0; n < block_size; n++) {
        int32_t acc = 0;
        uint16_t k = 0;
        /* Largest multiple of 4 that is <= num_taps */
        uint16_t taps_unrolled = num_taps & (uint16_t)~0x3U;

        /* ---- Unrolled body ---- */
        for (; k < taps_unrolled; k += 4) {
            acc += (int32_t)x[n - k]     * h[k];
            acc += (int32_t)x[n - k - 1] * h[k + 1];
            acc += (int32_t)x[n - k - 2] * h[k + 2];
            acc += (int32_t)x[n - k - 3] * h[k + 3];
        }
        /* ---- Scalar tail (0–3 remaining taps) ---- */
        for (; k < num_taps; k++) {
            acc += (int32_t)x[n - k] * h[k];
        }

        y[n] = (q15_t)(acc >> 15);
    }
}

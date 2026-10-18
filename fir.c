#include "fir.h"

/* ====================================================================
 * fir.c — Three Q15 fixed-point FIR filter implementations.
 *
 * All kernels use the history and arithmetic contract in fir.h.
 * A signed Q15 product fits int32_t, but a sum need not. Unsigned
 * accumulation defines wraparound without signed-overflow UB.
 * ==================================================================== */

/* ------------------------------------------------------------------
 * 1. Direct-Loop FIR
 *    - Uses signed index arithmetic into caller-supplied history.
 * ------------------------------------------------------------------ */
void fir_direct_q15(const q15_t *x, const q15_t *h, q15_t *y,
                    uint16_t block_size, uint16_t num_taps)
{
    for (uint16_t n = 0; n < block_size; n++) {
        uint32_t acc = 0;
        for (uint16_t k = 0; k < num_taps; k++) {
            acc += (uint32_t)((int32_t)x[(int32_t)n - k] * h[k]);
        }
        uint32_t bits = (acc >> 15) & UINT32_C(0xffff);
        y[n] = (q15_t)((int32_t)(bits ^ UINT32_C(0x8000)) - 32768);
    }
}

/* ------------------------------------------------------------------
 * 2. Circular-Buffer FIR (Pointer Decrement)
 *    - Inner loop walks px backwards; ph forwards — pure pointer ops.
 *    - No index arithmetic or conditional guard in the inner loop.
 *    - Decrements before loading, so exactly num_taps-1 history
 *      samples suffice without forming a pointer before the buffer.
 * ------------------------------------------------------------------ */
void fir_circular_q15(const q15_t *x, const q15_t *h, q15_t *y,
                      uint16_t block_size, uint16_t num_taps)
{
    for (uint16_t n = 0; n < block_size; n++) {
        uint32_t acc = 0;
        const q15_t *px = &x[n + 1];
        const q15_t *ph = h;

        for (uint16_t k = 0; k < num_taps; k++) {
            acc += (uint32_t)((int32_t)(*--px) * (*ph++));
        }
        uint32_t bits = (acc >> 15) & UINT32_C(0xffff);
        y[n] = (q15_t)((int32_t)(bits ^ UINT32_C(0x8000)) - 32768);
    }
}

/* ------------------------------------------------------------------
 * 3. Loop-Unrolled FIR (4× Manual Unrolling)
 *    - Processes four MAC operations per loop iteration.
 *    - Reduces loop-overhead instructions (branch, counter update).
 *    - Tail loop handles remaining taps when num_taps % 4 != 0.
 *    - Negative offsets access the same supplied history as above.
 * ------------------------------------------------------------------ */
void fir_unrolled4_q15(const q15_t *x, const q15_t *h, q15_t *y,
                       uint16_t block_size, uint16_t num_taps)
{
    for (uint16_t n = 0; n < block_size; n++) {
        uint32_t acc = 0;
        uint16_t k = 0;
        /* Largest multiple of 4 that is <= num_taps */
        uint16_t taps_unrolled = num_taps & (uint16_t)~0x3U;

        /* ---- Unrolled body ---- */
        for (; k < taps_unrolled; k += 4) {
            acc += (uint32_t)((int32_t)x[(int32_t)n - k]     * h[k]);
            acc += (uint32_t)((int32_t)x[(int32_t)n - k - 1] * h[k + 1]);
            acc += (uint32_t)((int32_t)x[(int32_t)n - k - 2] * h[k + 2]);
            acc += (uint32_t)((int32_t)x[(int32_t)n - k - 3] * h[k + 3]);
        }
        /* ---- Scalar tail (0–3 remaining taps) ---- */
        for (; k < num_taps; k++) {
            acc += (uint32_t)((int32_t)x[(int32_t)n - k] * h[k]);
        }

        uint32_t bits = (acc >> 15) & UINT32_C(0xffff);
        y[n] = (q15_t)((int32_t)(bits ^ UINT32_C(0x8000)) - 32768);
    }
}

#ifndef FIR_H
#define FIR_H

#include <stdint.h>

/* Q15 fixed-point type: 1 sign bit + 15 fractional bits */
typedef int16_t q15_t;

/* ------------------------------------------------------------------ */
/* FIR Filter Function Prototypes                                       */
/* All variants produce bit-exact results on the same input buffer.    */
/* ------------------------------------------------------------------ */

/**
 * fir_direct_q15 — Straightforward double-loop FIR.
 *
 * @x          : Input signal buffer (length >= block_size + num_taps - 1)
 * @h          : Filter coefficient buffer (length = num_taps)
 * @y          : Output buffer (length = block_size)
 * @block_size : Number of output samples to compute
 * @num_taps   : Filter order + 1
 */
void fir_direct_q15(const q15_t *x, const q15_t *h, q15_t *y,
                    uint16_t block_size, uint16_t num_taps);

/**
 * fir_circular_q15 — Pointer-decrement (circular-buffer style) FIR.
 * Avoids index arithmetic inside the inner loop by walking pointers directly.
 */
void fir_circular_q15(const q15_t *x, const q15_t *h, q15_t *y,
                      uint16_t block_size, uint16_t num_taps);

/**
 * fir_unrolled4_q15 — 4× manually unrolled inner loop FIR.
 * Reduces loop-control overhead; handles non-multiple-of-4 tail with scalar
 * cleanup loop.
 */
void fir_unrolled4_q15(const q15_t *x, const q15_t *h, q15_t *y,
                       uint16_t block_size, uint16_t num_taps);

#endif /* FIR_H */

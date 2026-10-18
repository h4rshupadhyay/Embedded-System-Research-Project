#ifndef FIR_H
#define FIR_H

#include <stdint.h>

/* Q15 fixed-point type: 1 sign bit + 15 fractional bits */
typedef int16_t q15_t;

/* ------------------------------------------------------------------ */
/* FIR Filter Function Prototypes                                       */
/* Shared contract for all three variants:                            */
/* x points to the first CURRENT sample within a contiguous buffer,  */
/* with num_taps-1 valid preceding history samples and block_size     */
/* current samples. h has num_taps entries, y has block_size entries.  */
/* The output buffer must not overlap x/history or h. num_taps >= 1. */
/* An empty block writes nothing.                                    */
/*                                                                  */
/* Products are signed Q30. Accumulation wraps modulo 2^32. Output is */
/* bits 15..30 of the sum interpreted as signed Q15 (no saturation).  */
/* This equals floor(exact_sum / 32768) wrapped to signed 16 bits,    */
/* including negative sums, without signed-overflow/shift ambiguity. */
/* To split a stream, carry the last num_taps-1 INPUT samples.        */
/* ------------------------------------------------------------------ */

/**
 * fir_direct_q15 — Straightforward double-loop FIR.
 *
 * @x          : Current-sample pointer with preceding history as above
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

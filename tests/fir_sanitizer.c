/* Exercise full-range products and exact history allocations under sanitizers. */
#include "fir.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

int main(void)
{
    void (*kernels[])(const q15_t *, const q15_t *, q15_t *, uint16_t, uint16_t) = {
        fir_direct_q15, fir_circular_q15, fir_unrolled4_q15
    };
    uint32_t state = 12345;
    for (uint16_t taps = 1; taps <= 32; ++taps) {
        for (uint16_t block = 1; block <= 33; block += 8) {
            q15_t *storage = malloc((taps - 1 + block) * sizeof(q15_t));
            q15_t *h = malloc(taps * sizeof(q15_t));
            q15_t *y = malloc(block * sizeof(q15_t));
            if (!storage || !h || !y)
                return 2;
            for (unsigned i = 0; i < taps - 1u + block; ++i) {
                state = state * 1664525u + 1013904223u;
                storage[i] = (q15_t)((int32_t)(state & 65535) - 32768);
            }
            for (unsigned i = 0; i < taps; ++i)
                h[i] = (i & 1) ? 32767 : -32768;
            for (unsigned variant = 0; variant < 3; ++variant) {
                kernels[variant](storage + taps - 1, h, y, block, taps);
                for (unsigned n = 0; n < block; ++n) {
                    int64_t total = 0;
                    for (unsigned k = 0; k < taps; ++k)
                        total += (int64_t)storage[taps - 1 + n - k] * h[k];
                    int64_t scaled = total >= 0 ? total / 32768 : -((-total + 32767) / 32768);
                    uint16_t bits = (uint16_t)scaled;
                    int32_t expected = bits < 32768 ? bits : (int32_t)bits - 65536;
                    if (y[n] != expected) {
                        fprintf(stderr, "Mismatch: variant=%u taps=%u block=%u sample=%u\n",
                                variant, taps, block, n);
                        return 1;
                    }
                }
            }
            free(y);
            free(h);
            free(storage);
        }
    }
    puts("Sanitizer/reference checks passed");
    return 0;
}

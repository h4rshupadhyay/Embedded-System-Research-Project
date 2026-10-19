#ifndef FIR_BASELINE_KERNELS_H
#define FIR_BASELINE_KERNELS_H
#include <stdint.h>
/* Research baselines, not a production API. state has taps-1+block elements;
 * coefficients are lag order; history oldest-first. Inputs/outputs disjoint.
 * direct32/fold32 require M*sum(abs(h)) <= INT32_MAX over admitted inputs.
 * fold64/fold32 require symmetry and 2*M*abs(h_pair) <= INT32_MAX.
 * fold64_wide requires symmetry only. All retain every product, including
 * zero coefficients. Halfband-specialized performance is outside this pilot. */
typedef void (*fir_function)(int16_t *, const int16_t *, const int16_t *,
                             int16_t *, uint32_t, uint32_t);
#define FIR_DECL(name) void name(int16_t *, const int16_t *, const int16_t *, int16_t *, uint32_t, uint32_t)
FIR_DECL(direct64);
FIR_DECL(direct32);
FIR_DECL(fold64);
FIR_DECL(fold32);
FIR_DECL(fold64_wide);
#endif

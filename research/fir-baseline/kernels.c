/* Exploratory exact FIR baselines; see kernels.h for admission proofs. */
#include "kernels.h"

static inline int16_t floor15(int32_t s)
{
    /* Defined floor division even for negative inputs; no signed right shift. */
    return (int16_t)(s >= 0 ? s / 32768 : -1 - (-(s + 1)) / 32768);
}

static inline int16_t quant32(int32_t s)
{
    if (s >= 1073741824) return 32767;
    if (s <= -1073741824) return -32768;
    return floor15(s);
}

static inline int16_t quant64(int64_t s)
{
    if (s >= 1073741824LL) return 32767;
    if (s <= -1073741824LL) return -32768;
    return floor15((int32_t)s);
}

static inline void append(int16_t *state, const int16_t *x, uint32_t n, uint32_t b)
{
    for (uint32_t i=0; i<b; ++i) state[n-1+i]=x[i];
}

static inline void retain(int16_t *state, uint32_t n, uint32_t b)
{
    /* Forward copy is valid when source and destination overlap. */
    for (uint32_t i=0; i<n-1; ++i) state[i]=state[b+i];
}

#define DIRECT(NAME, ACC, QUANT) \
void NAME(int16_t *state, const int16_t *h, const int16_t *x, int16_t *y, uint32_t n, uint32_t b) \
{ \
    append(state,x,n,b); \
    for (uint32_t j=0; j<b; ++j) { \
        ACC sum=0; \
        for (uint32_t i=0; i<n; ++i) \
            sum += (int32_t)h[i] * (int32_t)state[j+n-1-i]; \
        y[j]=QUANT(sum); \
    } \
    retain(state,n,b); \
}

#define FOLDED(NAME, ACC, PRODUCT, QUANT) \
void NAME(int16_t *state, const int16_t *h, const int16_t *x, int16_t *y, uint32_t n, uint32_t b) \
{ \
    append(state,x,n,b); \
    for (uint32_t j=0; j<b; ++j) { \
        ACC sum=0; \
        uint32_t i=0; \
        for (; i<n/2; ++i) { \
            int32_t pair=(int32_t)state[j+i]+(int32_t)state[j+n-1-i]; \
            sum += (PRODUCT)h[i] * pair; \
        } \
        if (n & 1U) sum += (int32_t)h[i] * (int32_t)state[j+i]; \
        y[j]=QUANT(sum); \
    } \
    retain(state,n,b); \
}

DIRECT(direct64, int64_t, quant64)
DIRECT(direct32, int32_t, quant32)
FOLDED(fold64, int64_t, int32_t, quant64)
FOLDED(fold32, int32_t, int32_t, quant32)
FOLDED(fold64_wide, int64_t, int64_t, quant64)

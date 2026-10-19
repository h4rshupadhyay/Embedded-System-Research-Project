/* Subprocess harness so 32-bit host GCC can be tested from 64-bit Python. */
#include "kernel.h"
#include <stdio.h>
#include <stdint.h>

#define LIMIT 2048
static struct {
    uint64_t lo;
    ProbeState state;
    uint64_t hi;
} guarded;
static int16_t input[LIMIT], output[LIMIT + 4];

static void state_line(char tag) {
    putchar(tag);
    for (unsigned k = 0; k < TAPS - 1; ++k)
        printf(" %lld", (long long)probe_get_state(&guarded.state, k));
    putchar('\n');
}

int main(void) {
    unsigned count, calls;
    if (scanf("%u %u", &count, &calls) != 2 || count > LIMIT) return 2;
    for (unsigned i = 0; i < count; ++i) {
        int value;
        if (scanf("%d", &value) != 1 || value < -32768 || value > 32767) return 2;
        input[i] = (int16_t)value;
    }
    guarded.lo = guarded.hi = UINT64_C(0x5a5a5a5a5a5a5a5a);
    for (unsigned i = 0; i < count + 4; ++i) output[i] = 23130;
    probe_init(&guarded.state);
    state_line('I');
    unsigned offset = 0;
    for (unsigned call = 0; call < calls; ++call) {
        unsigned b;
        if (scanf("%u", &b) != 1 || b < 1 || b > BLOCK || offset + b > count) return 2;
        probe_process(&guarded.state, input + offset, output + 2 + offset, b);
        offset += b;
        state_line('S');
    }
    if (offset != count) return 2;
    putchar('O');
    for (unsigned i = 0; i < count; ++i) printf(" %d", output[i + 2]);
    putchar('\n');
    printf("G %d\n", guarded.lo == UINT64_C(0x5a5a5a5a5a5a5a5a) &&
           guarded.hi == UINT64_C(0x5a5a5a5a5a5a5a5a) &&
           output[0] == 23130 && output[1] == 23130 &&
           output[count + 2] == 23130 && output[count + 3] == 23130);
    printf("B %u\n", probe_state_bytes());
    return 0;
}

@ startup.s — Minimal Cortex-M0 startup for Thumbulator (Armv6-M, Thumb)
@
@ Provides:
@   - A 2-entry vector table (.vectors section):
@       word 0: initial Main Stack Pointer  (top of 8 KiB SRAM)
@       word 1: Reset_Handler address | 1  (Thumb bit)
@   - Reset_Handler: jumps straight to main()
@
@ The simulator reads flash[0] as the initial SP and flash[1] as the
@ reset vector; the Thumb-bit (LSB=1) is mandatory.

    .syntax unified
    .cpu    cortex-m0
    .thumb

@ ── Vector table ─────────────────────────────────────────────────────
    .section .vectors, "a", %progbits
    .align  2
    .global _vectors
_vectors:
    .word   0x20002000          @ [0] Initial Stack Pointer (top of 8 KiB SRAM)
    .word   Reset_Handler + 1   @ [1] Reset vector (Thumb bit set)

@ ── Reset handler ────────────────────────────────────────────────────
    .section .text.Reset_Handler, "ax", %progbits
    .align  1
    .thumb_func
    .global Reset_Handler
    .type   Reset_Handler, %function
Reset_Handler:
    bl      main        @ call main(); never returns (main spins in while(1))
    b       .           @ safety: branch-to-self if main returns
    .size   Reset_Handler, . - Reset_Handler

.syntax unified
.cpu cortex-m0
.thumb
.section .vectors,"a",%progbits
.word 0x20001ff0
.word Reset_Handler
.section .text.Reset_Handler,"ax",%progbits
.thumb_func
.global Reset_Handler
Reset_Handler:
    ldr r0, =_bss_start
    ldr r1, =_bss_end
    movs r2, #0
1:  cmp r0, r1
    bhs 2f
    str r2, [r0]
    adds r0, #4
    b 1b
2:  bl main
    .short 0xdf01
    b .

.section .text.measured,"ax",%progbits
.thumb_func
.global measured
measured:
    push {r4,r5,r6,lr}
    ldr r4, =0x48000818
    movs r5, #1
    str r5, [r4]
    bl process_stream
    str r5, [r4,#16]
    pop {r4,r5,r6,pc}

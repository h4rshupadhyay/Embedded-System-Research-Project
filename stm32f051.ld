/* ============================================================
 * stm32f051.ld — Linker script for STM32F051 (Cortex-M0)
 * Flash: 64K @ 0x08000000
 * SRAM:   8K @ 0x20000000
 * ============================================================ */

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 64K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 8K
}

SECTIONS
{
  /* Interrupt vector table must be first in Flash */
  .text : {
    *(.vectors)
    *(.text*)
    *(.rodata*)
    . = ALIGN(4);
  } > FLASH

  /* Initialized data: stored in Flash, copied to RAM at startup */
  .data : {
    *(.data*)
    . = ALIGN(4);
  } > RAM AT > FLASH

  /* Zero-initialized BSS: stays in RAM */
  .bss : {
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
  } > RAM
}

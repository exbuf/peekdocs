@ sample.s -- ARM Cortex-M4 assembly: GPIO toggle for timing measurement
@ PEEKDOCS_TEST_MARKER

    .syntax unified
    .cpu cortex-m4
    .thumb

    .equ GPIOA_BASE,   0x40020000
    .equ GPIO_ODR,     0x14        @ Output data register offset
    .equ GPIO_BSRR,    0x18        @ Bit set/reset register offset
    .equ PIN_MASK,     (1 << 5)    @ PA5 (onboard LED on many boards)

    .section .text
    .global toggle_pin
    .type toggle_pin, %function

@ toggle_pin: Toggle PA5 output, useful for oscilloscope timing
@ Clobbers: r0, r1
toggle_pin:
    ldr  r0, =GPIOA_BASE
    ldr  r1, [r0, #GPIO_ODR]
    eor  r1, r1, #PIN_MASK
    str  r1, [r0, #GPIO_ODR]
    bx   lr

    .global delay_cycles
    .type delay_cycles, %function

@ delay_cycles: Busy-wait delay loop
@ Input: r0 = number of loop iterations
delay_cycles:
    subs r0, r0, #1
    bne  delay_cycles
    bx   lr

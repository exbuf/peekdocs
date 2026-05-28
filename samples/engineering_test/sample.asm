; sample.asm -- x86 assembly: 16-bit ADC read via port I/O
; PEEKDOCS_TEST_MARKER

section .data
    adc_base    equ  0x300       ; Base I/O address of ADC card
    adc_ctrl    equ  adc_base+0  ; Control register
    adc_status  equ  adc_base+1  ; Status register
    adc_data_lo equ  adc_base+2  ; Data low byte
    adc_data_hi equ  adc_base+3  ; Data high byte

section .text
global read_adc_channel

; read_adc_channel: Read a single ADC channel
; Input:  AL = channel number (0-15)
; Output: AX = 12-bit ADC value
read_adc_channel:
    push dx
    mov  dx, adc_ctrl
    out  dx, al              ; Select channel and start conversion

.wait_ready:
    mov  dx, adc_status
    in   al, dx
    test al, 0x80            ; Check conversion-complete bit
    jz   .wait_ready

    mov  dx, adc_data_lo
    in   al, dx
    mov  ah, al
    mov  dx, adc_data_hi
    in   al, dx
    xchg al, ah              ; AX = 12-bit result
    and  ax, 0x0FFF

    pop  dx
    ret

# Assembly (GAS) test file for peekdocs
.text
.globl _start
_start:
    movl $1, %eax
    int $0x80

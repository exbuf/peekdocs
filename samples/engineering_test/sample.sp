* sample.sp -- SPICE simulation: RC low-pass filter frequency response
* PEEKDOCS_TEST_MARKER
*
* First-order RC low-pass filter
* Cutoff frequency: f_c = 1/(2*pi*R*C) = 1591 Hz
*
Vin input 0 AC 1.0

R1 input output 1K
C1 output 0 100N

* Second stage for steeper rolloff
R2 output stage2 1K
C2 stage2 0 100N

Rload stage2 0 100K

.AC DEC 50 10 1MEG
.PRINT AC VM(output) VP(output)
.PRINT AC VM(stage2) VP(stage2)

* Transient analysis with 1 kHz square wave input
Vpulse input2 0 PULSE(0 5 0 1N 1N 0.5M 1M)
.TRAN 0.01M 5M

.OPTIONS POST ACCURATE
.END

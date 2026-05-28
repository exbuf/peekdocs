C     sample.f -- Fortran 77 beam deflection calculation
C     PEEKDOCS_TEST_MARKER
C
      PROGRAM BEAM
      IMPLICIT NONE
      REAL*8 E, I, L, W, X, DEFL
      REAL*8 DX
      INTEGER J, NPTS
      PARAMETER (NPTS = 20)

C     Material: A36 structural steel
C     E = Young's modulus (Pa), I = moment of inertia (m^4)
      E = 200.0D9
      I = 8.33D-6
      L = 3.0D0
      W = 5000.0D0

      DX = L / DBLE(NPTS)

      WRITE(*,*) '  X (m)     Deflection (mm)'
      WRITE(*,*) '  ------    ---------------'

      DO 10 J = 0, NPTS
          X = DX * DBLE(J)
          DEFL = (W * X) / (24.0D0 * E * I)
     &         * (L**3 - 2.0D0*L*X**2 + X**3)
          WRITE(*,100) X, DEFL * 1000.0D0
  100     FORMAT(F8.3, 4X, F12.6)
   10 CONTINUE

      STOP
      END

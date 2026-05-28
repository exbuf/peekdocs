! sample.f90 -- Finite difference heat equation solver (1D)
! PEEKDOCS_TEST_MARKER

program heat_equation
    implicit none
    integer, parameter :: nx = 100
    integer, parameter :: nt = 5000
    real(8), parameter :: dx = 0.01d0
    real(8), parameter :: dt = 1.0d-5
    real(8), parameter :: alpha = 1.172d-5  ! thermal diffusivity of steel
    real(8) :: u(nx), u_new(nx)
    real(8) :: r
    integer :: i, t

    r = alpha * dt / (dx * dx)

    ! Initial condition: left end at 100C, rest at 20C
    u = 20.0d0
    u(1) = 100.0d0

    ! Time stepping with explicit Euler
    do t = 1, nt
        u_new(1) = u(1)
        u_new(nx) = u(nx)
        do i = 2, nx - 1
            u_new(i) = u(i) + r * (u(i-1) - 2.0d0*u(i) + u(i+1))
        end do
        u = u_new
    end do

    ! Output final temperature profile
    do i = 1, nx
        write(*,'(F8.4, 2X, F10.4)') (i-1)*dx, u(i)
    end do

end program heat_equation

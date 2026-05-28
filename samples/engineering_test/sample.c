/*
 * pid_controller.c -- Discrete PID controller for motor speed regulation
 * PEEKDOCS_TEST_MARKER
 */

#include <stdio.h>
#include <stdlib.h>

typedef struct {
    double kp;          /* proportional gain */
    double ki;          /* integral gain */
    double kd;          /* derivative gain */
    double integral;
    double prev_error;
    double output_min;
    double output_max;
} PIDController;

void pid_init(PIDController *pid, double kp, double ki, double kd) {
    pid->kp = kp;
    pid->ki = ki;
    pid->kd = kd;
    pid->integral = 0.0;
    pid->prev_error = 0.0;
    pid->output_min = -100.0;
    pid->output_max = 100.0;
}

double pid_update(PIDController *pid, double setpoint, double measured, double dt) {
    double error = setpoint - measured;
    pid->integral += error * dt;
    double derivative = (error - pid->prev_error) / dt;
    pid->prev_error = error;

    double output = pid->kp * error + pid->ki * pid->integral + pid->kd * derivative;

    if (output > pid->output_max) output = pid->output_max;
    if (output < pid->output_min) output = pid->output_min;
    return output;
}

#include "../include/pid_controller.h"

double PIDController::compute(double error) {
    double derivative = error - last_error;
    last_error = error;
    return kp * error + kd * derivative;
}
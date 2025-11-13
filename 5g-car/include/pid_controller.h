#ifndef PID_CONTROLLER_H
#define PID_CONTROLLER_H

class PIDController {
private:
    double kp = 0.25;
    double kd = 0.125;
    double last_error = 0.0;

public:
    double compute(double error);
};

#endif // PID_CONTROLLER_H
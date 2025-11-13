#ifndef CONTROL_ACTUATOR_H
#define CONTROL_ACTUATOR_H

#include "common.h"
#include "pid_controller.h"
#include "gpio_control.h"

class ControlActuator {
private:
    thread control_thread;
    bool stop_requested = false;
    PIDController pid;
    GPIOControl gpio;
    double min_angle = 0, max_angle = 200;
    int red_nums = 0, pass_nums = 0;
    bool change_dao_finish = false, red_cone_finish = false, ab_finish = false, yellow_finish = false;
    int landr_pass = 0;

public:
    ControlActuator();
    ~ControlActuator();
private:
    void controlLoop();
};

#endif // CONTROL_ACTUATOR_H
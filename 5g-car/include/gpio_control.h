#ifndef GPIO_CONTROL_H
#define GPIO_CONTROL_H

#include <pigpio.h>
#include <thread>
#include <chrono>

class GPIOControl {
private:
    int motor_pin = 13;
    int servo_pin = 12;
    int last_dian = 10000;

public:
    void init();
    void setMotor(int value);
    void setServo(double angle);
    ~GPIOControl();
};

#endif // GPIO_CONTROL_H
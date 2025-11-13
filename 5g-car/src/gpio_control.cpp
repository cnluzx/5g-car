#include "../include/gpio_control.h"
#include "../include/common.h"

void GPIOControl::init() {
    if (gpioInitialise() < 0) exit(1);
    gpioSetMode(motor_pin, PI_OUTPUT);
    gpioSetPWMrange(motor_pin, 40000);
    gpioSetPWMfrequency(motor_pin, 200);
    gpioSetMode(servo_pin, PI_OUTPUT);
    gpioSetPWMrange(servo_pin, 100);  // 改为100，便于5%-10%占空比计算
    gpioSetPWMfrequency(servo_pin, 50);
    gpioPWM(motor_pin, 10000);  // 停止电机
    setServo(100);  // 默认100度
}



void GPIOControl::setMotor(int value) {
    if (value > 10800) {
        for (int i = max(10800, last_dian); i <= value; i += 50) {
            gpioPWM(motor_pin, min(i, value));
            this_thread::sleep_for(25ms);
        }
    } else {
        gpioPWM(motor_pin, value);
    }
    last_dian = value;
}

void GPIOControl::setServo(double angle) {
    // 50Hz (20ms周期) 舵机: 角度[-90,90] 映射到 PWM [2.5,12.5] (占空比2.5%-12.5%)
    // 脉宽: 2.5%*20ms=0.5ms (-90°), 12.5%*20ms=2.5ms (90°), 中点7.5% (1.5ms, 0°)


    double normalized_angle = (angle + 90.0) / 180.0;  // 归一化 -90->0, 90->1
    double pwm_value = 2.5 + (normalized_angle * 10.0);  // 线性映射 [2.5, 12.5]
    cout << "Servo angle: " << angle << ", PWM value: " << pwm_value << "\n";
    gpioPWM(servo_pin, static_cast<int>(round(pwm_value)));  // 四舍五入到整数
}

GPIOControl::~GPIOControl() {
    gpioTerminate();
}
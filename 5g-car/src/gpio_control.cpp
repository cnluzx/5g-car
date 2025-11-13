#include "../include/gpio_control.h"
#include "../include/config.h"
#include "../include/debug.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <cmath>

using namespace std;
using namespace chrono;

void GPIOControl::init() {
    LOG_INFO("GPIO 初始化中...");
    
    // 初始化 pigpio 库
    if (gpioInitialise() < 0) {
        LOG_ERROR("pigpio 库初始化失败！");
        exit(1);
    }
    
    // ==================== 电机配置 ====================
    gpioSetMode(motor_pin, PI_OUTPUT);
    gpioSetPWMrange(motor_pin, MOTOR_PWM_RANGE);
    gpioSetPWMfrequency(motor_pin, MOTOR_PWM_FREQ);
    gpioPWM(motor_pin, MOTOR_NEUTRAL);  // 初始化为停止状态
    LOG_INFO("电机初始化完成");
    
    // ==================== 舵机配置 ====================
    // 50Hz (20ms周期) 舵机: 角度[-90,90] 映射到 PWM [2.5,12.5] (占空比2.5%-12.5%)
    // 脉宽: 2.5%*20ms=0.5ms (-90°), 12.5%*20ms=2.5ms (90°), 中点7.5% (1.5ms, 0°)
    gpioSetMode(servo_pin, PI_OUTPUT);
    gpioSetPWMrange(servo_pin, SERVO_PWM_RANGE);  // 范围改为100，便于计算
    gpioSetPWMfrequency(servo_pin, SERVO_PWM_FREQ);  // 50Hz
    setServo(SERVO_NEUTRAL);  // 初始化为中性位置
    LOG_INFO("舵机初始化完成");
    
    LOG_INFO("GPIO 初始化完成");
}

void GPIOControl::setMotor(int value) {
    // 限制电机速度在合理范围内
    value = max(min(value, MOTOR_MAX), MOTOR_MIN);
    
    // 如果需要加速（速度增加较多时），采用平滑加速策略
    if (value > MOTOR_NEUTRAL && value > last_dian) {
        for (int i = max(MOTOR_NEUTRAL, last_dian); i <= value; i += MOTOR_ACCEL_STEP) {
            gpioPWM(motor_pin, min(i, value));
            this_thread::sleep_for(milliseconds(MOTOR_ACCEL_DELAY));
        }
    } else {
        // 减速或维持速度时直接设置
        gpioPWM(motor_pin, value);
    }
    
    last_dian = value;
}

void GPIOControl::setServo(double angle) {
    // 限制舵机角度范围
    angle = max(min(angle, SERVO_MAX), SERVO_MIN);
    
    // 角度映射计算
    // 目标：将 [SERVO_MIN, SERVO_MAX] 映射到 [2.5, 12.5] (PWM 占空比百分比)
    // 例如：0 度对应 100 (7.5%)，-90 度对应 25 (2.5%)，90 度对应 175 (12.5%)
    // 但由于我们使用的范围是 [0, SERVO_MAX]，直接计算如下：
    
    // 新的映射方式（基于配置中的中性位置）：
    // 假设 SERVO_NEUTRAL = 100 对应 0 度（实际由硬件决定）
    // 这里简化为线性映射
    
    double pwm_value = angle;  // 直接使用角度值作为 PWM 占空比设置
    
    // 输出调试信息
    stringstream ss;
    ss << "舵机角度设置: " << angle << " 度, PWM 值: " << static_cast<int>(pwm_value);
    LOG_DEBUG(ss.str());
    
    gpioPWM(servo_pin, static_cast<int>(round(pwm_value)));
}

GPIOControl::~GPIOControl() {
    LOG_INFO("GPIO 清理中...");
    
    // 确保电机和舵机都处于安全状态
    try {
        gpioPWM(motor_pin, MOTOR_NEUTRAL);
        gpioPWM(servo_pin, static_cast<int>(SERVO_NEUTRAL));
        this_thread::sleep_for(milliseconds(100));
    } catch (...) {
        LOG_WARN("GPIO 清理时出现异常");
    }
    
    // 终止 pigpio 库
    gpioTerminate();
    
    LOG_INFO("GPIO 已清理");
}
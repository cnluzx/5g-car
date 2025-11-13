#ifndef GPIO_CONTROL_H
#define GPIO_CONTROL_H

#include <pigpio.h>
#include <thread>
#include <chrono>

/**
 * @class GPIOControl
 * @brief GPIO 硬件控制类，用于控制电机和舵机
 * 
 * 功能：
 * - 初始化 pigpio 库和 GPIO 引脚
 * - 控制直流电机速度（通过 PWM）
 * - 控制舵机角度（通过 PWM）
 * - 清理和释放资源
 */
class GPIOControl {
private:
    // GPIO 引脚号（可通过 config.h 修改）
    int motor_pin = 13;
    int servo_pin = 12;
    
    // 电机最后设置的 PWM 值（用于平滑加速）
    int last_dian = 10000;

public:
    /**
     * @brief 初始化 GPIO 和 PWM
     * 
     * 配置：
     * - 电机：PWM 频率 200Hz，范围 40000
     * - 舵机：PWM 频率 50Hz，范围 100
     */
    void init();
    
    /**
     * @brief 设置电机速度
     * 
     * @param value PWM 值 (10000 = 停止，11000 = 前进，9000 = 后退)
     * 
     * 特点：
     * - 加速时采用平滑加速策略，避免突兀启动
     * - 减速时直接设置，反应迅速
     * - 值会限制在 [MOTOR_MIN, MOTOR_MAX] 范围内
     */
    void setMotor(int value);
    
    /**
     * @brief 设置舵机角度
     * 
     * @param angle 舵机角度 (0-200，100 为中性位置)
     * 
     * 特点：
     * - 采用线性 PWM 映射
     * - 角度会限制在 [SERVO_MIN, SERVO_MAX] 范围内
     * - 50Hz PWM 频率，适合标准舵机
     */
    void setServo(double angle);
    
    /**
     * @brief 析构函数，清理 GPIO 资源
     */
    ~GPIOControl();
};

#endif // GPIO_CONTROL_H
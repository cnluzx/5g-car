#include "../include/gpio_control.h"
#include "../include/config.h"
#include "../include/debug.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <fstream>

using namespace std;
using namespace chrono;

// ==================== pigpiod 守护进程管理函数 ====================

bool GPIOControl::isPigpiodRunning() {
    // 使用 pgrep 命令检查 pigpiod 进程是否存在
    int ret = system("pgrep -x pigpiod > /dev/null 2>&1");
    return (ret == 0);  // 返回值为 0 表示进程存在
}

bool GPIOControl::startPigpiod() {
    LOG_INFO("尝试启动 pigpiod 守护进程...");
    
    // 先检查是否已经运行
    if (isPigpiodRunning()) {
        LOG_INFO("pigpiod 已经在运行");
        return true;
    }
    
    // 启动 pigpiod（后台运行）
    // -l: 使用本地套接字（仅本机访问，推荐）
    // -g: 指定 GPIO 引脚
    int ret = system("pigpiod -l -g &");
    
    if (ret == 0 || ret == 256) {  // ret == 256 表示成功但进程在后台
        LOG_INFO("pigpiod 启动命令已发送");
        
        // 等待 pigpiod 完全启动（通常需要 100-500ms）
        for (int i = 0; i < 10; i++) {
            this_thread::sleep_for(milliseconds(100));
            if (isPigpiodRunning()) {
                LOG_INFO("pigpiod 已成功启动");
                pigpiod_started = true;
                return true;
            }
        }
        
        LOG_WARN("pigpiod 启动缓慢，继续等待...");
        this_thread::sleep_for(milliseconds(500));
        
        if (isPigpiodRunning()) {
            LOG_INFO("pigpiod 最终成功启动");
            pigpiod_started = true;
            return true;
        }
    }
    
    LOG_ERROR("启动 pigpiod 失败！请手动执行: sudo pigpiod");
    return false;
}

bool GPIOControl::stopPigpiod() {
    if (!pigpiod_started) {
        LOG_DEBUG("pigpiod 由本程序启动，准备关闭");
        return true;  // 不是本程序启动的，无需关闭
    }
    
    LOG_INFO("正在关闭 pigpiod 守护进程...");
    
    // 方法 1: 使用 pigpiod 的官方关闭命令
    int ret = system("killall pigpiod 2>/dev/null");
    
    if (ret == 0) {
        LOG_INFO("pigpiod 已关闭");
        return true;
    }
    
    // 方法 2: 如果上述方法失败，尝试 kill
    LOG_WARN("尝试使用 kill 命令关闭 pigpiod");
    ret = system("pkill -9 pigpiod 2>/dev/null");
    
    if (ret == 0 || !isPigpiodRunning()) {
        LOG_INFO("pigpiod 已成功关闭");
        return true;
    }
    
    LOG_WARN("pigpiod 关闭可能未成功");
    return false;
}

// ==================== GPIO 初始化 ====================

void GPIOControl::init() {
    LOG_INFO("GPIO 初始化中...");
    
    // ==================== 步骤 1: 启动/连接 pigpiod ====================
    if (!startPigpiod()) {
        LOG_ERROR("无法启动 pigpiod，程序退出");
        exit(1);
    }
    
    // ==================== 步骤 2: 初始化 pigpio 库 ====================
    int ret = gpioInitialise();
    if (ret < 0) {
        LOG_ERROR("pigpio 库初始化失败，错误代码: " + to_string(ret));
        LOG_ERROR("可能的原因:");
        LOG_ERROR("  1. pigpiod 未启动 (运行: sudo pigpiod)");
        LOG_ERROR("  2. 没有 root 权限");
        LOG_ERROR("  3. GPIO 被其他进程占用");
        stopPigpiod();
        exit(1);
    }
    
    LOG_INFO("pigpio 库初始化成功");
    
    // ==================== 步骤 3: 配置电机 ====================
    LOG_INFO("正在配置电机...");
    gpioSetMode(motor_pin, PI_OUTPUT);
    gpioSetPWMrange(motor_pin, MOTOR_PWM_RANGE);
    gpioSetPWMfrequency(motor_pin, MOTOR_PWM_FREQ);
    gpioPWM(motor_pin, MOTOR_NEUTRAL);  // 初始化为停止状态
    LOG_INFO("电机初始化完成 (引脚: " + to_string(motor_pin) + ")");
    
    // ==================== 步骤 4: 配置舵机 ====================
    LOG_INFO("正在配置舵机...");
    // 50Hz (20ms周期) 舵机: 角度[-90,90] 映射到 PWM [2.5,12.5] (占空比2.5%-12.5%)
    // 脉宽: 2.5%*20ms=0.5ms (-90°), 12.5%*20ms=2.5ms (90°), 中点7.5% (1.5ms, 0°)
    gpioSetMode(servo_pin, PI_OUTPUT);
    gpioSetPWMrange(servo_pin, SERVO_PWM_RANGE);  // 范围改为100，便于计算
    gpioSetPWMfrequency(servo_pin, SERVO_PWM_FREQ);  // 50Hz
    setServo(SERVO_NEUTRAL);  // 初始化为中性位置
    LOG_INFO("舵机初始化完成 (引脚: " + to_string(servo_pin) + ")");
    
    LOG_INFO("GPIO 初始化完成");
}

// ==================== 电机控制 ====================

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

// ==================== 舵机控制 ====================

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

// ==================== 析构函数和清理 ====================

GPIOControl::~GPIOControl() {
    LOG_INFO("GPIOControl 析构中...");
    
    try {
        // ==================== 步骤 1: 设置电机和舵机为安全位置 ====================
        LOG_INFO("设置电机和舵机到安全位置...");
        gpioPWM(motor_pin, MOTOR_NEUTRAL);      // 电机停止
        gpioPWM(servo_pin, static_cast<int>(SERVO_NEUTRAL));  // 舵机中性
        this_thread::sleep_for(milliseconds(100));
        
        // ==================== 步骤 2: 断开 pigpio 库连接 ====================
        LOG_INFO("正在关闭 pigpio 库连接...");
        gpioTerminate();
        LOG_INFO("pigpio 库已关闭");
        
        // ==================== 步骤 3: 关闭 pigpiod 守护进程 ====================
        if (pigpiod_started) {
            LOG_INFO("正在关闭 pigpiod 守护进程...");
            stopPigpiod();
        } else {
            LOG_DEBUG("pigpiod 守护进程非本程序启动，跳过关闭");
        }
        
    } catch (const exception& e) {
        LOG_ERROR(string("GPIO 清理时出现异常: ") + e.what());
    } catch (...) {
        LOG_ERROR("GPIO 清理时出现未知异常");
    }
    
    LOG_INFO("GPIOControl 已清理完毕");
}
#include "../include/control_actuator.h"
#include "../include/config.h"
#include "../include/debug.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <algorithm>
#include <sstream>

using namespace std;
using namespace chrono;

ControlActuator::ControlActuator() : gpio() {
    LOG_INFO("ControlActuator 初始化中...");
    gpio.init();
    control_thread = thread(&ControlActuator::controlLoop, this);
    LOG_INFO("ControlActuator 初始化完成，控制线程已启动");
}

void ControlActuator::controlLoop() {
    LOG_INFO("控制循环已启动");
    
    auto last_time = steady_clock::now();
    int frame_count = 0;
    
    while (!stop_requested && running) {
        ProcessedFrame result;
        {
            unique_lock<mutex> lock(result_mutex);
            // 等待处理结果
            result_cv.wait(lock, [&] { return !result_queue.empty() || !running; });
            if (!result_queue.empty()) {
                result = move(result_queue.front());
                result_queue.pop();
            } else {
                continue;
            }
        }

        frame_count++;
        
        // ==================== 状态机核心逻辑 ====================
        
        // 1. 蓝牌移除检测
        if (!blue_removed && result.blue_card_removed) {
            blue_removed = true;
            LOG_INFO("蓝牌已移除，开始运动");
            gpio.setMotor(11000);
        }

        // 2. 斑马线检测
        if (blue_removed && !has_banma) {
            if (result.zebra_crossing) {
                has_banma = true;
                LOG_INFO("检测到斑马线，继续前进");
                gpio.setMotor(11000);
            }
        }

        // 计算基础的中线误差
        double error = MIDLINE_CENTER - result.mid_line;
        
        // 如果在入库模式，调整中线目标
        if (ab_finish) {
            error = MIDLINE_CENTER - (result.mid_line + 40);
        }

        // 通过 PID 计算舵机角度调整
        double angle_adjust = pid.compute(error);
        double angle = SERVO_NEUTRAL + angle_adjust;  // 中性位置调整
        angle = max(min(angle, SERVO_MAX), SERVO_MIN);  // 限制舵机角度范围

        // ==================== 红锥绕行逻辑（关键修复点 1） ====================
        if (has_banma && !red_cone_finish && result.red_cone_pos != -1) {
            // 检测到红锥，进入绕行模式
            gpio.setMotor(11000);
            
            // 根据红锥序号（奇偶）调整偏移方向
            if (red_nums % 2 == 1) {
                error = MIDLINE_CENTER - (result.red_cone_pos - RED_CONE_OFFSET);
            } else {
                error = MIDLINE_CENTER - (result.red_cone_pos + RED_CONE_OFFSET);
            }
            
            angle_adjust = pid.compute(error);
            angle = SERVO_NEUTRAL + angle_adjust;
            
            red_nums++;
            stringstream ss;
            ss << "检测到第 " << red_nums << " 个红锥";
            LOG_INFO(ss.str());
            
            // ★ 关键修复：修改 pass_nums++ > 80 为 pass_nums >= 80
            if (red_nums >= RED_CONE_COUNT_TARGET) {
                pass_nums++;
                if (pass_nums >= RED_CONE_PASS_FRAMES) {
                    red_cone_finish = true;
                    ab_finish = false;  // 触发 AB 路段
                    ab_retry_count = 0;  // 重置 AB 重试计数
                    LOG_INFO("红锥绕行完成，进入 AB 路段检测");
                }
            }
        } 
        
        // ==================== AB 路段检测逻辑（关键修复点 2） ====================
        else if (red_cone_finish && !ab_finish) {
            gpio.setMotor(10800);
            ab_retry_count++;
            
            stringstream ss;
            ss << "AB 检测中... (重试计数: " << ab_retry_count << "/" << AB_RETRY_MAX << ")";
            LOG_DEBUG(ss.str());
            
            if (result.ab_result != -1) {
                // 成功获得 AB 结果
                gpio.setMotor(10000);
                this_thread::sleep_for(500ms);
                ab_finish = true;
                stringstream res_ss;
                res_ss << "AB 检测完成: " << (result.ab_result == 1 ? "A" : "B");
                LOG_INFO(res_ss.str());
            } 
            else if (ab_retry_count > AB_RETRY_MAX) {
                // ★ 关键修复：添加重试超时机制
                result.ab_result = AB_DEFAULT_CHOICE;  // 默认选择 B
                ab_finish = true;
                stringstream timeout_ss;
                timeout_ss << "AB 检测超时，使用默认选择: " 
                          << (result.ab_result == 1 ? "A" : "B");
                LOG_WARN(timeout_ss.str());
            }
        } 
        
        // ==================== 黄线检测和停车逻辑（关键修复点 3） ====================
        else if (ab_finish && !yellow_finish) {
            gpio.setMotor(10800);
            
            if (result.yellow_count >= YELLOW_DETECT_COUNT) {
                yellow_finish = true;
                LOG_INFO("检测到黄线，准备停车");
            }
        } 
        
        // ★ 关键修复：平滑制动逻辑，替代之前的直接 break
        if (yellow_finish) {
            static int brake_count = 0;
            brake_count++;
            
            if (brake_count < BRAKE_STEPS) {
                // 缓速阶段
                gpio.setMotor(BRAKE_SLOW_SPEED);
                stringstream brake_ss;
                brake_ss << "停车阶段 " << brake_count << "/" << BRAKE_STEPS;
                LOG_DEBUG(brake_ss.str());
            } else {
                // 完全停止
                gpio.setMotor(BRAKE_FINAL_SPEED);
                if (brake_count == BRAKE_STEPS) {
                    LOG_INFO("小车已安全停车！");
                }
            }
        }
        else {
            // 未进入任何特殊状态时保持标准速度
            gpio.setMotor(11000);
        }

        // 执行舵机控制
        gpio.setServo(angle);
        
        // 控制台输出调试信息
        if (ENABLE_STATS && frame_count % 10 == 0) {
            stringstream stat_ss;
            stat_ss << "中线: " << result.mid_line 
                   << ", 舵机角度: " << angle 
                   << ", 状态: "
                   << (yellow_finish ? "停车" : ab_finish ? "黄线" : red_cone_finish ? "AB检测" : "正常");
            LOG_DEBUG(stat_ss.str());
        }

        // ==================== 帧率控制 ====================
        // 保持稳定的 30 FPS
        this_thread::sleep_until(last_time + milliseconds(FRAME_DELAY_MS));
        last_time = steady_clock::now();
    }
    
    LOG_INFO("控制循环已退出");
}

ControlActuator::~ControlActuator() {
    LOG_INFO("ControlActuator 析构中...");
    stop_requested = true;
    result_cv.notify_all();  // 唤醒等待线程
    
    if (control_thread.joinable()) {
        control_thread.join();
    }
    
    // 确保电机停止
    gpio.setMotor(10000);
    gpio.setServo(SERVO_NEUTRAL);
    
    LOG_INFO("ControlActuator 已清理");
}
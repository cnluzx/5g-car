#ifndef CONTROL_ACTUATOR_H
#define CONTROL_ACTUATOR_H

#include "common.h"
#include "pid_controller.h"
#include "gpio_control.h"

/**
 * @class ControlActuator
 * @brief 控制执行器，管理车辆的状态机和运动控制
 * 
 * 职责：
 * - 管理车辆的多个工作状态（蓝牌→斑马→红锥→AB→黄线→停车）
 * - 根据图像处理结果计算控制指令
 * - 通过 PID 控制器调整舵机角度
 * - 控制电机速度，实现平滑加速/减速
 */
class ControlActuator {
private:
    // 控制线程
    std::thread control_thread;
    bool stop_requested = false;
    
    // 控制器实例
    PIDController pid;
    GPIOControl gpio;
    
    // 舵机角度限制
    double min_angle = 0, max_angle = 200;
    
    // ==================== 状态机变量 ====================
    
    // 蓝牌识别状态：是否已移除蓝牌
    bool blue_removed = false;
    
    // 斑马线状态：是否通过了斑马线
    bool has_banma = false;
    
    // 红锥绕行状态
    int red_nums = 0;           // 已检测到的红锥数量
    int pass_nums = 0;          // 通过的帧数计数
    bool red_cone_finish = false; // 红锥绕行是否完成
    
    // AB 路段状态
    int ab_retry_count = 0;     // AB 检测重试计数（新增）
    bool ab_finish = false;     // AB 路段是否完成
    
    // 黄线停车状态
    bool yellow_finish = false; // 是否进入停车阶段
    
    // 其他状态变量
    int landr_pass = 0;         // 左右检测计数

public:
    /**
     * @brief 构造函数，初始化控制器和启动控制线程
     */
    ControlActuator();
    
    /**
     * @brief 析构函数，停止控制线程并清理资源
     */
    ~ControlActuator();

private:
    /**
     * @brief 控制循环的主体函数
     * 
     * 在独立线程中运行，持续：
     * 1. 从结果队列获取图像处理结果
     * 2. 根据状态机更新控制命令
     * 3. 计算 PID 输出调整舵机和电机
     * 4. 保持恒定的帧率输出
     */
    void controlLoop();
};

#endif // CONTROL_ACTUATOR_H
#ifndef CONFIG_H
#define CONFIG_H

#include <iostream>

// ==================== GPIO 配置 ====================
// 电机和舵机的 GPIO 引脚号
const int MOTOR_PIN = 13;
const int SERVO_PIN = 12;

// ==================== PID 控制参数 ====================
// 比例增益系数
const double KP = 0.25;
// 微分增益系数
const double KD = 0.125;

// ==================== 舵机控制参数 ====================
// 舵机中性位置（0 度对应的 PWM 值）
const double SERVO_NEUTRAL = 100.0;
// 舵机最小角度（左转极限）
const double SERVO_MIN = 0.0;
// 舵机最大角度（右转极限）
const double SERVO_MAX = 200.0;
// 舵机 PWM 频率（Hz）
const int SERVO_PWM_FREQ = 50;
// 舵机 PWM 范围（用于 pigpio 的值）
const int SERVO_PWM_RANGE = 100;

// ==================== 电机控制参数 ====================
// 电机中性位置（停止）
const int MOTOR_NEUTRAL = 10000;
// 电机最小速度（反向最快）
const int MOTOR_MIN = 9500;
// 电机最大速度（正向最快）
const int MOTOR_MAX = 12000;
// 电机加速斜率（每 25ms 增加的 PWM 值）
const int MOTOR_ACCEL_STEP = 50;
// 电机加速延时（毫秒）
const int MOTOR_ACCEL_DELAY = 25;
// 电机 PWM 频率（Hz）
const int MOTOR_PWM_FREQ = 200;
// 电机 PWM 范围（用于 pigpio 的值）
const int MOTOR_PWM_RANGE = 40000;

// ==================== 检测和识别参数 ====================
// 斑马线检测：白色像素数阈值
const int ZEBRA_WHITE_PIXELS_THRESHOLD = 5000;
// 斑马线 Canny 边缘检测下限
const int ZEBRA_CANNY_LOW = 70;
// 斑马线 Canny 边缘检测上限
const int ZEBRA_CANNY_HIGH = 150;

// 红锥绕行：检测到 3 个红锥后需要持续 80 帧才能进入下一阶段
const int RED_CONE_COUNT_TARGET = 3;
const int RED_CONE_PASS_FRAMES = 80;

// AB 检测：最多重试 30 轮，超时后默认选择 B
const int AB_RETRY_MAX = 30;
const int AB_DEFAULT_CHOICE = 2;  // 2 代表 B

// 黄线检测：检测到 2 次黄线后开始停车
const int YELLOW_DETECT_COUNT = 2;

// ==================== 控制参数 ====================
// 图像处理目标帧率（fps）
const int TARGET_FPS = 30;
// 对应的延时时间（毫秒）
const int FRAME_DELAY_MS = 33;

// 中线偏移基准值（图像宽度的一半）
const double MIDLINE_CENTER = 160.0;
// 红锥左右调整偏移量
const int RED_CONE_OFFSET = 55;

// 停车阶段减速步数（分阶段降速）
const int BRAKE_STEPS = 10;
// 停车前速度
const int BRAKE_SLOW_SPEED = 10500;
// 停车完全停止速度
const int BRAKE_FINAL_SPEED = 10000;

// ==================== 外部工具和路径 ====================
// YOLO 检测脚本路径
const char* YOLO_SCRIPT_PATH = "/home/pi/g5g-new/yolo.py";
// YOLO 检测结果输出文件
const char* YOLO_RESULT_FILE = "res.txt";
// Python 解释器路径
const char* PYTHON_BIN = "/usr/local/bin/python3";

// ==================== 日志相关 ====================
// 是否启用调试日志输出
const bool ENABLE_DEBUG_LOG = true;
// 是否输出帧处理统计信息
const bool ENABLE_STATS = true;

#endif // CONFIG_H
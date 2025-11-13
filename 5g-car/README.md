<!-- 一些代码的阅读：
整体框架：
   g5g-car/
├── include/          # 头文件
│   ├── common.h      # 共享定义（如ProcessedFrame、mutex等）
│   ├── pid_controller.h
│   ├── gpio_control.h
│   ├── frame_capture.h
│   ├── image_processor.h
│   └── control_actuator.h
├── src/              # 源文件
│   ├── main.cpp
│   ├── pid_controller.cpp
│   ├── gpio_control.cpp
│   ├── frame_capture.cpp
│   ├── image_processor.cpp
│   └── control_actuator.cpp
├── image/            # 输出图像目录（从原代码继承）
│   ├── check/
│   ├── mid/
│   └── yellow/
├── Makefile          # 构建脚本
└── README.md         # 项目说明（添加运行、依赖）
### c++代码 
# G5G Refactored Autonomous Vehicle Project

## 依赖
- Raspberry Pi OS
- OpenCV4: `sudo apt install libopencv-dev`
- pigpio: `sudo apt install libpigpio-dev`
- Python3 (for YOLO): 确保 `/home/pi/g5g-new/yolo.py` 存在

## 构建与运行
1. 创建目录：`mkdir -p image/{check,mid,yellow}`
2. `make`
3. `./g5g_refactored`
4. Ctrl+C 停止

## 说明
- 多线程：捕获/处理/控制分离，提高FPS。
- 状态机：蓝牌 → 斑马 → 红锥 → AB → 黄线 → 停车。
- 输出：图像保存到 `image/` 子目录。
- 调试：监控控制台输出中线/角度/FPS。 -->

# 5G 自动驾驶小车项目

## 📋 项目概述

这是一个基于树莓派（Raspberry Pi）的自动驾驶比赛车项目，使用 OpenCV 进行视觉识别，通过 pigpio 库控制电机和舵机。车辆需要完成一条复杂的自动驾驶路线，涉及多个任务阶段。

### 项目特点

- **多线程架构**：图像捕获、处理、控制分离，充分利用多核 CPU
- **状态机设计**：清晰的任务流程，易于扩展和维护
- **PID 控制**：自适应舵机调节，实现精准循迹
- **实时调试**：完整的日志系统，便于问题追踪
- **鲁棒性强**：包含异常处理和重试机制

## 🚗 车辆路线说明

车辆需要依次完成以下任务：

```
蓝牌识别 → 斑马线通行 → 红锥绕行 → AB路段选择 → 黄线跟踪 → 自动停车
```

### 详细流程

| 阶段 | 说明 | 触发条件 | 输出 |
|------|------|---------|------|
| **蓝牌识别** | 识别并移除蓝色卡片 | 检测到蓝牌移除 | 开始前进 |
| **斑马线通行** | 通过斑马线区域 | 边缘检测识别条纹 | 继续运动 |
| **红锥绕行** | 左右交替绕行 3 个红锥 | 连续检测 3 个红锥 + 80 帧稳定性确认 | 进入 AB 检测 |
| **AB路段选择** | 通过 YOLO 判断走 A 路还是 B 路 | YOLO 检测成功或超时（默认 B） | 路径确定 |
| **黄线跟踪** | 跟踪黄色线条前进 | 检测到 2 条黄线 | 启动停车 |
| **自动停车** | 平滑减速至完全停止 | 黄线检测完成 | 车辆停止 |

## 📦 依赖和环境

### 系统要求

- **硬件**：Raspberry Pi 3B/4B 或更高版本
- **系统**：Raspberry Pi OS（基于 Debian）
- **Python 版本**：Python 3.7+

### 依赖包安装

```bash
# 更新包列表
sudo apt update && sudo apt upgrade -y

# 安装 OpenCV4
sudo apt install -y libopencv-dev

# 安装 pigpio 库（GPIO 控制）
sudo apt install -y libpigpio-dev

# 安装 Python3 及相关工具
sudo apt install -y python3 python3-pip

# 安装 YOLO（如果使用）
pip3 install torch torchvision ultralytics
# 或者
pip3 install yolov5
```

### 验证安装

```bash
# 检查 OpenCV 版本
pkg-config --modversion opencv4

# 检查 pigpio 库
dpkg -l | grep pigpio

# 检查 Python 版本
python3 --version
```

## 🔧 编译和运行

### 目录结构

```
5g-car/
├── include/                 # 头文件目录
│   ├── common.h            # 共享定义（数据结构、全局变量）
│   ├── config.h            # 参数配置（新增）
│   ├── debug.h             # 日志系统（新增）
│   ├── frame_capture.h     # 摄像头捕获
│   ├── image_processor.h   # 图像处理
│   ├── control_actuator.h  # 控制执行
│   ├── pid_controller.h    # PID 控制器
│   └── gpio_control.h      # GPIO 硬件控制
│
├── src/                    # 源文件目录
│   ├── main.cpp           # 主程序入口
│   ├── frame_capture.cpp  # 摄像头捕获实现
│   ├── image_processor.cpp # 图像处理实现
│   ├── control_actuator.cpp # 控制执行实现
│   ├── pid_controller.cpp  # PID 控制器实现
│   └── gpio_control.cpp    # GPIO 硬件控制实现
│
├── image/                 # 调试输出目录（运行时自动创建）
│   ├── check/            # 蓝牌检测图像
│   ├── mid/              # 中线检测图像
│   └── yellow/           # 黄线检测图像
│
├── Makefile              # 编译脚本
├── README.md            # 项目文档（本文件）
└── .gitignore          # Git 忽略文件列表（新增）
```

### 编译步骤

```bash
# 进入项目目录
cd 5g-car

# 创建输出目录
mkdir -p image/{check,mid,yellow}

# 编译项目
make

# 如果编译失败，尝试调试版本
make debug

# 清理编译文件
make clean
```

### 运行程序

```bash
# 普通运行
./g5g_refactored

# 通过 Makefile 运行（自动编译和创建目录）
make run

# 停止程序：按 Ctrl+C
```

## 🎛️ 参数调整指南

所有可配置参数都在 `include/config.h` 中集中管理，无需修改代码就可调整。

### 常用参数

**PID 参数**（影响转向精准度）：
```cpp
const double KP = 0.25;   // 比例系数（增大→反应快但易震荡）
const double KD = 0.125;  // 微分系数（增大→减弱震荡）
```

**电机速度**（影响前进速度）：
```cpp
const int MOTOR_NEUTRAL = 10000;  // 停止
const int MOTOR_MAX = 12000;      // 最大前进速度
```

**舵机范围**（影响转向角度）：
```cpp
const double SERVO_MIN = 0.0;     // 左转极限
const double SERVO_MAX = 180.0;   // 右转极限
const double SERVO_NEUTRAL = 100.0; // 中性位置
```

**检测阈值**：
```cpp
const int ZEBRA_WHITE_PIXELS_THRESHOLD = 5000;  // 斑马线
const int RED_CONE_COUNT_TARGET = 3;            // 红锥数量
const int RED_CONE_PASS_FRAMES = 80;            // 红锥稳定帧数
const int AB_RETRY_MAX = 30;                    // AB 重试次数
const int YELLOW_DETECT_COUNT = 2;              // 黄线检测数
```

## 🐛 调试和日志

### 启用调试日志

在 `config.h` 中修改：
```cpp
const bool ENABLE_DEBUG_LOG = true;   // 启用调试日志
const bool ENABLE_STATS = true;       // 启用统计信息
```

### 日志级别

程序使用四个日志级别，在 `debug.h` 中定义：

| 级别 | 宏定义 | 说明 | 示例 |
|------|--------|------|------|
| DEBUG | LOG_DEBUG(msg) | 详细调试信息 | 中线位置、舵机角度 |
| INFO | LOG_INFO(msg) | 重要信息 | 状态转移、初始化完成 |
| WARNING | LOG_WARN(msg) | 警告信息 | 检测失败、超时 |
| ERROR | LOG_ERROR(msg) | 错误信息 | 硬件故障、致命错误 |

### 输出目录说明

程序运行时会在 `image/` 目录下保存处理后的图像，用于离线调试：

```
image/check/   - 蓝牌检测的处理图像
image/mid/     - 中线检测的处理图像
image/yellow/  - 黄线检测的处理图像
```

### 实时监控

运行时在控制台输出类似信息：
```
[16:45:23.123] [INFO] 5G 自动驾驶小车程序启动
[16:45:23.456] [INFO] 启动工作线程...
[16:45:23.789] [DBUG] 捕获统计: 已捕获 30 帧, 实际 FPS: 29.8
[16:45:24.012] [DBUG] 处理统计: 已处理 30 帧, 中线: 158, 红锥: -1, 黄线计数: 0
```

## 🔄 工作原理

### 三线程架构

```
┌─────────────────────────────────────────────────────┐
│                    主线程                            │
│            （监控、定期输出统计信息）                  │
└─────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
    ┌─────────┐      ┌──────────────┐   ┌──────────────┐
    │   捕获   │      │  图像处理     │   │  控制执行     │
    │  线程    │      │  线程        │   │  线程        │
    │ ~30FPS  │      │              │   │              │
    └────┬────┘      └──────┬───────┘   └──────┬───────┘
         │                  │                  │
         └─→ frame_queue ─→ │                  │
                           │                  │
              └─→ result_queue ──────────────→ │
                                               │
                               ↓────→ GPIO ─→ 电机/舵机
```

### 数据流向

1. **FrameCapture 线程**：
   - 读取摄像头画面（~30 FPS）
   - 将 Mat 对象推入 frame_queue

2. **ImageProcessor 线程**：
   - 从 frame_queue 获取图像
   - 执行颜色识别、边缘检测、YOLO 推理等
   - 构建 ProcessedFrame 结果对象
   - 将结果推入 result_queue

3. **ControlActuator 线程**：
   - 从 result_queue 获取处理结果
   - 运行状态机，判断当前阶段
   - 计算 PID 输出，控制舵机和电机

4. **主线程**：
   - 创建上述三个线程对象
   - 定期监控程序状态（可选）
   - 等待 Ctrl+C 信号后优雅关闭

### 同步机制

- **互斥锁 (mutex)**：保护 frame_queue 和 result_queue
- **条件变量 (condition_variable)**：线程间的高效通知

## 📊 已知问题与改进方向

### ✅ 已修复（v2.0）

- [x] 红锥计数逻辑错误（pass_nums++ > 80 → pass_nums >= 80）
- [x] AB 检测缺乏重试机制（新增 ab_retry_count）
- [x] 停车逻辑不完善（新增平滑制动流程）
- [x] 缺少日志系统（新增 debug.h）
- [x] 缺少参数管理（新增 config.h）

### ⚠️ 待改进

- [ ] 图像处理算法可进一步优化（深度学习加速）
- [ ] 多线程同步可使用 lock-free 数据结构
- [ ] 加入 IMU 传感器增强定位精度
- [ ] 实现自适应参数调整（机器学习）
- [ ] 添加网络通信模块（远程监控）

## 📝 编码规范

### 代码风格

- **缩进**：4 个空格
- **命名**：camelCase 用于变量和函数，PascalCase 用于类
- **注释**：为复杂逻辑添加注释，函数添加 Doxygen 格式文档

### 提交规范

```bash
# 修复 Bug
git commit -m "fix: 修复红锥计数逻辑"

# 新增功能
git commit -m "feat: 添加日志系统"

# 文档更新
git commit -m "docs: 更新 README"
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。

## 📄 许可证

[待补充]

## 📧 联系方式

[待补充]

---

**最后更新**：2025 年 11 月 13 日
**版本**：v2.0 (修复版本)
一些代码的阅读：
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
- 调试：监控控制台输出中线/角度/FPS。

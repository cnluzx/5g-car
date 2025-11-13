#include "smartcar.h"
#include <iostream>

namespace smartcar {
    // 全局变量定义
    cv::Mat frameToProcess;
    int findab = 0;
    int find_blue_card = 0;
    int blue_card_remove_flag = 0;
    int hasBanma = 1;
    int Banma_finish = 1;
    int red_nums = 0;
    double res_y = 240.0;
    int num_yellow = 0;
    int flag_yellow = 0;
    std::vector<cv::Point> left_line;
    std::vector<cv::Point> right_line;

    SmartCar::SmartCar() {
        // 构造函数
    }

    SmartCar::~SmartCar() {
        // 析构函数
    }

    void SmartCar::initialize() {
        // GPIO初始化
        if (gpioInitialise() < 0) {
            std::cerr << "GPIO initialization failed" << std::endl;
            exit(1);
        }
        
        // 设置GPIO模式
        gpioSetMode(13, PI_OUTPUT);  // 电机
        gpioSetMode(12, PI_OUTPUT);  // 舵机
        
        // 设置PWM参数
        gpioSetPWMrange(13, 40000);
        gpioSetPWMfrequency(13, 200);
        gpioSetPWMrange(12, 30000);
        gpioSetPWMfrequency(12, 50);
        
        // 初始化电机和舵机
        gpioPWM(13, 10000);
        gpioPWM(12, 1565);
    }

    void SmartCar::processFrame() {
        // 图像处理逻辑
        if (frameToProcess.empty()) return;
        
        // 1. 蓝色卡片检测
        if (find_blue_card) {
            // 蓝色卡片处理逻辑
        }
        
        // 2. 红色锥桶检测
        if (red_nums > 0) {
            // 红色锥桶处理逻辑
        }
        
        // 3. 黄色边缘检测
        if (flag_yellow) {
            // 黄色边缘处理逻辑
        }
        
        // 4. 跑道检测
        // 跑道检测逻辑
    }

    void SmartCar::controlMotors() {
        // PID控制参数
        double kp = 0.25;
        double ki = 0.00;
        double kd = 0.125;
        static double last_error = 0;
        
        // 计算误差
        double error = res_y - 120.0;
        
        // PID计算
        double angle = kp * error + kd * (error - last_error);
        last_error = error;
        
        // 控制舵机
        int servo_value = 1565 + (int)(angle * 10);
        gpioPWM(12, servo_value);
        
        // 控制电机
        if (Banma_finish) {
            gpioPWM(13, 10800);  // 停止
        } else {
            gpioPWM(13, 12000);  // 前进
        }
    }

    void SmartCar::run() {
        cv::VideoCapture cap(0);
        if (!cap.isOpened()) {
            std::cerr << "Cannot open camera" << std::endl;
            return;
        }
        
        while (true) {
            cap >> frameToProcess;
            if (frameToProcess.empty()) break;
            
            processFrame();
            controlMotors();
            
            // 显示处理后的图像
            cv::imshow("Frame", frameToProcess);
            if (cv::waitKey(1) == 27) break;  // ESC键退出
        }
        
        cap.release();
        cv::destroyAllWindows();
    }
}

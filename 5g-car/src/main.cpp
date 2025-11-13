#include "../include/common.h"
#include "../include/frame_capture.h"
#include "../include/image_processor.h"
#include "../include/control_actuator.h"
#include "../include/debug.h"
#include <iostream>
#include <csignal>
#include <thread>
#include <chrono>

using namespace std;
using namespace chrono;

// 全局变量（在 common.h 中声明，这里定义）
queue<cv::Mat> frame_queue;
queue<ProcessedFrame> result_queue;
mutex frame_mutex;
mutex result_mutex;
condition_variable frame_cv;
condition_variable result_cv;
bool running = true;

/**
 * @brief 信号处理函数，用于优雅关闭程序
 * @param signum 收到的信号号
 */
void signalHandler(int signum) {
    stringstream ss;
    ss << "收到中断信号 (" << signum << ")，准备关闭...";
    LOG_INFO(ss.str());
    running = false;
    frame_cv.notify_all();
    result_cv.notify_all();
}

/**
 * @brief 主程序入口
 * 
 * 启动三个工作线程：
 * 1. FrameCapture - 摄像头捕获线程（~30 FPS）
 * 2. ImageProcessor - 图像处理线程（处理所有捕获的帧）
 * 3. ControlActuator - 控制执行线程（根据结果控制电机和舵机）
 * 
 * 主线程作为监控线程，定期检查程序状态
 */
int main() {
    LOG_INFO("========================================");
    LOG_INFO("5G 自动驾驶小车程序启动");
    LOG_INFO("========================================");
    
    // 注册信号处理函数，用于优雅关闭
    signal(SIGINT, signalHandler);
    
    try {
        LOG_INFO("启动工作线程...");
        
        // 启动三个核心线程
        FrameCapture capturer;          // 线程 1：图像捕获
        ImageProcessor processor;       // 线程 2：图像处理
        ControlActuator actuator;       // 线程 3：控制执行
        
        LOG_INFO("所有线程已启动，程序开始运行");
        LOG_INFO("按 Ctrl+C 停止程序");
        
        // 主线程：作为监控线程
        // 定期检查程序状态，可以添加统计信息输出
        int monitor_count = 0;
        while (running) {
            this_thread::sleep_for(100ms);
            monitor_count++;
            
            // 每 10 秒输出一次统计信息
            if (ENABLE_STATS && monitor_count % 100 == 0) {
                stringstream stats_ss;
                stats_ss << "帧队列大小: " << frame_queue.size() 
                        << ", 结果队列大小: " << result_queue.size();
                LOG_DEBUG(stats_ss.str());
            }
        }
        
        LOG_INFO("主循环已退出");
        this_thread::sleep_for(500ms);  // 给各线程清理的时间
        
    } catch (const exception& e) {
        LOG_ERROR(string("程序异常: ") + e.what());
        running = false;
        return 1;
    } catch (...) {
        LOG_ERROR("发生未知异常");
        running = false;
        return 1;
    }
    
    LOG_INFO("========================================");
    LOG_INFO("5G 自动驾驶小车程序已关闭");
    LOG_INFO("========================================");
    
    return 0;
}
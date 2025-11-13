#include "../include/frame_capture.h"
#include "../include/debug.h"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <sstream>

using namespace std;
using namespace cv;
using namespace chrono;

FrameCapture::FrameCapture() : cap(0) {
    LOG_INFO("FrameCapture 初始化中...");
    
    // 打开摄像头（ID 为 0，即默认摄像头）
    if (!cap.isOpened()) {
        LOG_ERROR("摄像头打开失败！请检查摄像头连接和驱动");
        running = false;
        return;
    }
    
    // 设置摄像头参数
    cap.set(CAP_PROP_FRAME_WIDTH, 320);   // 宽度
    cap.set(CAP_PROP_FRAME_HEIGHT, 240);  // 高度
    cap.set(CAP_PROP_FPS, 30);             // 帧率
    
    // 启动捕获线程
    capture_thread = thread(&FrameCapture::captureLoop, this);
    
    LOG_INFO("FrameCapture 初始化完成，捕获线程已启动");
}

void FrameCapture::captureLoop() {
    LOG_INFO("图像捕获循环已启动");
    
    Mat frame;
    int frame_count = 0;
    auto start_time = steady_clock::now();
    
    while (running && !stop_requested) {
        if (!cap.read(frame)) {
            LOG_WARN("读取摄像头画面失败");
            this_thread::sleep_for(chrono::milliseconds(100));
            continue;
        }
        
        if (frame.empty()) {
            LOG_WARN("获取到空白画面");
            continue;
        }
        
        // 将帧推入队列供处理线程使用
        {
            unique_lock<mutex> lock(frame_mutex);
            frame_queue.push(frame);
            frame_cv.notify_one();  // 通知处理线程有新数据
        }
        
        frame_count++;
        
        // 每 30 帧输出一次统计信息
        if (frame_count % 30 == 0 && ENABLE_STATS) {
            auto now = steady_clock::now();
            auto elapsed = duration_cast<milliseconds>(now - start_time).count();
            double fps = frame_count * 1000.0 / elapsed;
            
            stringstream ss;
            ss << "捕获统计: 已捕获 " << frame_count << " 帧, 实际 FPS: " << fps;
            LOG_DEBUG(ss.str());
        }
        
        // 控制帧率，目标 30 FPS
        this_thread::sleep_for(chrono::milliseconds(33));
    }
    
    LOG_INFO("图像捕获循环已退出");
}

FrameCapture::~FrameCapture() {
    LOG_INFO("FrameCapture 析构中...");
    stop_requested = true;
    
    if (capture_thread.joinable()) {
        capture_thread.join();
    }
    
    cap.release();
    
    LOG_INFO("FrameCapture 已清理");
}
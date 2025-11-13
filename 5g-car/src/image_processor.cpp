#include "../include/image_processor.h"
#include "../include/config.h"
#include "../include/debug.h"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <fstream>
#include <sstream>
#include <chrono>

using namespace std;
using namespace cv;
using namespace chrono;

ImageProcessor::ImageProcessor() {
    LOG_INFO("ImageProcessor 初始化中...");
    process_thread = thread(&ImageProcessor::processLoop, this);
    LOG_INFO("ImageProcessor 初始化完成，处理线程已启动");
}

void ImageProcessor::processLoop() {
    LOG_INFO("图像处理循环已启动");
    
    Mat frame;
    int frame_count = 0;
    
    while (running && !stop_requested) {
        {
            unique_lock<mutex> lock(frame_mutex);
            frame_cv.wait(lock, [&] { return !frame_queue.empty() || !running; });
            if (!frame_queue.empty()) {
                frame = move(frame_queue.front());
                frame_queue.pop();
            } else {
                continue;
            }
        }

        frame_count++;
        
        // 处理图像，提取所有特征
        ProcessedFrame result;
        
        // 1. 检测蓝牌（假设有相应的检测函数）
        result.blue_card_removed = detectBlueCard(frame);
        
        // 2. 检测斑马线
        result.zebra_crossing = detectZebra(frame);
        
        // 3. 检测中线位置
        result.mid_line = detectMidLine(frame);
        
        // 4. 检测红锥位置
        result.red_cone_pos = detectRedCone(frame);
        
        // 5. 检测黄线数量
        result.yellow_count = detectYellow(frame);
        
        // 6. 调用 YOLO 进行 AB 检测
        result.ab_result = callYoloAB();
        
        // 推入结果队列
        {
            unique_lock<mutex> lock(result_mutex);
            result_queue.push(move(result));
            result_cv.notify_one();
        }
        
        // 定期输出统计信息
        if (frame_count % 30 == 0 && ENABLE_STATS) {
            stringstream ss;
            ss << "处理统计: 已处理 " << frame_count << " 帧, "
               << "中线: " << result.mid_line 
               << ", 红锥: " << result.red_cone_pos
               << ", 黄线计数: " << result.yellow_count;
            LOG_DEBUG(ss.str());
        }
    }
    
    LOG_INFO("图像处理循环已退出");
}

bool ImageProcessor::detectBlueCard(const Mat& frame) {
    // 蓝牌检测逻辑（具体实现）
    // 返回是否检测到蓝牌被移除
    return false;  // 默认返回
}

bool ImageProcessor::detectZebra(const Mat& frame) {
    Mat gray, edges;
    cvtColor(frame, gray, COLOR_BGR2GRAY);
    GaussianBlur(gray, gray, Size(5, 5), 0);
    Canny(gray, edges, ZEBRA_CANNY_LOW, ZEBRA_CANNY_HIGH);
    
    int white_pixels = countNonZero(edges);
    bool detected = white_pixels > ZEBRA_WHITE_PIXELS_THRESHOLD;
    
    if (detected) {
        LOG_DEBUG("斑马线检测: 是");
    }
    
    return detected;
}

double ImageProcessor::detectMidLine(const Mat& frame) {
    // 中线检测逻辑（具体实现）
    // 返回中线位置（像素坐标）
    return 160.0;  // 默认中心
}

int ImageProcessor::detectRedCone(const Mat& frame) {
    // 红锥检测逻辑（具体实现）
    // 返回红锥位置，-1 表示未检测到
    return -1;
}

int ImageProcessor::detectYellow(const Mat& frame) {
    // 黄线检测逻辑（具体实现）
    // 返回检测到的黄线数量
    return 0;
}

int ImageProcessor::callYoloAB() {
    // 调用 YOLO 脚本进行 AB 检测
    stringstream cmd;
    cmd << PYTHON_BIN << " " << YOLO_SCRIPT_PATH << " > " << YOLO_RESULT_FILE;
    
    int ret = system(cmd.str().c_str());
    if (ret != 0) {
        LOG_WARN("YOLO 脚本执行失败");
        return -1;
    }
    
    // 读取结果文件
    ifstream file(YOLO_RESULT_FILE);
    string line;
    if (file.is_open() && getline(file, line)) {
        try {
            int result = stoi(line);
            stringstream result_ss;
            result_ss << "YOLO AB 检测结果: " << (result == 1 ? "A" : "B");
            LOG_DEBUG(result_ss.str());
            return result;
        } catch (...) {
            LOG_WARN("无法解析 YOLO 结果");
            return -1;
        }
    }
    
    return -1;
}

ImageProcessor::~ImageProcessor() {
    LOG_INFO("ImageProcessor 析构中...");
    stop_requested = true;
    
    if (process_thread.joinable()) {
        process_thread.join();
    }
    
    LOG_INFO("ImageProcessor 已清理");
}
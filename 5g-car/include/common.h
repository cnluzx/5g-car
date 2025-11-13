#ifndef COMMON_H
#define COMMON_H

#include <opencv2/opencv.hpp>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <chrono>
#include <signal.h>
#include <iostream>

using namespace cv;
using namespace std;
using namespace std::chrono;

// 共享结构体：处理后的帧数据
struct ProcessedFrame {
    Mat binary_edges;       // 二值化边缘图像，用于跟踪
    double mid_line = 160.0; // 中线x坐标
    int red_cone_pos = -1;   // 红锥桶位置（-1表示无）
    bool blue_card_detected = false;
    bool blue_card_removed = false;
    bool zebra_crossing = false;
    bool zebra_finished = true;
    int ab_result = -1;      // YOLO AB结果
    bool yellow_detected = false;
    int yellow_count = 0;
};

// 共享队列和同步
extern queue<Mat> frame_queue;                    // 原始帧队列
extern queue<ProcessedFrame> result_queue;        // 处理结果队列
extern mutex frame_mutex;
extern mutex result_mutex;
extern condition_variable frame_cv;
extern condition_variable result_cv;
extern bool running;

// 信号处理
void signalHandler(int signum);

#endif // COMMON_H
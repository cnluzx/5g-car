#pragma once
#include <opencv2/opencv.hpp>
#include <pigpio.h>
#include <vector>
#include <string>

namespace smartcar {
    // 全局变量
    extern cv::Mat frameToProcess;
    extern int findab;
    extern int find_blue_card;
    extern int blue_card_remove_flag;
    extern int hasBanma;
    extern int Banma_finish;
    extern int red_nums;
    extern double res_y;
    extern int num_yellow;
    extern int flag_yellow;
    extern std::vector<cv::Point> left_line;
    extern std::vector<cv::Point> right_line;

    // 核心功能类
    class SmartCar {
    public:
        SmartCar();
        ~SmartCar();
        void initialize();
        void run();
    private:
        void processFrame();
        void controlMotors();
    };
}

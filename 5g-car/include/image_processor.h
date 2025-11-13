#ifndef IMAGE_PROCESSOR_H
#define IMAGE_PROCESSOR_H

#include "common.h"
#include "pid_controller.h"

class ImageProcessor {
private:
    thread process_thread;
    bool stop_requested = false;
    PIDController pid;  // 未直接使用，但可扩展

public:
    ImageProcessor();
    ~ImageProcessor();
private:
    void processLoop();
    bool detectBlueCard(const Mat& frame);
    int detectRedCone(const Mat& frame);
    bool detectYellow(const Mat& frame, int& count);
    bool detectZebra(const Mat& frame);
    int callYoloAB();
    double trackMidLine(const Mat& binary);
    Mat processEdges(const Mat& frame);
};

#endif // IMAGE_PROCESSOR_H
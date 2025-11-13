#ifndef FRAME_CAPTURE_H
#define FRAME_CAPTURE_H

#include "common.h"

class FrameCapture {
private:
    cv::VideoCapture cap;
    thread capture_thread;
    bool stop_requested = false;

public:
    FrameCapture();
    ~FrameCapture();
private:
    void captureLoop();
};

#endif // FRAME_CAPTURE_H
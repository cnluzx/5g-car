#include "../include/frame_capture.h"
#include "../include/common.h"

FrameCapture::FrameCapture() {
    cap.open(0);  // 摄像头索引
    if (!cap.isOpened()) {
        cerr << "Error: Could not open video source." << endl;
        exit(1);
    }
    cap.set(CAP_PROP_FRAME_WIDTH, 320);
    cap.set(CAP_PROP_FRAME_HEIGHT, 240);
    capture_thread = thread(&FrameCapture::captureLoop, this);
}

void FrameCapture::captureLoop() {
    while (!stop_requested && running) {
        Mat frame;
        cap >> frame;
        if (frame.empty()) continue;

        {
            unique_lock<mutex> lock(frame_mutex);
            if (frame_queue.size() < 5) {  // 限队列大小防积压
                frame_queue.push(frame.clone());
                frame_cv.notify_one();
            }
        }
        this_thread::sleep_for(33ms);  // ~30 FPS
    }
}

FrameCapture::~FrameCapture() {
    stop_requested = true;
    if (capture_thread.joinable()) capture_thread.join();
    cap.release();
}
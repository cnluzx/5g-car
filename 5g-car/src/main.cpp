#include "../include/common.h"
#include "../include/frame_capture.h"
#include "../include/image_processor.h"
#include "../include/control_actuator.h"

queue<Mat> frame_queue;
queue<ProcessedFrame> result_queue;
mutex frame_mutex;
mutex result_mutex;
condition_variable frame_cv;
condition_variable result_cv;
bool running = true;

void signalHandler(int signum) {
    cout << "Interrupt signal (" << signum << ") received.\n";
    running = false;
    frame_cv.notify_all();
    result_cv.notify_all();
}

int main() {
    signal(SIGINT, signalHandler);

    // 启动线程
    FrameCapture capturer;
    ImageProcessor processor;
    ControlActuator actuator;

    // 主线程：监控（可加FPS计算）
    while (running) {
        this_thread::sleep_for(100ms);
    }

    return 0;
}
// g5g_refactored.cpp
// Refactored version: Simplified structure using classes for modularity.
// Multithreading: Separate threads for frame capture, image processing, and control actuation.
// Uses std::queue for frame passing, mutex/condition_variable for synchronization.
// Global variables minimized; state managed in classes.
// Assumes Raspberry Pi environment with pigpio, OpenCV4, etc.
// Compile with: g++ -std=c++17 -O2 -o g5g_refactored g5g_refactored.cpp `pkg-config --cflags --libs opencv4` -lpigpio -lpthread -lopenal

#include <opencv2/opencv.hpp>
#include <pigpio.h>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <queue>
#include <chrono>
#include <signal.h>
#include <iostream>
#include <fstream>
#include <cstdlib>
#include <vector>
#include <cmath>

using namespace cv;
using namespace std;
using namespace std::chrono;

// Forward declarations
class FrameCapture;
class ImageProcessor;
class ControlActuator;

// Shared data structures
struct ProcessedFrame {
    Mat binary_edges;  // Processed binary image for tracking
    double mid_line = 160.0;  // Midline x-coordinate
    int red_cone_pos = -1;    // Red cone position (-1 if none)
    bool blue_card_detected = false;
    bool blue_card_removed = false;
    bool zebra_crossing = false;
    bool zebra_finished = true;
    int ab_result = -1;       // YOLO AB result
    bool yellow_detected = false;
    int yellow_count = 0;
};

queue<Mat> frame_queue;  // Incoming raw frames
queue<ProcessedFrame> result_queue;  // Processed results
mutex frame_mutex;
mutex result_mutex;
condition_variable frame_cv;
condition_variable result_cv;
bool running = true;

// Signal handler
void signalHandler(int signum) {
    cout << "Interrupt signal (" << signum << ") received.\n";
    running = false;
    frame_cv.notify_all();
    result_cv.notify_all();
}

// PID Controller Class
class PIDController {
private:
    double kp = 0.25;
    double kd = 0.125;
    double last_error = 0.0;

public:
    double compute(double error) {
        double derivative = error - last_error;
        last_error = error;
        return kp * error + kd * derivative;
    }
};

// GPIO Control Class (simplified)
class GPIOControl {
private:
    int motor_pin = 13;
    int servo_pin = 12;
    int last_dian = 10000;

public:
    void init() {
        if (gpioInitialise() < 0) exit(1);
        gpioSetMode(motor_pin, PI_OUTPUT);
        gpioSetPWMrange(motor_pin, 40000);
        gpioSetPWMfrequency(motor_pin, 200);
        gpioSetMode(servo_pin, PI_OUTPUT);
        gpioSetPWMrange(servo_pin, 30000);
        gpioSetPWMfrequency(servo_pin, 50);
        gpioPWM(motor_pin, 10000);  // Stop motor
        setServo(156.5);
    }

    void setMotor(int value) {
        if (value > 10800) {
            for (int i = max(10800, last_dian); i <= value; i += 50) {
                gpioPWM(motor_pin, min(i, value));
                this_thread::sleep_for(25ms);
            }
        } else {
            gpioPWM(motor_pin, value);
        }
        last_dian = value;
    }

    void setServo(double angle) {
        double value = (0.5 + (2 / 270.0) * angle) / 20 * 30000;
        cout << "Servo value: " << value << "\n";
        gpioPWM(servo_pin, value);
    }

    ~GPIOControl() {
        gpioTerminate();
    }
};

// Frame Capture Thread Class
class FrameCapture {
private:
    VideoCapture cap;
    thread capture_thread;
    bool stop_requested = false;

public:
    FrameCapture() {
        cap.open(2);  // Camera index
        if (!cap.isOpened()) {
            cerr << "Error: Could not open video source." << endl;
            exit(1);
        }
        cap.set(CAP_PROP_FRAME_WIDTH, 320);
        cap.set(CAP_PROP_FRAME_HEIGHT, 240);
        capture_thread = thread(&FrameCapture::captureLoop, this);
    }

    void captureLoop() {
        while (!stop_requested && running) {
            Mat frame;
            cap >> frame;
            if (frame.empty()) continue;

            {
                unique_lock<mutex> lock(frame_mutex);
                if (frame_queue.size() < 5) {  // Limit queue size to prevent backlog
                    frame_queue.push(frame.clone());
                    frame_cv.notify_one();
                }
            }
            this_thread::sleep_for(33ms);  // ~30 FPS cap
        }
    }

    ~FrameCapture() {
        stop_requested = true;
        if (capture_thread.joinable()) capture_thread.join();
        cap.release();
    }
};

// Image Processing Thread Class (combines all detections)
class ImageProcessor {
private:
    thread process_thread;
    bool stop_requested = false;
    PIDController pid;  // Not used here, but could be for future

    // Simplified blue card detection
    bool detectBlueCard(const Mat& frame) {
        Mat hsv;
        cvtColor(frame, hsv, COLOR_BGR2HSV);
        Scalar lower_blue(100, 50, 50);
        Scalar upper_blue(130, 255, 255);
        Mat mask;
        inRange(hsv, lower_blue, upper_blue, mask);
        int area = countNonZero(mask);
        return area > 60000;  // Threshold for detection
    }

    // Simplified red cone detection
    int detectRedCone(const Mat& frame) {
        Mat roi = frame(Rect(0, frame.rows * 0.55, frame.cols, frame.rows * 0.35));
        Mat hsv;
        cvtColor(roi, hsv, COLOR_BGR2HSV);
        Mat mask1, mask2, mask;
        inRange(hsv, Scalar(0, 43, 46), Scalar(10, 255, 255), mask1);
        inRange(hsv, Scalar(153, 43, 46), Scalar(180, 255, 255), mask2);
        mask = mask1 | mask2;
        Mat kernel = getStructuringElement(MORPH_RECT, Size(3, 3));
        erode(mask, mask, kernel);
        dilate(mask, mask, kernel);
        vector<vector<Point>> contours;
        findContours(mask, contours, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE);
        if (contours.empty() || contours[0].size() < 5) return -1;
        Rect bbox = boundingRect(contours[0]);
        if (bbox.height > 5 && bbox.height < 100) {
            return bbox.x + (bbox.width / 2);  // Center x
        }
        return -1;
    }

    // Simplified yellow line detection
    bool detectYellow(const Mat& frame, int& count) {
        Mat hsv;
        cvtColor(frame, hsv, COLOR_BGR2HSV);
        Scalar lower_yellow(20, 20, 20);
        Scalar upper_yellow(34, 255, 255);
        Mat mask;
        inRange(hsv, lower_yellow, upper_yellow, mask);
        Mat roi = mask(Rect(0, frame.rows * 0.7, frame.cols, frame.rows * 0.2));
        int pixels = countNonZero(roi);
        if (pixels > 1000) {
            count++;
            return count >= 2;
        }
        return false;
    }

    // Simplified zebra crossing (placeholder: use edge detection)
    bool detectZebra(const Mat& frame) {
        Mat gray, edges;
        cvtColor(frame, gray, COLOR_BGR2GRAY);
        GaussianBlur(gray, gray, Size(5, 5), 0);
        Canny(gray, edges, 70, 150);
        int white_pixels = countNonZero(edges);
        return white_pixels > 5000;  // Simple threshold
    }

    // YOLO AB (simplified call)
    int callYoloAB() {
        system("/usr/local/bin/python3 /home/pi/g5g-new/yolo.py > res.txt");
        ifstream file("res.txt");
        string line;
        if (file.is_open() && getline(file, line)) {
            return stoi(line);
        }
        return -1;
    }

    // Line tracking on binary edges
    double trackMidLine(const Mat& binary) {
        vector<Point> left, right, mid;
        int rows = binary.rows, cols = binary.cols;
        int begin = 160;
        for (int i = rows - 1; i >= rows / 2; --i) {
            int to_left = begin;
            while (to_left > 1 && !(binary.at<uchar>(i, to_left) == 255 && binary.at<uchar>(i, to_left + 1) == 255)) --to_left;
            left.emplace_back(to_left > 1 ? to_left : 1, i);

            int to_right = begin;
            while (to_right < cols - 1 && !(binary.at<uchar>(i, to_right) == 255 && binary.at<uchar>(i, to_right - 2) == 255)) ++to_right;
            right.emplace_back(to_right < cols - 1 ? to_right : cols - 1, i);

            if (left.back().x > 1 && right.back().x < cols - 1) {
                mid.emplace_back((left.back().x + right.back().x) / 2, i);
            }
            begin = (to_left + to_right) / 2;
        }
        if (mid.empty()) return 160.0;
        double sum = 0;
        size_t size = min(mid.size(), mid.size() / 2 + 5);
        for (size_t j = mid.size() / 2; j < size; ++j) {
            sum += mid[j].x;
        }
        return sum / (size - mid.size() / 2);
    }

    // Binary edge processing (Hough simplified)
    Mat processEdges(const Mat& frame) {
        Mat gray, edges;
        cvtColor(frame, gray, COLOR_BGR2GRAY);
        GaussianBlur(gray, gray, Size(5, 5), 0);
        Canny(gray, edges, 70, 150);
        // Simple ROI mask
        Mat mask = Mat::zeros(edges.size(), CV_8UC1);
        vector<Point> poly = {{0, edges.rows}, {edges.cols, edges.rows}, {edges.cols, edges.rows * 0.5}, {0, edges.rows * 0.5}};
        fillPoly(mask, {poly}, 255);
        Mat roi_edges;
        bitwise_and(edges, mask, roi_edges);
        // Simple Hough (no full impl, use tracking instead)
        return roi_edges;  // Return masked edges for tracking
    }

public:
    ImageProcessor() {
        process_thread = thread(&ImageProcessor::processLoop, this);
    }

    void processLoop() {
        static int blue_remove_count = 0;
        static int yellow_count = 0;
        static int red_count = 0;
        static bool zebra_start = false;
        static bool ab_done = false;
        static bool yellow_done = false;

        while (!stop_requested && running) {
            Mat frame;
            {
                unique_lock<mutex> lock(frame_mutex);
                frame_cv.wait(lock, [&] { return !frame_queue.empty() || !running; });
                if (!frame_queue.empty()) {
                    frame = move(frame_queue.front());
                    frame_queue.pop();
                } else continue;
            }

            ProcessedFrame result;
            result.binary_edges = processEdges(frame);

            // Sequential detections (optimized by ROI where possible)
            result.mid_line = trackMidLine(result.binary_edges);
            result.red_cone_pos = detectRedCone(frame);
            result.blue_card_detected = detectBlueCard(frame);
            result.yellow_detected = detectYellow(frame, yellow_count);
            result.zebra_crossing = detectZebra(frame);

            // State machine logic (simplified from original)
            if (result.blue_card_detected && blue_remove_count < 3) {
                blue_remove_count++;
            } else if (!result.blue_card_detected && blue_remove_count >= 3) {
                result.blue_card_removed = true;
                blue_remove_count = 0;
            }

            if (result.zebra_crossing && !zebra_start) {
                zebra_start = true;
                result.zebra_finished = false;
            } else if (!result.zebra_crossing && zebra_start) {
                result.zebra_finished = true;
                zebra_start = false;
            }

            if (result.red_cone_pos != -1) red_count++;
            if (result.yellow_detected) yellow_done = true;

            if (!ab_done && red_count >= 3) {
                result.ab_result = callYoloAB();
                if (result.ab_result != -1) ab_done = true;
            }

            result.yellow_count = yellow_count;
            yellow_count = result.yellow_detected ? yellow_count + 1 : 0;

            {
                unique_lock<mutex> lock(result_mutex);
                if (result_queue.size() < 5) {
                    result_queue.push(move(result));
                    result_cv.notify_one();
                }
            }
        }
    }

    ~ImageProcessor() {
        stop_requested = true;
        if (process_thread.joinable()) process_thread.join();
    }
};

// Control Actuator Thread Class
class ControlActuator {
private:
    thread control_thread;
    bool stop_requested = false;
    PIDController pid;
    GPIOControl gpio;
    double min_angle = 0, max_angle = 200;
    int red_nums = 0, pass_nums = 0;
    bool change_dao_finish = false, red_cone_finish = false, ab_finish = false, yellow_finish = false;
    int landr_pass = 0;

public:
    ControlActuator() : gpio() {
        gpio.init();
        control_thread = thread(&ControlActuator::controlLoop, this);
    }

    void controlLoop() {
        auto last_time = steady_clock::now();
        while (!stop_requested && running) {
            ProcessedFrame result;
            {
                unique_lock<mutex> lock(result_mutex);
                result_cv.wait(lock, [&] { return !result_queue.empty() || !running; });
                if (!result_queue.empty()) {
                    result = move(result_queue.front());
                    result_queue.pop();
                } else continue;
            }

            // State machine (simplified)
            static bool blue_removed = false, has_banma = true;

            if (!blue_removed && result.blue_card_removed) {
                blue_removed = true;
                cout << "Blue card removed, starting motion.\n";
            }

            if (blue_removed && !has_banma) {
                has_banma = result.zebra_crossing;
                if (has_banma) cout << "Zebra crossing detected.\n";
            }

            double error = 160.0 - result.mid_line;
            if (ab_finish) error = 160.0 - (result.mid_line + 40);  // Adjust for parking

            double angle_adjust = pid.compute(error);
            double angle = 156.5 + angle_adjust;
            angle = max(min(angle, max_angle), min_angle);

            if (result.red_cone_pos != -1 && !red_cone_finish) {
                gpio.setMotor(11000);
                if (red_nums % 2 == 1) error = 160 - (result.red_cone_pos - 55);
                else error = 160 - (result.red_cone_pos + 55);
                angle_adjust = pid.compute(error);
                angle = 156.5 + angle_adjust;
                red_nums++;
                cout << "Red cone " << red_nums << " detected.\n";
                if (red_nums >= 3 && pass_nums++ > 80) {
                    red_cone_finish = true;
                    ab_finish = false;  // Trigger AB
                }
            } else if (red_cone_finish && !ab_finish) {
                gpio.setMotor(10800);
                if (result.red_cone_pos != -1) {
                    gpio.setMotor(10000);
                    this_thread::sleep_for(500ms);
                    result.ab_result = result.ab_result != -1 ? result.ab_result : 2;  // Default B
                    ab_finish = true;
                    cout << "AB result: " << result.ab_result << "\n";
                }
            } else if (ab_finish && !yellow_finish) {
                gpio.setMotor(10800);
                if (result.yellow_count >= 2) {
                    yellow_finish = true;
                    gpio.setMotor(10000);
                    cout << "Yellow detected, parking!\n";
                    break;
                }
            } else {
                gpio.setMotor(11000);  // Default speed
            }

            gpio.setServo(angle);
            cout << "Midline: " << result.mid_line << ", Angle: " << angle << "\n";

            // FPS-like throttling
            this_thread::sleep_until(last_time + 33ms);
            last_time = steady_clock::now();
        }
    }

    ~ControlActuator() {
        stop_requested = true;
        if (control_thread.joinable()) control_thread.join();
    }
};

int main() {
    signal(SIGINT, signalHandler);

    // Start threads
    FrameCapture capturer;
    ImageProcessor processor;
    ControlActuator actuator;

    // Main thread: Monitor (can add FPS calc here if needed)
    while (running) {
        this_thread::sleep_for(100ms);
    }

    return 0;
}
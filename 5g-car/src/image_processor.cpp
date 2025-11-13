#include "../include/image_processor.h"
#include <fstream>
#include <cstdlib>

ImageProcessor::ImageProcessor() {
    process_thread = thread(&ImageProcessor::processLoop, this);
}

void ImageProcessor::processLoop() {
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

        // 顺序检测（使用ROI优化）
        result.mid_line = trackMidLine(result.binary_edges);
        result.red_cone_pos = detectRedCone(frame);
        result.blue_card_detected = detectBlueCard(frame);
        result.yellow_detected = detectYellow(frame, yellow_count);
        result.zebra_crossing = detectZebra(frame);

        // 状态机逻辑（简化自原版）
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

bool ImageProcessor::detectBlueCard(const Mat& frame) {
    Mat hsv;
    cvtColor(frame, hsv, COLOR_BGR2HSV);
    Scalar lower_blue(100, 50, 50);
    Scalar upper_blue(130, 255, 255);
    Mat mask;
    inRange(hsv, lower_blue, upper_blue, mask);
    int area = countNonZero(mask);
    return area > 60000;  // 检测阈值
}

int ImageProcessor::detectRedCone(const Mat& frame) {
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
        return bbox.x + (bbox.width / 2);  // 返回中心x
    }
    return -1;
}

bool ImageProcessor::detectYellow(const Mat& frame, int& count) {
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

bool ImageProcessor::detectZebra(const Mat& frame) {
    Mat gray, edges;
    cvtColor(frame, gray, COLOR_BGR2GRAY);
    GaussianBlur(gray, gray, Size(5, 5), 0);
    Canny(gray, edges, 70, 150);
    int white_pixels = countNonZero(edges);
    return white_pixels > 5000;  // 简单阈值
}

int ImageProcessor::callYoloAB() {
    system("/usr/local/bin/python3 /home/pi/g5g-new/yolo.py > res.txt");
    ifstream file("res.txt");
    string line;
    if (file.is_open() && getline(file, line)) {
        return stoi(line);
    }
    return -1;
}

double ImageProcessor::trackMidLine(const Mat& binary) {
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

Mat ImageProcessor::processEdges(const Mat& frame) {
    Mat gray, edges;
    cvtColor(frame, gray, COLOR_BGR2GRAY);
    GaussianBlur(gray, gray, Size(5, 5), 0);
    Canny(gray, edges, 70, 150);
    // 简单ROI掩膜
    Mat mask = Mat::zeros(edges.size(), CV_8UC1);
    vector<Point> poly = {{0, edges.rows}, {edges.cols, edges.rows}, {edges.cols, edges.rows * 0.5}, {0, edges.rows * 0.5}};
    fillPoly(mask, {poly}, 255);
    Mat roi_edges;
    bitwise_and(edges, mask, roi_edges);
    return roi_edges;  // 返回掩膜边缘用于跟踪
}

ImageProcessor::~ImageProcessor() {
    stop_requested = true;
    if (process_thread.joinable()) process_thread.join();
}
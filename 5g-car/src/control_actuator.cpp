#include "../include/control_actuator.h"

ControlActuator::ControlActuator() : gpio() {
    gpio.init();
    control_thread = thread(&ControlActuator::controlLoop, this);
}

void ControlActuator::controlLoop() {
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

        // 状态机（简化）
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
        if (ab_finish) error = 160.0 - (result.mid_line + 40);  // 入库调整

        double angle_adjust = pid.compute(error);
        double angle = 100.0 + angle_adjust;  // 中性位置调整为100度
        angle = max(min(angle, max_angle), min_angle);

        if (result.red_cone_pos != -1 && !red_cone_finish) {
            gpio.setMotor(11000);
            if (red_nums % 2 == 1) error = 160 - (result.red_cone_pos - 55);
            else error = 160 - (result.red_cone_pos + 55);
            angle_adjust = pid.compute(error);
            angle = 100.0 + angle_adjust;  // 中性位置调整为100度
            red_nums++;
            cout << "Red cone " << red_nums << " detected.\n";
            if (red_nums >= 3 && pass_nums++ > 80) {
                red_cone_finish = true;
                ab_finish = false;  // 触发AB
            }
        } 
        
        else if (red_cone_finish && !ab_finish) {
            gpio.setMotor(10800);
            if (result.red_cone_pos != -1) {
                gpio.setMotor(10000);
                this_thread::sleep_for(500ms);
                result.ab_result = result.ab_result != -1 ? result.ab_result : 2;  // 默认B
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
            gpio.setMotor(11000);  // 默认速度
        }

        gpio.setServo(angle);
        cout << "Midline: " << result.mid_line << ", Angle: " << angle << "\n";

        // FPS节流
        this_thread::sleep_until(last_time + 33ms);
        last_time = steady_clock::now();
    }
}

ControlActuator::~ControlActuator() {
    stop_requested = true;
    if (control_thread.joinable()) control_thread.join();
}
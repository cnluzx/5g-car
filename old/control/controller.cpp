#include "core/smartcar.h"

// PID控制参数
double kp = 0.25;
double ki = 0.00;
double kd = 0.125;
double last_error = 0;
double sum_error = 0;

// GPIO初始化和控制
void Set_gpio();
void Set_dian(int value);
double PID(double error1);
void Set_duo(int angle);

#include "core/smartcar.h"
#include <iostream>

int main() {
    smartcar::SmartCar car;
    
    // 初始化
    car.initialize();
    
    // 运行主循环
    car.run();
    
    return 0;
}

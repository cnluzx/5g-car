import pigpio
import time
import math

# 驱动相关参数
kp = 0.25
ki = 0.00
kd = 0.125
last_error = 0
sum_error = 0

class GPIOController:
    def __init__(self):
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise Exception("无法连接到pigpio守护进程")
        self.last_dian = 10000
        
    def set_gpio(self):
        # 设置电机控制引脚
        self.pi.set_mode(13, pigpio.OUTPUT)
        self.pi.set_PWM_range(13, 40000)
        self.pi.set_PWM_frequency(13, 200)
        
        # 设置舵机控制引脚
        self.pi.set_mode(12, pigpio.OUTPUT)
        self.pi.set_PWM_range(12, 30000)
        self.pi.set_PWM_frequency(12, 50)
        
        # 初始化设置
        self.pi.set_PWM_dutycycle(13, 10000)
        self.set_duo(156.5)
    
    def set_dian(self, value):
        if value > 10800:
            start = max(10800, self.last_dian)
            for i in range(start, value + 1, 50):
                self.pi.set_PWM_dutycycle(13, min(i, value))
                time.sleep(0.025)  # 25ms
        else:
            self.pi.set_PWM_dutycycle(13, value)
        self.last_dian = value
    
    def pid(self, error1):
        angle = kp * error1 + kd * (error1 - last_error)
        last_error = error1
        return angle
    
    def set_duo(self, angle):
        value = (0.5 + (2 / 270.0) * angle) / 20 * 30000  # 角度转换
        print(f"value: {value}")
        self.pi.set_PWM_dutycycle(12, value)
    
    def cleanup(self):
        self.pi.stop()

# 使用示例
if __name__ == "__main__":
    try:
        controller = GPIOController()
        controller.set_gpio()
        
        # 在这里添加你的主要控制逻辑
        
    except KeyboardInterrupt:
        controller.cleanup()
    except Exception as e:
        print(f"错误: {e}")
        controller.cleanup()

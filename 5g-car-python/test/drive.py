import pigpio
import time
import math
import subprocess 


# PID 参数
kp = 0.25
ki = 0.00
kd = 0.125

speed_val = 13000   # 电机最大值


class Dian_Duo:
    def __init__(self):
        self.start_pigpiod()
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise Exception("无法连接到 pigpiod")

        self.last_error = 0
        self.sum_error = 0
        self.last_dian = 11800  # 电机初始速度

        self.set_gpio()
        print("[Dian_Duo] 初始化完成")

    # -------------------------
    # 启动 pigpio 守护进程
    # -------------------------
    def start_pigpiod(self):
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'pigpiod' not in result.stdout:
                print("[Dian_Duo] pigpiod 未运行，正在启动...")
                subprocess.Popen(['sudo', 'pigpiod'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                print("[Dian_Duo] pigpiod 已启动")
            else:
                print("[Dian_Duo] pigpiod 已运行")
        except Exception as e:
            print(f"[Dian_Duo] 启动 pigpiod 失败: {e}")

    # -------------------------
    # GPIO 初始化
    # -------------------------
    def set_gpio(self):

        # -------------- 电机 PWM (13号脚) --------------
        self.pi.set_mode(13, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(13, 200)     # 200Hz
        self.pi.set_PWM_range(13, 40000)       # 0~20000 的可调范围

        # -------------- 舵机 PWM (12号脚) --------------
        self.pi.set_mode(12, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(12, 50)       # 舵机固定 50Hz
        # 舵机用 set_servo_pulsewidth，不需要 set_PWM_range

        print("[Dian_Duo] GPIO 初始化完毕")

    # -------------------------
    # 电机平滑加速
    # -------------------------
    def set_dian(self, value):
        value = max(0, min(value, speed_val))

        if value > self.last_dian:
            start = max(10800, self.last_dian)
            for i in range(start, value + 1, 50):
                self.pi.set_PWM_dutycycle(13, i)
                time.sleep(0.02)
        else:
            self.pi.set_PWM_dutycycle(13, value)

        self.last_dian = value

    # -------------------------
    # PID控制
    # -------------------------
    def pid(self, error):
        angle = kp * error + kd * (error - self.last_error)
        self.last_error = error
        return angle

    # -------------------------
    # 舵机功能：-90° 到 +90°
    # 使用脉宽控制（500~2500 微秒）
    # -------------------------
    def set_duo(self, angle):
    # 限制角度范围
        angle = max(0, min(180, angle))

        # 0° → 500us ，180° → 2500us
        pulsewidth = 500 + (angle / 180.0) * 2000  

        print(f"[Dian_Duo] 舵机角度: {angle}°, 脉宽: {pulsewidth}us")

        self.pi.set_servo_pulsewidth(12, pulsewidth)


    # -------------------------
    # 清理
    # -------------------------
    def cleanup(self):
        self.pi.set_servo_pulsewidth(12, 0)
        self.pi.set_PWM_dutycycle(13, 0)
        self.pi.stop()
        print("[Dian_Duo] GPIO 资源已释放")


# -------------------------
# 使用示例
# -------------------------
if __name__ == "__main__":
    try:
        controller = Dian_Duo()

        print("舵机转到 0°")
        controller.set_duo(60)
        time.sleep(1)

        print("舵机转到 +45°")
        controller.set_duo(100)
        time.sleep(1)

        print("舵机转到 -45°")
        controller.set_duo(140)
        time.sleep(1)

        print("电机加速到 12000")
        controller.set_dian(12000)
        time.sleep(2)

        print("电机降速到 10000")
        controller.set_dian(10000)

    except KeyboardInterrupt:
        pass
    finally:
        controller.cleanup()

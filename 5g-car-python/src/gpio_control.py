import pigpio
import time

class GPIOControl:
    def __init__(self, sim_mode=False, motor_pin=18, servo_pin=17):
        self.sim_mode = sim_mode
        self.motor_pin = motor_pin
        self.servo_pin = servo_pin
        self.pi = None
        self.started = False

    def init(self):
        if self.sim_mode:
            print("[GPIO] 仿真模式，跳过 pigpio 初始化")
            return
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("无法连接 pigpio daemon，请运行 pigpiod")
        self.started = True
        # 配置 PWM、频率等（按你的硬件参数）
        self.pi.set_mode(self.motor_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.servo_pin, pigpio.OUTPUT)
        # 初始化停止
        self.set_motor(0)
        self.set_servo(90)

    def set_motor(self, value):
        if self.sim_mode:
            # value 例如 0-20000
            print(f"[GPIO_SIM] set_motor {value}")
            return
        # clamp & 写 PWM (示例)
        self.pi.set_PWM_dutycycle(self.motor_pin, int(value / 20000.0 * 255))

    def set_servo(self, angle):
        if self.sim_mode:
            print(f"[GPIO_SIM] set_servo {angle}")
            return
        # 将角度映射为脉宽，例如 0-180 -> 500-2500 微秒
        pulse = int(500 + (angle / 180.0) * 2000)
        self.pi.set_servo_pulsewidth(self.servo_pin, pulse)

    def cleanup(self):
        if self.sim_mode:
            print("[GPIO] 仿真清理")
            return
        if self.pi:
            self.set_motor(0)
            self.set_servo(90)
            self.pi.stop()
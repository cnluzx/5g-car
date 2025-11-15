import time

class PIDController:
    def __init__(self, kp=0.25, ki=0.0, kd=0.125):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev = 0.0
        self.sum = 0.0
        self.last_time = None

    def update(self, error):
        now = time.time()
        dt = 0.02
        if self.last_time:
            dt = now - self.last_time
        self.last_time = now

        self.sum += error * dt
        de = (error - self.prev) / dt if dt > 0 else 0.0
        out = self.kp * error + self.ki * self.sum + self.kd * de
        self.prev = error
        return out
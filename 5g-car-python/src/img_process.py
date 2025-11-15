import threading
import queue
import time
import cv2
import numpy as np
import json
# 如果使用 ultralytics： from ultralytics import YOLO
# 或者在此模块用 subprocess 调用外部脚本

class ProcessedResult:
    def __init__(self, mid_line=0.0, red_cone_pos=-1, yellow_count=0, zebra=False, ab_result=-1):
        self.mid_line = mid_line
        self.red_cone_pos = red_cone_pos
        self.yellow_count = yellow_count
        self.zebra = zebra
        self.ab_result = ab_result

class ImageProcessor(threading.Thread):
    def __init__(self, frame_queue, result_queue, sim_mode=False):
        super().__init__(daemon=True)
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.running = False
        self.sim_mode = sim_mode
        # 如果使用内嵌模型，建议在这里加载一次
        # self.model = YOLO('yolov8n.pt')
    
    def run(self):
        self.running = True
        frame_count = 0
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            frame_count += 1
            res = ProcessedResult()
            # 示例：检测中线（占位）
            res.mid_line = self.detect_mid_line(frame)
            # 检测红锥、黄线、斑马线等（占位实现）
            res.red_cone_pos = self.detect_red_cone(frame)
            res.yellow_count = self.detect_yellow(frame)
            res.zebra = self.detect_zebra(frame)

            # AB 检测：调用内嵌模型或外部脚本
            res.ab_result = self.call_yolo_ab(frame)

            try:
                self.result_queue.put(res, timeout=0.1)
            except:
                pass

            if frame_count % 30 == 0:
                print(f"[ImageProcessor] 已处理 {frame_count} 帧, mid={res.mid_line}, red={res.red_cone_pos}, yellow={res.yellow_count}, ab={res.ab_result}")

    def stop(self):
        self.running = False

    def detect_mid_line(self, frame):
        # 占位：返回宽度中心
        return frame.shape[1] / 2

    def detect_red_cone(self, frame):
        # TODO: 实现颜色/形状检测
        return -1

    def detect_yellow(self, frame):
        # TODO: 实现黄线检测
        return 0

    def detect_zebra(self, frame):
        # TODO: 实现斑马线检测
        return False

    def call_yolo_ab(self, frame):
        # 推荐：如果推理开销大，把模型加载为成员（self.model）
        # 下面示例调用外部脚本并读取 JSON 输出（非阻塞版本可改为进程池）
        import subprocess, shlex
        try:
            # 将当前帧临时写入文件，或改为内存共享/直接把图像传入模型
            tmp = '/tmp/cur_frame.jpg'
            cv2.imwrite(tmp, frame)
            cmd = f"python3 python/yolo.py {tmp}"
            proc = subprocess.run(shlex.split(cmd), capture_output=True, timeout=3)
            out = proc.stdout.decode().strip()
            if not out:
                return -1
            data = json.loads(out)
            if 'result' in data:
                return 1 if data['result'] == 'A' else 0
        except Exception as e:
            print("[ImageProcessor] YOLO 调用失败:", e)
        return -1
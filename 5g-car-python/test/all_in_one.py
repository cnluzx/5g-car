import pygame
import os 
import numpy as np 
import cv2 
import time
import threading
import subprocess 
import platform 
import onnxruntime 

try:
    import pigpio
except ImportError:
    pigpio = None
    print("[Dian_Duo] 未找到 pigpio 库，Windows 环境将跳过硬件相关操作")
#############################################################################################
if_sound = False
if_baffle_move  = False

#############################################################################################
# Baffle 全局配置参数（新增检测间隔配置）
BLUE_LOWER = np.array([100, 150, 50])    # 蓝色 HSV 下限
BLUE_UPPER = np.array([140, 255, 255])   # 蓝色 HSV 上限
BLUE_AREA_THRESHOLD = 5000               # 蓝色区域最小面积阈值
CHECK_INTERVAL = 5                       # 状态打印间隔（检测周期数）
DETECTION_INTERVAL = 0.25               # 检测间隔时间（秒）→ 控制检测速度，越大越慢
CONFIRM_FRAMES = 3                       # 移除确认帧数（避免误判）

#############################################################################################
# PID 参数
kp = 0.25
ki = 0.00
kd = 0.125

speed_val = 13000   # 电机最大值
#############################################################################################
class Broadcast:
    def __init__(self):

        ####初始化pygame 
        ####其中有全局变量控制 if_sound是否播放 
        ####类成员变量 audio_initialized控制是否初始化成功 
        #### 如果initialized成功，则可以播放音频 
        ####整体调用流程:

        ###sound = Broadcast() 
        ###sound._play_sound(sound,speak )  即可播放音频 

        ###测试
        ###sound = Broadcast() 
        ###sound.test() 测试函数
        try:
            pygame.init()
            pygame.mixer.init()
            self.audio_initialized = True
            print("[Broadcast] pygame.mixer 初始化成功")

        except Exception as e:
            ###如果初始化失败
            print(f"[Broadcast] pygame.mixer 初始化失败: {e}")
            self.audio_initialized = False

    def _play_sound(self, place, name):


        if not self.audio_initialized:
            print("[Broadcast] 音频未初始化，跳过播放")
            return False 
        sound_path = f"files/{place}/{name}.mp3"

        print(f"[Broadcast] 尝试播放: {sound_path}")
        if not os.path.exists(sound_path):
            print(f"[Broadcast] 错误: 文件不存在 - {sound_path}")
            return False 
        try:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
            print(f"[Broadcast] 开始播放 {name}")
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(20)
            print(f"[Broadcast] 播放完成 {name}")  ###直至播放完毕
            if_sound = True 
            return True 

        except Exception as e:
            print(f"[Broadcast] 播放声音失败: {e}")
            return False 
    def test(self): 
        ret= sound._play_sound("sound","speak") 
        print(ret)  

class Baffle:
    def __init__(self, cap_id=0):
        self.detection_complete = False  # 整个检测流程是否完成
        self.baffle_detected = False     # 是否已确认检测到挡板
        self.cap = cv2.VideoCapture(cap_id)
        
        # 检查摄像头是否打开成功
        if not self.cap.isOpened():
            raise ValueError(f"无法打开摄像头 cap{cap_id} (ID={cap_id})")
        
        # 摄像头参数配置（降低资源占用）
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
        self.cap.set(cv2.CAP_PROP_FPS, 10)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.frame_count = 0
        self.detect_count = 0  # 检测周期计数器
        print(f"[find_baffle] 摄像头 cap{cap_id} 初始化成功（检测间隔：{DETECTION_INTERVAL}秒）")

    def process_blue_area(self, frame):
        # 固定 HSV 阈值筛选蓝色区域
        lower = BLUE_LOWER
        upper = BLUE_UPPER

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)

        # 形态学操作去除噪声
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask

    def find_blue_card(self, frame):
        mask = self.process_blue_area(frame)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:
            return False  # 无有效蓝色轮廓
        # 取最大轮廓面积判断
        max_area = cv2.contourArea(sorted(contours, key=cv2.contourArea, reverse=True)[0])
        # 降低打印频率
        if self.detect_count % CHECK_INTERVAL == 0:
            print(f"[find_baffle] 最大蓝色区域面积: {max_area:.1f} (阈值: {BLUE_AREA_THRESHOLD})")
        return max_area > BLUE_AREA_THRESHOLD

    def detection_stream(self):
        print("[find_baffle] 挡板检测线程已启动...")
        print(f"[find_baffle] 检测速度：每{DETECTION_INTERVAL}秒检测一次（按 'q' 键退出）")
        print("[find_baffle] 第一步：等待检测蓝色挡板...")

        while not self.detection_complete:
            ret, frame = self.cap.read()
            if not ret:
                print("[find_baffle] 捕获帧失败，重试...")
                time.sleep(DETECTION_INTERVAL)
                continue

            # 检测计数+1，执行蓝色区域检测
            self.detect_count += 1
            has_blue = self.find_blue_card(frame)

            ###################################
            # 阶段1：等待检测到蓝色挡板（确认挡板存在）
            ###################################
            if not self.baffle_detected:
                if has_blue:
                    print("\n[find_baffle] ✅ 已检测到蓝色挡板！")
                    print("[find_baffle] 第二步：持续监测，等待挡板移除...")
                    self.baffle_detected = True  # 进入阶段2
                    self.frame_count = 0  # 重置移除确认计数器
                    self.detect_count = 0
                else:
                    # 每CHECK_INTERVAL次打印等待提示
                    if self.detect_count % CHECK_INTERVAL == 0:
                        print("[find_baffle] 🔍 未检测到挡板，请放置蓝色挡板...")

            ###################################
            # 阶段2：已检测到挡板，等待其移除（核心逻辑）
            ###################################
            else:
                if not has_blue:
                    # 连续CONFIRM_FRAMES次未检测到 → 确认挡板移除
                    self.frame_count += 1
                    if self.frame_count >= CONFIRM_FRAMES:
                        print(f"\n[find_baffle] 🎉 连续{CONFIRM_FRAMES}次未检测到挡板，确认已移除！")
                        print("[find_baffle] 检测流程完成！")
                        self.detection_complete = True
                        break
                    else:
                        print(f"[find_baffle] 检测到挡板消失（连续 {self.frame_count}/{CONFIRM_FRAMES} 次），确认中...")
                else:
                    # 仍检测到挡板 → 重置确认计数器
                    self.frame_count = 0
                    if self.detect_count % CHECK_INTERVAL == 0:
                        print("[find_baffle] 🔍 挡板仍存在，持续等待移除...")

            ###################################
            # 按键退出+检测延迟（控制速度）
            ###################################
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[find_baffle] 收到退出指令，程序终止")
                self.detection_complete = True
                break
            
            # 每次检测后延迟，核心减速逻辑
            time.sleep(DETECTION_INTERVAL)

        print("[find_baffle] 检测已停止")

    def stop(self):
        self.cap.release()
        cv2.destroyAllWindows()
        print("[find_baffle] 摄像头已释放，资源清理完成")

    def test(self): 
        self.detection_stream() 
        self.stop()


class Control:
    def __init__(self):
        # 判断操作系统：Windows 不执行硬件初始化
        self.os_type = platform.system()
        self.pi = None  # pigpio 实例（Linux有效，Windows为None）
        
        if self.os_type != "Windows":
            self.start_pigpiod()
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise Exception("无法连接到 pigpiod")

            self.last_error = 0
            self.sum_error = 0
            self.last_dian = 11800  # 电机初始速度

            self.set_gpio()
            print("[Dian_Duo] 初始化完成（Linux环境）")
        else:
            # Windows 环境初始化占位参数，避免属性不存在报错
            self.last_error = 0
            self.sum_error = 0
            self.last_dian = 11800
            print("[Dian_Duo] 初始化完成（Windows环境，跳过硬件操作）")

    # -------------------------
    # 启动 pigpio 守护进程（仅Linux执行）
    # -------------------------
    def start_pigpiod(self):
        if self.os_type == "Windows":
            print("[Dian_Duo] Windows环境，不启动 pigpiod")
            return
        
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
    # GPIO 初始化（仅Linux执行）
    # -------------------------
    def set_gpio(self):
        if self.os_type == "Windows":
            print("[Dian_Duo] Windows环境，不初始化 GPIO")
            return

        # -------------- 电机 PWM (13号脚) --------------
        self.pi.set_mode(13, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(13, 200)     # 200Hz
        self.pi.set_PWM_range(13, 40000)       # 0~40000 的可调范围

        # -------------- 舵机 PWM (12号脚) --------------
        self.pi.set_mode(12, pigpio.OUTPUT)
        self.pi.set_PWM_frequency(12, 50)       # 舵机固定 50Hz
        # 舵机用 set_servo_pulsewidth，不需要 set_PWM_range

        print("[Dian_Duo] GPIO 初始化完毕")

    # -------------------------
    # 电机平滑加速（仅Linux执行）
    # -------------------------
    def set_dian(self, value):
        if self.os_type == "Windows":
            print(f"[Dian_Duo] Windows环境，跳过电机控制（目标速度：{value}）")
            return
        
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
    # PID控制（Windows环境仅计算不执行硬件操作）
    # -------------------------
    def pid(self, error):
        angle = kp * error + kd * (error - self.last_error)
        self.last_error = error
        print(f"[Dian_Duo] PID计算完成，输出角度：{angle:.2f}°")
        return angle

    # -------------------------
    # 舵机功能：-90° 到 +90°（仅Linux执行）
    # 使用脉宽控制（500~2500 微秒）
    # -------------------------
    def set_duo(self, angle):
        if self.os_type == "Windows":
            print(f"[Dian_Duo] Windows环境，跳过舵机控制（目标角度：{angle}°）")
            return
        
        # 限制角度范围（0°~180° 对应物理 -90°~+90°）
        angle = max(0, min(180, angle))

        # 0° → 500us ，180° → 2500us
        pulsewidth = 500 + (angle / 180.0) * 2000  

        print(f"[Dian_Duo] 舵机角度: {angle}°, 脉宽: {pulsewidth:.0f}us")
        self.pi.set_servo_pulsewidth(12, pulsewidth)

    # -------------------------
    # 清理资源（仅Linux执行）
    # -------------------------
    def cleanup(self):
        if self.os_type == "Windows":
            print("[Dian_Duo] Windows环境，跳过资源释放")
            return
        
        if self.pi:
            self.pi.set_servo_pulsewidth(12, 0)
            self.pi.set_PWM_dutycycle(13, 0)
            self.pi.stop()
            print("[Dian_Duo] GPIO 资源已释放")


class Yolo:
    def __init__(self, onnx_model_path, class_names_path, conf_thres=0.5, iou_thres=0.4):
        """
        初始化 YOLO ONNX 检测器
        :param onnx_model_path: ONNX 模型文件路径
        :param class_names_path: 类别名称文件路径（每行一个类别）
        :param conf_thres: 置信度阈值（过滤低置信度检测结果）
        :param iou_thres: NMS 的 IOU 阈值（去除重复检测框）
        """
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.class_names = self._load_class_names(class_names_path)
        self.input_shape = (480, 320)  # YOLO 模型默认输入尺寸（根据模型实际情况调整）
        
        # 初始化 ONNX Runtime 推理会话
        self.session = self._init_onnx_session(onnx_model_path)
        # 获取模型输入名称
        self.input_name = self.session.get_inputs()[0].name

    def _init_onnx_session(self, model_path):
        """初始化 ONNX Runtime 会话"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ONNX 模型文件不存在：{model_path}")
        
        try:
            # 配置推理参数（CPU 推理，支持 GPU 扩展）
            providers = ['CPUExecutionProvider']
            # 若系统支持 GPU，可添加 CUDA  provider（需安装对应版本的 onnxruntime-gpu）
            # if onnxruntime.get_device() == 'GPU':
            #     providers.insert(0, 'CUDAExecutionProvider')
            
            session = onnxruntime.InferenceSession(
                model_path,
                providers=providers,
                provider_options=[{'device_id': 0}] if 'CUDAExecutionProvider' in providers else None
            )
            print(f"[Yolo] ONNX 模型加载成功：{model_path}")
            print(f"[Yolo] 推理设备：{providers[0]}")
            return session
        except Exception as e:
            raise RuntimeError(f"ONNX 模型初始化失败：{e}")

    def _load_class_names(self, class_path):
        """加载类别名称列表"""
        if not os.path.exists(class_path):
            raise FileNotFoundError(f"类别文件不存在：{class_path}")
        
        with open(class_path, 'r', encoding='utf-8') as f:
            class_names = [line.strip() for line in f.readlines() if line.strip()]
        print(f"[Yolo] 加载类别数：{len(class_names)}")
        return class_names

    def _preprocess(self, frame):
        """图像预处理：缩放、归一化、维度转换"""
        # 保存原始图像尺寸（用于后续还原检测框）
        self.orig_h, self.orig_w = frame.shape[:2]
        
        # 缩放图像到模型输入尺寸（保持长宽比，填充黑边）
        img = cv2.resize(frame, self.input_shape, interpolation=cv2.INTER_LINEAR)
        # 归一化：像素值从 [0,255] 转为 [0,1]
        img = img / 255.0
        # 维度转换：(H,W,C) → (C,H,W) → (1,C,H,W)（模型输入格式）
        img = np.transpose(img, (2, 0, 1)).astype(np.float32)
        img = np.expand_dims(img, axis=0)
        return img

    def _postprocess(self, outputs):
        """后处理：解析模型输出，过滤低置信度，NMS 去重"""
        # YOLO 模型输出格式：(1, num_boxes, num_params) → num_params 包含 (x1,y1,x2,y2,conf,class_id,...)
        outputs = outputs[0]  # 去除 batch 维度
        boxes = []
        confidences = []
        class_ids = []

        # 解析每个检测框
        for out in outputs:
            if len(out) < 5:
                continue  # 无效检测框跳过
            x1, y1, x2, y2, conf = out[:5]
            class_scores = out[5:]
            class_id = np.argmax(class_scores)
            class_conf = class_scores[class_id]
            total_conf = conf * class_conf  # 置信度 = 框置信度 × 类别置信度

            # 过滤低置信度检测框
            if total_conf >= self.conf_thres:
                # 还原检测框到原始图像尺寸
                x1 = int(x1 * self.orig_w / self.input_shape[1])
                y1 = int(y1 * self.orig_h / self.input_shape[0])
                x2 = int(x2 * self.orig_w / self.input_shape[1])
                y2 = int(y2 * self.orig_h / self.input_shape[0])
                boxes.append([x1, y1, x2, y2])
                confidences.append(float(total_conf))
                class_ids.append(class_id)

        # NMS 去除重复检测框
        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, self.conf_thres, self.iou_thres
        )

        # 整理最终检测结果
        results = []
        if len(indices) > 0:
            for i in indices.flatten():
                results.append({
                    "box": boxes[i],  # [x1,y1,x2,y2]
                    "confidence": confidences[i],  # 置信度
                    "class_id": class_ids[i],  # 类别ID
                    "class_name": self.class_names[class_ids[i]]  # 类别名称
                })
        return results

    def detect(self, frame):
        """核心检测函数：输入图像帧，返回检测结果"""
        if frame is None:
            print("[Yolo] 输入图像为空，跳过检测")
            return []
        
        # 1. 图像预处理
        input_img = self._preprocess(frame)
        
        # 2. ONNX 模型推理
        try:
            outputs = self.session.run(None, {self.input_name: input_img})
        except Exception as e:
            print(f"[Yolo] 推理失败：{e}")
            return []
        
        # 3. 结果后处理
        results = self._postprocess(outputs)
        print(f"[Yolo] 检测到 {len(results)} 个目标")
        return results

    def draw_detections(self, frame, results):
        """在图像上绘制检测框和标签（可选可视化）"""
        for res in results:
            x1, y1, x2, y2 = res["box"]
            class_name = res["class_name"]
            confidence = res["confidence"]
            
            # 绘制检测框（蓝色，线宽2）
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            # 绘制标签背景（黑色半透明）
            label = f"{class_name} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            label_y1 = max(y1 - label_size[1] - 5, 0)
            cv2.rectangle(
                frame, (x1, label_y1), (x1 + label_size[0], y1 - 2),
                (0, 0, 0), -1
            )
            # 绘制标签文字（白色）
            cv2.putText(
                frame, label, (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
        return frame

    def test(self, test_img_path, save_output=True):
        """测试函数：加载单张图像进行检测，可选保存结果"""
        frame = cv2.imread(test_img_path)
        if frame is None:
            print(f"[Yolo] 无法读取测试图像：{test_img_path}")
            return
        
        # 执行检测
        results = self.detect(frame)
        # 绘制结果
        frame_with_detections = self.draw_detections(frame, results)
        
        # 显示结果（Linux环境可直接显示，Windows需调整窗口配置）
        if platform.system() != "Windows":
            cv2.imshow("[Yolo] 检测结果", frame_with_detections)
            print("[Yolo] 按 'q' 键关闭窗口")
            while cv2.waitKey(1) & 0xFF != ord('q'):
                continue
            cv2.destroyAllWindows()
        
        # 保存结果
        if save_output:
            output_path = "yolo_detection_result.jpg"
            cv2.imwrite(output_path, frame_with_detections)
            print(f"[Yolo] 检测结果已保存到：{output_path}")

def Line_stream():
    ...

if __name__ == "__main__": 
    sound = Broadcast()
    baffle = Baffle()
    baffle.test()



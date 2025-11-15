import pygame
import os
import threading
import queue
import cv2
import numpy as np
import time

##################################
## 流程——检测挡板、循迹白线、斑马线检测
running_flag = threading.Event()
running_flag.set()
audio_queue = queue.Queue(maxsize=10)

# 定义常量（挡板检测）
BLUE_AREA_THRESHOLD = 10000
MIN_ROW = 70
MAX_ROW = 120
BLUE_LOWER = np.array([100, 43, 46])
BLUE_UPPER = np.array([124, 255, 255])

# 定义常量（斑马线检测）
BANMA_WIDTH = 6
BANMA_NUMS = 3
BANMA_FLAG_THRESHOLD = 3
BANMA_CONSECUTIVE_FRAMES = 3  # 连续帧阈值

# 定义常量（循迹参数）
ROI_BOTTOM_RATIO = 0.5  # 调整为C++逻辑：从rows*0.5开始
IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
CENTER_X = IMAGE_WIDTH // 2  # 160
BOUNDARY_LEFT = 1
BOUNDARY_RIGHT = IMAGE_WIDTH - 2  # 318
CONTINUOUS_WHITE = 2  # 连续白像素数
MID_SAMPLE_OFFSET = 5  # 中下部采样偏移


if_sound = False 

class Broadcast:
    def __init__(self):

        ####初始化pygame 
        ####其中有全局变量控制 if_sound是否播放 
        ####类成员变量 audio_initialized控制是否初始化成功 
        #### 如果initialized成功，则可以播放音频 
        ####整体调用流程:

        ###sound = Broadcast() 
        ###sound._play_sound(sound,speak )  即可播放音频 

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
            return
        sound_path = f"/home/pi/5g-car-python/{place}/{name}.mp3"

        print(f"[Broadcast] 尝试播放: {sound_path}")
        if not os.path.exists(sound_path):
            print(f"[Broadcast] 错误: 文件不存在 - {sound_path}")
            return
        try:
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
            print(f"[Broadcast] 开始播放 {name}")
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(20)
            print(f"[Broadcast] 播放完成 {name}")  ###直至播放完毕
            if_sound = True 

        except Exception as e:
            print(f"[Broadcast] 播放声音失败: {e}")
            



class Baffle:
    def __init__(self, cap_id=2):
        """
        初始化摄像头和检测器
        Args:
            cap_id: 摄像头ID，默认2 (cap2)
        """
        self.detection_complete = False
        self.cap = cv2.VideoCapture(cap_id)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开摄像头 cap{cap_id} (ID={cap_id})")
        
        # 设置参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少延迟
        
        self.frame_count = 0
        print(f"[find_baffle] 摄像头 cap{cap_id} 初始化成功")

    def process_blue_area(self, frame):
        """
        处理图像，提取蓝色区域
        Returns: mask: 处理后的二值图像
        """
        if frame is None or frame.size == 0:
            raise ValueError("Input frame is empty")
        
        # 转换到HSV空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 提取蓝色区域
        mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 应用ROI限制
        mask[:MIN_ROW, :] = 0
        mask[MAX_ROW:, :] = 0
        
        return mask

    def find_blue_card(self, frame):
        """
        查找蓝色挡板
        Returns: bool: 是否找到蓝色挡板
        """
        try:
            mask = self.process_blue_area(frame)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            
            if not contours:
                return False
                
            # 按面积排序
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # 检查最大轮廓面积
            area = cv2.contourArea(contours[0])
            print(f"[find_baffle] 最大蓝色面积: {area}")
            return area > BLUE_AREA_THRESHOLD
            
        except Exception as e:
            print(f"Error in find_blue_card: {str(e)}")
            return False

    def detection_thread(self):
        print("[find_baffle] 检测线程已启动...")
        
        last_time = time.time()
        fps = 30  # 目标FPS
        consecutive_no_detection = 0  # 连续未检测到挡板的帧数
        max_no_detection = 10  # 连续未检测到的最大帧数
        
        while not self.detection_complete:
            ret, frame = self.cap.read()
            if not ret:
                print("[find_baffle] 捕获帧失败，重试...")
                time.sleep(0.1)
                continue
            
            self.frame_count += 1
            
            # 帧率控制
            current_time = time.time()
            if (current_time - last_time) < (1.0 / fps):
                time.sleep((1.0 / fps) - (current_time - last_time))
            last_time = current_time
            
            # 每5帧执行检测
            if self.frame_count % 5 == 0:
                if self.find_blue_card(frame):
                    print("[find_baffle] 找到蓝色挡板")
                    consecutive_no_detection = 0
                else:
                    consecutive_no_detection += 1
                    if consecutive_no_detection >= max_no_detection:
                        print("[find_baffle] 连续未检测到挡板，检测完成")
                        self.detection_complete = True
        
        print("[find_baffle] 检测线程已停止")

    def stop(self):
        """停止检测并释放资源"""
        self.cap.release()
        cv2.destroyAllWindows()


class LineTracker:
    def __init__(self, cap_id=2, boardcast=None):
        """
        初始化循迹器
        Args:
            cap_id: 摄像头ID，默认2
            boardcast: 语音播报实例，用于斑马线播报
        """
        self.cap = cv2.VideoCapture(cap_id)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开摄像头 cap{cap_id} (ID={cap_id})")
        
        # 设置参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.boardcast = boardcast
        self.frame_count = 0
        self.tracking_complete = False  # 循迹完成标志（可用于外部控制）
        self.image_count = 0  # 用于保存图像计数
        print(f"[line_tracker] 摄像头 cap{cap_id} 初始化成功")

    def tracking(self, dilated_image, frame):
        """
        两侧白线像素级扫描循迹（移植自C++ Tracking函数）
        Returns: mid_final (int): 中线x坐标
        """
        rows, cols = dilated_image.shape[:2]
        left_line = []
        right_line = []
        mid = []
        begin = CENTER_X  # 160

        # 从底向上扫描（i=239 to rows*0.5）
        for i in range(rows - 1, int(rows * ROI_BOTTOM_RATIO) - 1, -1):  # ROI_BOTTOM_RATIO=0.5
            find_l = False
            find_r = False
            to_left = begin
            to_right = begin

            # 找左线：从begin左移，找连续2白像素
            while to_left >= BOUNDARY_LEFT:
                if (dilated_image[i, to_left] == 255 and
                    (to_left + 1 < cols and dilated_image[i, to_left + 1] == 255)):
                    find_l = True
                    left_line.append((to_left, i))
                    break
                else:
                    to_left -= 1
            if not find_l:
                left_line.append((BOUNDARY_LEFT, i))

            # 找右线：从begin右移，找连续2白像素
            while to_right <= BOUNDARY_RIGHT:
                if (dilated_image[i, to_right] == 255 and
                    (to_right - 1 >= 0 and dilated_image[i, to_right - 1] == 255)):
                    find_r = True
                    right_line.append((to_right, i))
                    break
                else:
                    to_right += 1
            if not find_r:
                right_line.append((BOUNDARY_RIGHT, i))

            # 计算中点
            midx1 = left_line[-1][0]
            midx2 = right_line[-1][0]
            mid.append(((midx1 + midx2) // 2, i))

            # 更新下一行起始
            begin = (to_left + to_right) // 2

            # 如果两边都边界，移除无效中点
            if to_left == BOUNDARY_LEFT and to_right == BOUNDARY_RIGHT:
                if mid:
                    mid.pop()

        if not mid:
            return CENTER_X  # 默认中心

        # 取中下部平均（size = len(mid)/2 + 5）
        size_mid = len(mid)
        half = size_mid // 2
        sample_size = min(half + MID_SAMPLE_OFFSET, size_mid)
        mid_final = 0
        for i in range(half, sample_size):
            mid_x = mid[i][0]
            mid_final += mid_x
            print(f"mid: ({mid_x}, {mid[i][1]})    ", end='')
            cv2.circle(frame, mid[i], 2, (0, 0, 255), -1)  # 红点中线

        mid_final //= (sample_size - half)
        print()  # 换行

        # 画左/右线点
        for point in left_line:
            cv2.circle(frame, point, 2, (0, 255, 0), -1)  # 绿点
        for point in right_line:
            cv2.circle(frame, point, 2, (0, 255, 0), -1)  # 绿点

        # 保存图像（类似C++）
        save_path = f"./image/mid/{self.image_count:04d}.jpg"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        cv2.imwrite(save_path, frame)
        self.image_count += 1

        return mid_final

    def calculate_steering(self, mid_final):
        """
        计算转向角度（基于中线偏差，移植自C++ PID部分简化版）
        """
        if mid_final == CENTER_X:
            return 0  # 直行

        error = CENTER_X - mid_final  # 偏差（正:右偏，负:左偏）
        # 简化PID：假设比例系数k=0.1875 (30/160范围)，实际可集成完整PID
        steering_angle = int(error * 0.1875)  # -30 to 30度
        steering_angle = np.clip(steering_angle, -30, 30)

        print(f"[line_tracker] 中线x: {mid_final}, 偏差: {error}, 转向角: {steering_angle}°")
        return steering_angle

    def detect_zebra_in_roi(self, frame):
        """
        在ROI区域检测斑马线（整合到循迹中）
        """
        if frame is None or frame.size == 0:
            return False
        
        rows, cols = frame.shape[:2]
        
        # 转换为HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 定义白色范围
        lower_white = np.array([0, 0, 160])
        upper_white = np.array([180, 50, 255])
        
        mask1 = cv2.inRange(hsv, lower_white, upper_white)
        
        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask1 = cv2.dilate(mask1, kernel)
        mask1 = cv2.erode(mask1, kernel)
        
        # 简单ROI：下半部（类似C++扫描范围）
        roi_mask = mask1[int(rows * 0.5):, :]
        
        # 扫描逻辑（简化版，基于多行连续检测）
        consecutive_rows = 0
        for i in range(int(roi_mask.shape[0] * 0.5), roi_mask.shape[0], 2):  # 相对ROI
            abs_i = int(rows * 0.5) + i
            if abs_i >= rows:
                break
            cout1 = 0  # 本行斑马线组数
            j = 10
            while j < cols - 10:
                cout2 = 0
                if roi_mask[i, j] == 0:  # 黑色
                    j += 1
                    while j < cols - 10 and roi_mask[i, j] == 255:
                        j += 1
                        cout2 += 1
                    if BANMA_WIDTH <= cout2 < 40:
                        cout1 += 1
                else:
                    j += 1
                
                if cout1 >= BANMA_NUMS:
                    consecutive_rows += 1
                    if consecutive_rows >= BANMA_FLAG_THRESHOLD:
                        print(f"[zebra_detect] 检测到斑马线 (连续 {consecutive_rows} 行)")
                        return True
                    break
            if cout1 < BANMA_NUMS:
                consecutive_rows = 0  # 重置
        
        return False

    def tracking_thread(self, max_frames=1000):  # 默认最大帧数，避免无限循环
        """
        循迹主循环，同时检测斑马线（使用像素扫描替换Hough）
        """
        print("[line_tracker] 循迹线程已启动...")
        
        last_time = time.time()
        fps = 30
        zebra_consecutive = 0
        parked = False
        
        while not self.tracking_complete and self.frame_count < max_frames:
            ret, frame = self.cap.read()
            if not ret:
                print("[line_tracker] 捕获帧失败，重试...")
                time.sleep(0.1)
                continue
            
            self.frame_count += 1
            
            # 帧率控制
            current_time = time.time()
            if (current_time - last_time) < (1.0 / fps):
                time.sleep((1.0 / fps) - (current_time - last_time))
            last_time = current_time
            
            # 图像预处理：灰度 + 高斯模糊 + Canny（类似C++ frame_processorByHF）
            grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            kernel_size = 5
            grayscale = cv2.GaussianBlur(grayscale, (kernel_size, kernel_size), 0)
            low_t = 70
            high_t = 150
            edges = cv2.Canny(grayscale, low_t, high_t)
            
            # 形态学膨胀（粗化白线，类似C++ dilated_image）
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            dilated_image = cv2.dilate(edges, kernel)
            
            # 两侧白线扫描
            mid_final = self.tracking(dilated_image, frame)
            
            # 计算转向
            steering = self.calculate_steering(mid_final)
            # 这里模拟输出控制信号，例如发送到电机
            print(f"[line_tracker] 帧 {self.frame_count}: 中线 {mid_final}, 转向: {steering}°")
            # 实际应用中：发送 steering 到 PWM 控制电机
            
            # 每5帧检测一次斑马线
            if self.frame_count % 5 == 0:
                if self.detect_zebra_in_roi(frame):
                    zebra_consecutive += 1
                    print(f"[zebra_detect] 连续 {zebra_consecutive} 帧检测到斑马线")
                    if zebra_consecutive >= BANMA_CONSECUTIVE_FRAMES and not parked:
                        print("[zebra_detect] 确认检测到斑马线，停车并播报")
                        if self.boardcast:
                            self.boardcast.update_sound("banma", "tingche")  # 播报停车
                        parked = True
                        time.sleep(10)  # 停车10秒
                        parked = False
                        zebra_consecutive = 0  # 重置
                else:
                    zebra_consecutive = 0
        
        print("[line_tracker] 循迹线程已停止")

    def stop(self):
        """停止并释放资源"""
        self.tracking_complete = True
        self.cap.release()
        cv2.destroyAllWindows()


# 使用示例（主程序）
if __name__ == "__main__":
    # 创建语音播报实例并启动线程
    boardcast = Broadcast()
    sound_thread = threading.Thread(target=boardcast.threading_sound)
    sound_thread.start()
    
    # 第一步：检测挡板移除
    baffle_detector = Baffle(cap_id=2)
    detect_thread_baffle = threading.Thread(target=baffle_detector.detection_thread)
    detect_thread_baffle.start()
    
    print("find_baffle识别功能启动...")
    
    # 等待挡板检测完成（挡板被移除）
    while not baffle_detector.detection_complete:
        time.sleep(0.1)
    
    detect_thread_baffle.join()
    baffle_detector.stop()
    print("挡板检测完成，开始循迹...")
    
    # 第二步：循迹白线，同时检测斑马线
    tracker = LineTracker(cap_id=2, boardcast=boardcast)
    track_thread = threading.Thread(target=tracker.tracking_thread, args=(30,))  # 例如跑500帧
    track_thread.start()
    
    print("循迹功能启动...")
    
    # 等待循迹完成（这里模拟，实际可根据条件设置tracker.tracking_complete = True）
    track_thread.join()
    
    tracker.stop()
    print("循迹完成，程序已退出")
    
    # 停止语音线程
    running_flag.clear()
    sound_thread.join()
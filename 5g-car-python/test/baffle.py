import cv2
import time 
import numpy as np

BLUE_AREA_THRESHOLD = 20000

# 初始阈值
BLUE_LOWER = np.array([100, 43, 46])
BLUE_UPPER = np.array([124, 255, 255])

class Baffle:
    def __init__(self, cap_id=0):
        self.detection_complete = False
        self.cap = cv2.VideoCapture(cap_id)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开摄像头 cap{cap_id} (ID={cap_id})")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.frame_count = 0
        print(f"[find_baffle] 摄像头 cap{cap_id} 初始化成功")

        # Trackbar窗口
        self.create_trackbar()

    def create_trackbar(self):
        cv2.namedWindow("HSV Adjust", cv2.WINDOW_NORMAL)

        cv2.createTrackbar("H_low", "HSV Adjust", BLUE_LOWER[0], 179, lambda x: None)
        cv2.createTrackbar("S_low", "HSV Adjust", BLUE_LOWER[1], 255, lambda x: None)
        cv2.createTrackbar("V_low", "HSV Adjust", BLUE_LOWER[2], 255, lambda x: None)

        cv2.createTrackbar("H_high", "HSV Adjust", BLUE_UPPER[0], 179, lambda x: None)
        cv2.createTrackbar("S_high", "HSV Adjust", BLUE_UPPER[1], 255, lambda x: None)
        cv2.createTrackbar("V_high", "HSV Adjust", BLUE_UPPER[2], 255, lambda x: None)

    def get_trackbar_values(self):
        h_low  = cv2.getTrackbarPos("H_low", "HSV Adjust")
        s_low  = cv2.getTrackbarPos("S_low", "HSV Adjust")
        v_low  = cv2.getTrackbarPos("V_low", "HSV Adjust")

        h_high = cv2.getTrackbarPos("H_high", "HSV Adjust")
        s_high = cv2.getTrackbarPos("S_high", "HSV Adjust")
        v_high = cv2.getTrackbarPos("V_high", "HSV Adjust")

        lower = np.array([h_low, s_low, v_low])
        upper = np.array([h_high, s_high, v_high])

        return lower, upper

    def process_blue_area(self, frame):
        lower, upper = self.get_trackbar_values()  # 从 Trackbar 动态获取 HSV 阈值

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)

        # 形态学
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # ❌ 去掉区域限制（不再裁剪）
        # mask[:MIN_ROW, :] = 0
        # mask[MAX_ROW:, :] = 0

        return mask

    def find_blue_card(self, frame):
        mask = self.process_blue_area(frame)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:
            return False, mask

        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        area = cv2.contourArea(contours[0])

        print(f"[find_baffle] 最大蓝色面积: {area}")
        return area > BLUE_AREA_THRESHOLD, mask

    def detection_thread(self):
        print("[find_baffle] 检测线程已启动...")

        cv2.namedWindow('Video Stream', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Mask View', cv2.WINDOW_NORMAL)

        while not self.detection_complete:
            ret, frame = self.cap.read()
            if not ret:
                print("[find_baffle] 捕获帧失败，重试...")
                time.sleep(0.1)
                continue

            found, mask = self.find_blue_card(frame)

            cv2.imshow("Video Stream", frame)
            cv2.imshow("Mask View", mask)

            # 若 found=False → 挡板存在；found=True → 挡板移除
            if found:
                print("[find_baffle] 挡板已移除，检测结束")
                self.detection_complete = True
                break
            else:
                print("[find_baffle] 正在检测到挡板...")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.detection_complete = True

        print("[find_baffle] 检测线程已停止")

    def stop(self):
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    baffle = Baffle()
    baffle.detection_thread()
    baffle.stop()

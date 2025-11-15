import cv2
import numpy as np
import platform

# ---------------- 默认参数 ----------------
params = {
    "start_ratio": 0.55,    # ROI 起始行比例
    "end_ratio": 0.9,       # ROI 结束行比例
    "H_low": 100, "S_low": 43, "V_low": 46,
    "H_high": 130, "S_high": 255, "V_high": 255,
    "kernel_size": 3,
    "min_height": 5,
    "max_height": 100
}

# ---------------- Trackbar回调 ----------------
def nothing(x):
    pass

# ---------------- 创建调参窗口 ----------------
def create_trackbar_window():
    cv2.namedWindow("Params", cv2.WINDOW_NORMAL)

    # ROI
    cv2.createTrackbar("start_ratio", "Params", int(params["start_ratio"]*100), 100, nothing)
    cv2.createTrackbar("end_ratio", "Params", int(params["end_ratio"]*100), 100, nothing)

    # 蓝色
    cv2.createTrackbar("H_low", "Params", params["H_low"], 179, nothing)
    cv2.createTrackbar("S_low", "Params", params["S_low"], 255, nothing)
    cv2.createTrackbar("V_low", "Params", params["V_low"], 255, nothing)
    cv2.createTrackbar("H_high", "Params", params["H_high"], 179, nothing)
    cv2.createTrackbar("S_high", "Params", params["S_high"], 255, nothing)
    cv2.createTrackbar("V_high", "Params", params["V_high"], 255, nothing)

    # 核大小和高度限幅
    cv2.createTrackbar("kernel_size", "Params", params["kernel_size"], 20, nothing)
    cv2.createTrackbar("min_height", "Params", params["min_height"], 200, nothing)
    cv2.createTrackbar("max_height", "Params", params["max_height"], 400, nothing)

# ---------------- 获取当前参数 ----------------
def update_params():
    params["start_ratio"] = cv2.getTrackbarPos("start_ratio", "Params") / 100.0
    params["end_ratio"]   = cv2.getTrackbarPos("end_ratio", "Params") / 100.0
    params["H_low"] = cv2.getTrackbarPos("H_low", "Params")
    params["S_low"] = cv2.getTrackbarPos("S_low", "Params")
    params["V_low"] = cv2.getTrackbarPos("V_low", "Params")
    params["H_high"] = cv2.getTrackbarPos("H_high", "Params")
    params["S_high"] = cv2.getTrackbarPos("S_high", "Params")
    params["V_high"] = cv2.getTrackbarPos("V_high", "Params")
    params["kernel_size"] = max(1, cv2.getTrackbarPos("kernel_size", "Params"))
    params["min_height"] = cv2.getTrackbarPos("min_height", "Params")
    params["max_height"] = cv2.getTrackbarPos("max_height", "Params")

# ---------------- 蓝色检测函数 ----------------
def blue_detect(img):
    h, w = img.shape[:2]
    start_row = int(h * params["start_ratio"])
    end_row = int(h * params["end_ratio"])
    roi = img[start_row:end_row, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([params["H_low"], params["S_low"], params["V_low"]])
    upper_blue = np.array([params["H_high"], params["S_high"], params["V_high"]])

    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # 形态学去噪
    kernel = np.ones((params["kernel_size"], params["kernel_size"]), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        return None, mask
    cnt = max(contours, key=cv2.contourArea)
    x, y, w_rect, h_rect = cv2.boundingRect(cnt)
    if not (params["min_height"] < h_rect < params["max_height"]):
        return None, mask
    return (x, y + start_row, w_rect, h_rect), mask

# ---------------- 主程序 ----------------
if __name__ == "__main__":
    system_platform = platform.system()
    if system_platform == "Windows":
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        raise Exception("无法打开摄像头")

    create_trackbar_window()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        update_params()

        obj, mask = blue_detect(frame)
        vis_img = frame.copy()
        if obj is not None:
            x, y, w_rect, h_rect = obj
            cv2.rectangle(vis_img, (x, y), (x+w_rect, y+h_rect), (0,255,0), 2)

        cv2.imshow("Frame", vis_img)
        cv2.imshow("Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

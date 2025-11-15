import cv2
import numpy as np
import platform

# ---------------- 默认参数 ----------------
params = {
    "start_ratio": 0.55,    # ROI 起始行比例
    "end_ratio": 0.9,       # ROI 结束行比例
    "H_low1": 0, "S_low1": 43, "V_low1": 46,
    "H_high1": 10, "S_high1": 255, "V_high1": 255,
    "H_low2": 153, "S_low2": 43, "V_low2": 46,
    "H_high2": 180, "S_high2": 255, "V_high2": 255,
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

    # 红色1
    cv2.createTrackbar("H_low1", "Params", params["H_low1"], 179, nothing)
    cv2.createTrackbar("S_low1", "Params", params["S_low1"], 255, nothing)
    cv2.createTrackbar("V_low1", "Params", params["V_low1"], 255, nothing)
    cv2.createTrackbar("H_high1", "Params", params["H_high1"], 179, nothing)
    cv2.createTrackbar("S_high1", "Params", params["S_high1"], 255, nothing)
    cv2.createTrackbar("V_high1", "Params", params["V_high1"], 255, nothing)

    # 红色2
    cv2.createTrackbar("H_low2", "Params", params["H_low2"], 179, nothing)
    cv2.createTrackbar("S_low2", "Params", params["S_low2"], 255, nothing)
    cv2.createTrackbar("V_low2", "Params", params["V_low2"], 255, nothing)
    cv2.createTrackbar("H_high2", "Params", params["H_high2"], 179, nothing)
    cv2.createTrackbar("S_high2", "Params", params["S_high2"], 255, nothing)
    cv2.createTrackbar("V_high2", "Params", params["V_high2"], 255, nothing)

    # 核大小和高度限幅
    cv2.createTrackbar("kernel_size", "Params", params["kernel_size"], 20, nothing)
    cv2.createTrackbar("min_height", "Params", params["min_height"], 200, nothing)
    cv2.createTrackbar("max_height", "Params", params["max_height"], 400, nothing)

# ---------------- 获取当前参数 ----------------
def update_params():
    params["start_ratio"] = cv2.getTrackbarPos("start_ratio", "Params") / 100.0
    params["end_ratio"]   = cv2.getTrackbarPos("end_ratio", "Params") / 100.0
    params["H_low1"] = cv2.getTrackbarPos("H_low1", "Params")
    params["S_low1"] = cv2.getTrackbarPos("S_low1", "Params")
    params["V_low1"] = cv2.getTrackbarPos("V_low1", "Params")
    params["H_high1"] = cv2.getTrackbarPos("H_high1", "Params")
    params["S_high1"] = cv2.getTrackbarPos("S_high1", "Params")
    params["V_high1"] = cv2.getTrackbarPos("V_high1", "Params")
    params["H_low2"] = cv2.getTrackbarPos("H_low2", "Params")
    params["S_low2"] = cv2.getTrackbarPos("S_low2", "Params")
    params["V_low2"] = cv2.getTrackbarPos("V_low2", "Params")
    params["H_high2"] = cv2.getTrackbarPos("H_high2", "Params")
    params["S_high2"] = cv2.getTrackbarPos("S_high2", "Params")
    params["V_high2"] = cv2.getTrackbarPos("V_high2", "Params")
    params["kernel_size"] = max(1, cv2.getTrackbarPos("kernel_size", "Params"))
    params["min_height"] = cv2.getTrackbarPos("min_height", "Params")
    params["max_height"] = cv2.getTrackbarPos("max_height", "Params")

# ---------------- 红色检测函数 ----------------
def red_detect(img):
    h, w = img.shape[:2]
    start_row = int(h * params["start_ratio"])
    end_row = int(h * params["end_ratio"])
    roi = img[start_row:end_row, :]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([params["H_low1"], params["S_low1"], params["V_low1"]])
    upper_red1 = np.array([params["H_high1"], params["S_high1"], params["V_high1"]])
    lower_red2 = np.array([params["H_low2"], params["S_low2"], params["V_low2"]])
    upper_red2 = np.array([params["H_high2"], params["S_high2"], params["V_high2"]])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

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

        obj, mask = red_detect(frame)
        vis_img = frame.copy()
        if obj is not None:
            x, y, w_rect, h_rect = obj
            cv2.rectangle(vis_img, (x, y), (x+w_rect, y+h_rect), (255,0,0), 2)

        cv2.imshow("Frame", vis_img)
        cv2.imshow("Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

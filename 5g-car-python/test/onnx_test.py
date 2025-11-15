from  import Yolo  # 导入你的 Yolo 类
import cv2

if __name__ == "__main__":
    # -------------------------- 初始化双模型检测器 --------------------------
    yolo = Yolo(
        ab_onnx_path="AB.onnx",       # 你的 AB 模型路径
        lr_onnx_path="LR.onnx",       # 你的 LR 模型路径
        class_names_path="class.names",# 类别文件路径
        conf_thres=0.5,               # 置信度阈值（可调整）
        iou_thres=0.4                 # NMS 阈值（可调整）
    )

    # -------------------------- 测试单张图像（Windows 支持显示） --------------------------
    print("=== 开始测试 AB 模型 ===")
    yolo.test_AB(test_img_path="test.jpg", save_output=True)  # 保存结果为 yolo_ab_detection_result.jpg

    print("\n=== 开始测试 LR 模型 ===")
    yolo.test_LR(test_img_path="test.jpg", save_output=True)  # 保存结果为 yolo_lr_detection_result.jpg

    # -------------------------- 实时检测（Windows 摄像头支持） --------------------------
    print("\n=== 开始实时检测（按 'q' 退出）===")
    cap = cv2.VideoCapture(0)  # 0 表示默认摄像头（外接摄像头可改为 1）
    
    # Windows 摄像头适配：设置摄像头分辨率（避免卡顿）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("❌ 无法读取摄像头画面")
            break
        
        # 分别调用 AB 和 LR 专属检测函数
        ab_results = yolo.detect_AB(frame)
        lr_results = yolo.detect_LR(frame)
        
        # 绘制检测结果（AB 蓝色框，LR 红色框，Windows 正常显示）
        frame = yolo.draw_detections(frame, ab_results, model_type="AB")
        frame = yolo.draw_detections(frame, lr_results, model_type="LR")
        
        # 显示画面（Windows 窗口正常弹出）
        cv2.imshow("AB + LR 双模型实时检测（Windows）", frame)
        
        # 按 'q' 退出（Windows 键盘响应正常）
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("=== 实时检测结束 ===")
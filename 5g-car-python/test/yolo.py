import cv2
import numpy as np
import onnxruntime

def simple_onnx_test(onnx_model_path, image_path, conf_thres=0.5, iou_thres=0.4):
    """
    完整 ONNX 测试（含后处理，直接输出检测到的目标）
    """
    # 加载模型
    session = onnxruntime.InferenceSession(
        onnx_model_path,
        providers=['CPUExecutionProvider']
    )
    input_name = session.get_inputs()[0].name
    input_shape = session.get_inputs()[0].shape  # (1,3,640,640)
    img_h, img_w = input_shape[2], input_shape[3]

    # 预处理（适配模型输入 640x640）
    image = cv2.imread(image_path)
    original_h, original_w = image.shape[:2]
    img = cv2.resize(image, (img_w, img_h))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)

    # 推理
    outputs = session.run(None, {input_name: img})[0]  # 取第一个输出张量

    # -------------------------- 核心：YOLO 后处理 --------------------------
    # 1. 过滤低置信度框
    boxes = []
    confidences = []
    class_ids = []
    for box in outputs[0]:  # 遍历所有候选框
        x, y, w, h, conf = box[:5]
        class_scores = box[5:]
        if conf < conf_thres:
            continue  # 跳过低置信度框
        class_id = np.argmax(class_scores)  # 取分数最高的类别
        boxes.append([x, y, w, h])
        confidences.append(conf)
        class_ids.append(class_id)

    # 2. NMS 去重（去掉重叠框）
    indices = cv2.dnn.NMSBoxes(
        boxes, confidences, conf_thres, iou_thres
    )

    # 3. 转换坐标到原始图像尺寸（模型输入 640x640 → 原始图像尺寸）
    final_results = []
    if len(indices) > 0:
        for i in indices.flatten():
            x, y, w, h = boxes[i]
            # YOLO 输出是中心坐标 (x,y) + 宽高 (w,h)，转成对角坐标 (x1,y1,x2,y2)
            x1 = int((x - w/2) * (original_w / img_w))
            y1 = int((y - h/2) * (original_h / img_h))
            x2 = int((x + w/2) * (original_w / img_w))
            y2 = int((y + h/2) * (original_h / img_h))
            final_results.append({
                "class_id": class_ids[i],
                "confidence": round(confidences[i], 2),
                "box": [x1, y1, x2, y2]
            })

    # -------------------------- 输出最终检测结果 --------------------------
    print("="*50)
    print(f"📊 最终检测结果（置信度阈值：{conf_thres}）")
    print(f"✅ 共检测到 {len(final_results)} 个目标")
    for i, res in enumerate(final_results, 1):
        print(f"目标 {i}：类别 ID {res['class_id']}，置信度 {res['confidence']}，位置 {res['box']}")
    
    # 可视化检测结果（在图像上画框）
    for res in final_results:
        x1, y1, x2, y2 = res["box"]
        cv2.rectangle(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
        label = f"Class{res['class_id']} {res['confidence']}"
        cv2.putText(image, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    cv2.imwrite("onnx_detection_result.jpg", image)
    print(f"\n📁 检测结果已保存为：onnx_detection_result.jpg")

    return final_results

if __name__ == '__main__':
    onnx_model_path = "LR.onnx"
    image_path = "2.jpg"
    try:
        simple_onnx_test(onnx_model_path, image_path)
        print("\n✅ 完整检测测试成功！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
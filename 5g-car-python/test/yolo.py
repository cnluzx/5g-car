# simple_test.py
import torch
import cv2
import numpy as np

def simple_pt_test(model_path, image_path):
    """
    简单的PyTorch模型测试
    """
    # 加载模型
    model = torch.load(model_path, map_location='cpu')
    model.eval()
    
    # 读取图像
    image = cv2.imread(image_path)
    original_shape = image.shape[:2]
    
    # 预处理
    img = cv2.resize(image, (640, 640))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)
    img_tensor = torch.from_numpy(img)
    
    # 推理
    with torch.no_grad():
        outputs = model(img_tensor)
    
    print("推理完成!")
    print(f"输出类型: {type(outputs)}")
    print(f"输出形状: {outputs.shape if hasattr(outputs, 'shape') else 'N/A'}")
    
    # 简单的输出解析
    if hasattr(outputs, 'shape'):
        print(f"输出维度: {outputs.shape}")
    
    return outputs

# 使用示例
if __name__ == '__main__':
    model_path = "LR.pt"  # 您的.pt模型文件
    image_path = "test.jpg"  # 测试图像
    
    try:
        results = simple_pt_test(model_path, image_path)
        print("测试成功!")
    except Exception as e:
        print(f"测试失败: {e}")
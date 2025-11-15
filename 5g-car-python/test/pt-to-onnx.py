import os
import sys
from ultralytics import YOLO

# -------------------------- 配置参数（只需修改这3项！） --------------------------
PT_MODEL_PATH = "AB.pt"          # 你的 PT 模型路径（和脚本同文件夹则直接写文件名）
OUTPUT_ONNX_PATH = "AB.onnx"     # 输出 ONNX 文件名
INPUT_SHAPE = (480, 320)         # 模型输入尺寸（必须和训练时一致，如 640x640）

# -------------------------- 自动校验与转换 --------------------------
def pt_to_onnx():
    # 1. 校验 PT 模型是否存在
    if not os.path.exists(PT_MODEL_PATH):
        print(f"❌ 未找到 PT 模型文件：{PT_MODEL_PATH}")
        print(f"   请确保模型文件在以下路径：{os.path.abspath(PT_MODEL_PATH)}")
        input("按回车键退出...")
        sys.exit(1)

    # 2. 加载 YOLO 模型
    print(f"✅ 找到 PT 模型：{PT_MODEL_PATH}")
    try:
        model = YOLO(PT_MODEL_PATH)
        print("✅ YOLO 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败：{e}")
        print("   请确保已安装 ultralytics：pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple")
        input("按回车键退出...")
        sys.exit(1)

    # 3. 执行转换（Windows 优化参数）
    print(f"🔄 开始转换 PT → ONNX（输入尺寸：{INPUT_SHAPE}）...")
    try:
        # 导出 ONNX，适配 Windows 环境和后续推理
        results = model.export(
            format="onnx",
            imgsz=INPUT_SHAPE,
            opset=12,               # 兼容大部分 ONNX Runtime 版本
            simplify=True,          # 自动简化模型（减小体积）
            dynamic=False,          # 关闭动态输入，提升兼容性
            save=True,              # 保存 ONNX 文件
            output=OUTPUT_ONNX_PATH # 自定义输出路径
        )
    except Exception as e:
        print(f"❌ 转换失败：{e}")
        print("   尝试解决：1. 升级依赖 pip install --upgrade ultralytics onnx  2. 更换 opset 为 11/13")
        input("按回车键退出...")
        sys.exit(1)

    # 4. 校验转换结果
    if os.path.exists(OUTPUT_ONNX_PATH):
        file_size = os.path.getsize(OUTPUT_ONNX_PATH) / 1024 / 1024  # 转为 MB
        print(f"🎉 转换成功！")
        print(f"📁 ONNX 保存路径：{os.path.abspath(OUTPUT_ONNX_PATH)}")
        print(f"📊 文件大小：{file_size:.2f} MB")
    else:
        print(f"❌ 转换成功但未找到 ONNX 文件，请检查输出路径")

    input("按回车键退出...")

if __name__ == "__main__":
    print("="*50)
    print("          Windows PT → ONNX 转换工具（ultralytics YOLO 版）")
    print("="*50)
    pt_to_onnx()
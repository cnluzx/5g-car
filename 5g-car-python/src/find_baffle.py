###find baffle 找挡板脚本
import cv2
import numpy as np

# 定义常量
BLUE_AREA_THRESHOLD = 10000
MIN_ROW = 70
MAX_ROW = 120
BLUE_LOWER = np.array([100, 43, 46])
BLUE_UPPER = np.array([124, 255, 255])

def process_blue_area(frame):
    """
    处理图像，提取蓝色区域
    Args:
        frame: 输入图像
    Returns:
        mask: 处理后的二值图像
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

def find_blue_card(frame):
    """
    查找蓝色挡板
    Args:
        frame: 输入图像
    Returns:
        bool: 是否找到蓝色挡板
    """
    try:
        mask = process_blue_area(frame)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        if not contours:
            return False
            
        # 按面积排序
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # 检查最大轮廓面积
        return cv2.contourArea(contours[0]) > BLUE_AREA_THRESHOLD
        
    except Exception as e:
        print(f"Error in find_blue_card: {str(e)}")
        return False

def is_blue_card_removed(frame):
    """
    检测蓝色挡板是否移开
    Args:
        frame: 输入图像
    Returns:
        bool: 蓝色挡板是否移开
    """
    try:
        mask = process_blue_area(frame)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        if not contours:
            return True
            
        # 按面积排序
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # 检查最大轮廓面积
        return cv2.contourArea(contours[0]) < BLUE_AREA_THRESHOLD
        
    except Exception as e:
        print(f"Error in is_blue_card_removed: {str(e)}")
        return True

def calculate_blue_area(frame):
    """
    计算蓝色区域总面积
    Args:
        frame: 输入图像
    Returns:
        float: 蓝色区域总面积
    """
    try:
        mask = process_blue_area(frame)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        total_area = sum(cv2.contourArea(contour) for contour in contours)
        print(f"蓝色总面积: {total_area}")
        return total_area
        
    except Exception as e:
        print(f"Error in calculate_blue_area: {str(e)}")
        return 0.0

# 使用示例
if __name__ == "__main__":
    # 读取图像
    frame = cv2.imread("your_image.jpg")
    
    if frame is not None:
        # 查找蓝色挡板
        if find_blue_card(frame):
            print("找到蓝色挡板")
        else:
            print("未找到蓝色挡板")
            
        # 检查是否移开
        if is_blue_card_removed(frame):
            print("蓝色挡板已移开")
        else:
            print("蓝色挡板未移开")
            
        # 计算蓝色区域面积
        total_area = calculate_blue_area(frame)

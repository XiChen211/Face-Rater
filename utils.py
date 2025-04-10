# utils.py
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import numpy as np
import cv2
import traceback # Import traceback for detailed error printing

def cv_image_to_qpixmap(cv_img, label_size):
    """将 OpenCV 图像 (numpy array) 转换为 QPixmap 并在 QLabel 中显示"""
    try:
        # 检查图像是否有效
        if cv_img is None or cv_img.size == 0:
             print("错误：cv_image_to_qpixmap 接收到无效的图像数据")
             return None, "无效的图像数据"

        qImg = None
        # 检查图像维度
        if len(cv_img.shape) == 3 and cv_img.shape[2] == 3: # 彩色图像
            height, width, channel = cv_img.shape
            bytesPerLine = 3 * width

            # --- !!! 修改点在这里 !!! ---
            # 1. 使用 OpenCV 将 BGR 转换为 RGB
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            # 2. 使用 RGB 数据创建 QImage，并指定格式为 Format_RGB888
            qImg = QImage(rgb_image.data, width, height, bytesPerLine, QImage.Format_RGB888)
            # --- 修改结束 ---

        elif len(cv_img.shape) == 2: # 灰度图像 (保持不变)
             height, width = cv_img.shape
             bytesPerLine = width
             qImg = QImage(cv_img.data, width, height, bytesPerLine, QImage.Format_Grayscale8)
        else:
             print(f"错误：不支持的图像形状 {cv_img.shape}")
             return None, "不支持的图像格式"

        if qImg is None:
            # This case might be redundant now, but kept for safety
            return None, "无法创建 QImage"

        pixmap = QPixmap.fromImage(qImg)
        # 缩放图片以适应 QLabel 大小，保持纵横比
        # 使用 label_size (QSize) 来进行缩放
        scaled_pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return scaled_pixmap, None # 返回 pixmap 和 无错误

    except Exception as e:
        print(f"转换图片到 QPixmap 时出错: {e}")
        traceback.print_exc() # 打印详细错误堆栈
        return None, f"显示图片时出错: {e}"
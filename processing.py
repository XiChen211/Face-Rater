# processing.py
import os
import traceback
import numpy as np
import cv2
from PIL import Image
import torch
from torchvision import transforms
from PyQt5.QtCore import QThread, pyqtSignal

# 从项目文件中导入
import config # 导入配置
from models import CNNRegressionModel # 导入模型定义

# 尝试导入必要的库
try:
    from ultralytics import YOLO
    from supervision import Detections
except ImportError as e:
    print(f"错误: 缺少必要的库: {e}. 请运行 'pip install ultralytics supervision'")
    YOLO = None # 标记库不可用
    Detections = None


# --- 1. 图像预处理 (用于颜值打分模型) ---
score_transform = transforms.Compose([
    transforms.Resize(config.SCORE_MODEL_INPUT_SIZE), # 使用配置文件中的尺寸
    transforms.ToTensor(),
    # 如果训练时用了 normalization，这里也要加上
    # transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# --- 2. 模型加载 ---
yolo_model = None
beauty_model = None
models_loaded = {"yolo": False, "beauty": False}

# 加载 YOLOv8
if YOLO is not None: # 仅在库成功导入时尝试加载
    if os.path.exists(config.YOLO_MODEL_PATH):
        try:
            yolo_model = YOLO(config.YOLO_MODEL_PATH)
            print("YOLOv8 人脸检测模型加载成功。")
            models_loaded["yolo"] = True
        except Exception as e:
            print(f"加载 YOLOv8 模型 '{config.YOLO_MODEL_PATH}' 时出错: {e}")
            traceback.print_exc()
    else:
        print(f"错误：YOLOv8 模型文件未找到于 '{config.YOLO_MODEL_PATH}'")
else:
     print("错误：ultralytics 或 supervision 库未安装，无法加载 YOLOv8 模型。")


# 加载颜值打分模型
if os.path.exists(config.BEAUTY_MODEL_PATH):
    try:
        beauty_model = CNNRegressionModel() # 实例化模型类
        # 加载权重，映射到正确设备
        beauty_model.load_state_dict(torch.load(config.BEAUTY_MODEL_PATH, map_location=config.DEVICE))
        beauty_model.to(config.DEVICE) # 移动模型到设备
        beauty_model.eval()          # 设置为评估模式
        print(f"颜值打分模型从 '{config.BEAUTY_MODEL_PATH}' 加载成功。")
        models_loaded["beauty"] = True
    except FileNotFoundError:
        print(f"错误：颜值打分模型文件未找到于 '{config.BEAUTY_MODEL_PATH}'")
    except Exception as e:
        print(f"加载颜值打分模型 '{config.BEAUTY_MODEL_PATH}' 时出错: {e}")
        traceback.print_exc()
else:
    print(f"错误：颜值打分模型文件未找到于 '{config.BEAUTY_MODEL_PATH}'")


# --- 3. 后台处理线程 ---
class ProcessingThread(QThread):
    # Signal arguments: cv_img (for display), score_text, status_message
    finished = pyqtSignal(object, str, str)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        # 注意：线程不直接持有模型，而是使用本模块全局加载的模型
        # 这假设模型是线程安全的（PyTorch 模型通常在 eval 模式下是）

    def run(self):
        """在后台线程中执行检测和打分"""
        # 检查模型是否已加载
        if not models_loaded["yolo"]:
            self.finished.emit(None, "N/A", "错误: YOLO 模型未加载")
            return
        if not models_loaded["beauty"]:
            self.finished.emit(None, "N/A", "错误: 颜值打分模型未加载")
            return

        cv_img = None # 初始化以防早期错误
        try:
            # 1. 加载图片
            print(f"线程：正在加载图片 {self.image_path}")
            cv_img = cv2.imread(self.image_path)
            if cv_img is None:
                self.finished.emit(None, "N/A", f"错误: 无法读取图片 {os.path.basename(self.image_path)}")
                return
            pil_img = Image.open(self.image_path).convert("RGB") # 用于 YOLO 和裁剪

            # 2. 人脸检测 (YOLOv8)
            print("线程：开始人脸检测...")
            yolo_output = yolo_model(pil_img, verbose=False) # verbose=False 减少控制台输出
            print("线程：人脸检测完成.")

            if Detections is None: # 再次检查 supervision 是否可用
                 self.finished.emit(cv_img, "N/A", "错误: supervision 库不可用")
                 return

            results = Detections.from_ultralytics(yolo_output[0])

            if len(results) == 0:
                print("线程：未检测到人脸。")
                self.finished.emit(cv_img, "N/A", "未检测到人脸")
                return

            print(f"线程：检测到 {len(results)} 张人脸。处理第一张...")
            # 获取第一个检测到的人脸边界框
            x_min, y_min, x_max, y_max = map(int, results.xyxy[0])

            # 坐标有效性检查
            h_img, w_img = cv_img.shape[:2]
            x_min = max(0, x_min)
            y_min = max(0, y_min)
            x_max = min(w_img - 1, x_max)
            y_max = min(h_img - 1, y_max)

            if x_min >= x_max or y_min >= y_max:
                 self.finished.emit(cv_img, "N/A", "检测到无效的人脸框")
                 return

            # 3. 裁剪人脸区域 (从 PIL Image)
            face_pil = pil_img.crop((x_min, y_min, x_max, y_max))

            # 4. 颜值打分
            print("线程：开始颜值打分...")
            face_tensor = score_transform(face_pil).unsqueeze(0) # 预处理并加 batch 维度
            face_tensor = face_tensor.to(config.DEVICE)       # 移动到设备

            with torch.no_grad():
                score_output = beauty_model(face_tensor)
            score = score_output.item()
            score_text = f"{score:.2f}" # 格式化分数
            print(f"线程：颜值打分完成，分数: {score_text}")

            # 5. 在 OpenCV 图像上绘制边界框
            cv2.rectangle(cv_img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            # 6. 发送成功结果信号
            self.finished.emit(cv_img, score_text, f"处理完成: {os.path.basename(self.image_path)}")

        except Exception as e:
            print(f"线程：处理过程中发生错误: {e}")
            traceback.print_exc()
            # 尝试返回原始（或部分处理的）图片和错误信息
            error_message = f"错误: 处理失败 - {e}"
            self.finished.emit(cv_img, "错误", error_message)

def get_model_load_status():
    """返回模型加载状态"""
    return models_loaded
# config.py
import torch
import os
from huggingface_hub import hf_hub_download

# --- 模型和文件路径 ---
YOLO_REPO_ID = "arnabdhar/YOLOv8-Face-Detection"
YOLO_FILENAME = "model.pt"
# 尝试从 Hugging Face Hub 下载/查找 YOLO 模型路径
try:
    print(f"正在查找/下载 {YOLO_FILENAME} 从 {YOLO_REPO_ID}...")
    # 使用 cache_dir 参数可以指定缓存位置，默认为 ~/.cache/huggingface/hub
    YOLO_MODEL_PATH = hf_hub_download(repo_id=YOLO_REPO_ID, filename=YOLO_FILENAME)
    print(f"YOLO 模型路径: {YOLO_MODEL_PATH}")
    if not os.path.exists(YOLO_MODEL_PATH):
         print(f"警告: hf_hub_download 完成但文件 {YOLO_MODEL_PATH} 不存在?")
         # 提供一个备用/默认本地路径 (如果下载失败或不可靠)
         YOLO_MODEL_PATH = "model.pt" # 需要手动放置在此路径
         print(f"将尝试使用本地路径: {YOLO_MODEL_PATH}")

except Exception as e:
    print(f"无法从 HuggingFace Hub 下载或查找 YOLO 模型: {e}")
    # 提供一个备用/默认本地路径
    YOLO_MODEL_PATH = "model.pt" # 需要手动放置在此路径
    print(f"将尝试使用本地路径: {YOLO_MODEL_PATH}")


# 颜值打分模型权重文件路径 (相对于项目根目录)
BEAUTY_MODEL_PATH = 'beauty_cnn_model.pth'

# --- 设备配置 ---
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"使用的设备: {DEVICE}")

# --- 图像处理参数 ---
# 颜值打分模型期望的输入尺寸
SCORE_MODEL_INPUT_SIZE = (128, 128) # (Height, Width)

# --- UI 配置 (可选) ---
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 650
IMAGE_MIN_WIDTH = 550
IMAGE_MIN_HEIGHT = 450
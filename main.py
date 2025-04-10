# main.py
import sys
from PyQt5.QtWidgets import QApplication

# 导入主窗口类
from ui_main_window import FaceScoringApp
# 导入模型状态检查（虽然窗口内部也会检查，这里可以提前在控制台输出信息）
from processing import get_model_load_status

if __name__ == '__main__':
    # 检查模型加载状态（在创建UI前）
    model_status = get_model_load_status()
    print("-" * 30)
    print("模型加载状态汇总:")
    print(f"  - YOLOv8 检测模型: {'加载成功' if model_status['yolo'] else '加载失败'}")
    print(f"  - 颜值打分模型: {'加载成功' if model_status['beauty'] else '加载失败'}")
    print("-" * 30)

    if not model_status['yolo'] or not model_status['beauty']:
        print("警告：一个或多个模型未能加载，应用程序功能将受限。请查看之前的错误日志。")
        # 可以选择在这里提示用户并退出，或者让窗口自己处理
        # reply = QMessageBox.warning(None, "启动问题", "模型加载失败，是否继续？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.No:
        #     sys.exit(1)

    app = QApplication(sys.argv)
    mainWindow = FaceScoringApp()
    mainWindow.show()
    sys.exit(app.exec_())
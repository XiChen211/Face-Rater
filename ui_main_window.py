# ui_main_window.py
import os
import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                             QFileDialog, QMessageBox, QApplication, QFrame,
                             QSpacerItem, QSizePolicy, QProgressBar, QStatusBar, QMainWindow)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, QSize, QTimer

# --- 导入代码 ---
try:
    import config
    from processing import ProcessingThread, get_model_load_status
    from utils import cv_image_to_qpixmap
except ImportError as e:
    print("导入错误: {}. 请确保 config.py, processing.py, utils.py 在正确的位置。".format(e))
    # --- 模拟类和函数 ---
    class MockConfig:
        WINDOW_WIDTH = 600; WINDOW_HEIGHT = 650; IMAGE_MIN_WIDTH = 550; IMAGE_MIN_HEIGHT = 450; DEVICE = "cpu"
    config = MockConfig()
    def get_model_load_status(): return {"yolo": False, "beauty": False}
    class ProcessingThread:
        finished = type('MockSignal', (object,), {'connect': lambda self, slot: None, 'disconnect': lambda self, slot: None})() # 模拟信号
        def __init__(self, path): pass
        def start(self): print("[Mock] ProcessingThread started.")
        def isRunning(self): return False
        def requestInterruption(self): pass
        def wait(self, timeout=0): return True
    def cv_image_to_qpixmap(img, size): return None, "工具函数未加载"
    print("警告：正在使用模拟的配置、处理和工具函数。")
# --- 导入代码结束 ---


class FaceScoringApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.processing_thread = None
        self.model_status = get_model_load_status()
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_fake_progress)
        self.progress_value = 0
        self.initUI()
        self.applyStyles()
        self.check_model_status_on_init()

    def initUI(self):
        self.setWindowTitle('颜值打分系统 Pro')
        self.setGeometry(150, 150, config.WINDOW_WIDTH + 50, config.WINDOW_HEIGHT + 50)
        try:
            self.setWindowIcon(QIcon.fromTheme("face-smile", QIcon("icon.png")))
        except Exception as icon_e:
             print("警告：无法加载窗口图标: {}".format(icon_e))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- 图片显示标签 ---
        self.imageLabel = QLabel('拖拽图片到这里或点击下方按钮上传')
        self.imageLabel.setObjectName("imageLabel")
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setMinimumSize(QSize(config.IMAGE_MIN_WIDTH, config.IMAGE_MIN_HEIGHT))
        # 允许拖放事件到达此控件
        self.imageLabel.setAcceptDrops(True)
        # !!! 关联事件处理器 !!!
        self.imageLabel.dragEnterEvent = self.dragEnterEvent # 必须关联以接受拖放
        self.imageLabel.dropEvent = self.dropEvent       # 必须关联以处理放置
        main_layout.addWidget(self.imageLabel, 1)

        # --- 结果显示框架 ---
        result_frame = QFrame()
        result_frame.setObjectName("resultFrame")
        result_layout = QHBoxLayout(result_frame)
        score_title_label = QLabel("颜值评分:")
        self.scoreLabel = QLabel("N/A")
        self.scoreLabel.setObjectName("scoreLabel")
        result_layout.addStretch()
        result_layout.addWidget(score_title_label)
        result_layout.addWidget(self.scoreLabel)
        result_layout.addStretch()
        main_layout.addWidget(result_frame)

        # --- 控制/状态框架 ---
        control_frame = QFrame()
        control_layout = QVBoxLayout(control_frame)
        self.progressBar = QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setVisible(False)
        control_layout.addWidget(self.progressBar)
        self.uploadButton = QPushButton(" 上传图片")
        try:
            self.uploadButton.setIcon(QIcon.fromTheme("document-open", QIcon("upload_icon.png")))
            self.uploadButton.setIconSize(QSize(24, 24))
        except Exception as icon_e:
            print("警告：无法加载上传按钮图标: {}".format(icon_e))
        self.uploadButton.setCursor(Qt.PointingHandCursor)
        self.uploadButton.clicked.connect(self.startProcessing)
        control_layout.addWidget(self.uploadButton)
        main_layout.addWidget(control_frame)

        # --- 状态栏 ---
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusLabel = QLabel("就绪")
        self.fileNameLabel = QLabel("")
        self.statusBar.addPermanentWidget(self.fileNameLabel, 1)
        self.statusBar.addPermanentWidget(self.statusLabel)

    def applyStyles(self):
        """应用 QSS 样式"""
        style_sheet = """
            QMainWindow {
                background-color: #282c34;
            }
            QWidget {
                color: #abb2bf;
                font-family: 'Verdana', sans-serif;
                font-size: 10pt;
            }
            QLabel#imageLabel {
                background-color: #3b4048;
                border: 2px dashed #5c6370; /* 保持默认虚线边框 */
                border-radius: 10px;
                color: #5c6370;
                font-size: 12pt;
                padding: 10px;
            }
            /* 没有 dragEnter 的视觉反馈样式 */
            QFrame#resultFrame {
                 border: none;
                 margin-top: 10px;
            }
            QFrame#resultFrame QLabel {
                font-size: 14pt;
                color: #CCCCCC;
                background: transparent;
            }
            QLabel#scoreLabel {
                color: #98c379;
                font-size: 32pt;
                font-weight: bold;
                min-width: 80px;
                qproperty-alignment: 'AlignCenter';
            }
            QPushButton {
                background-color: #61afef;
                color: #282c34;
                border: none;
                padding: 12px 25px;
                border-radius: 5px;
                font-size: 11pt;
                font-weight: bold;
                margin-top: 10px;
                outline: none;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #7abfff;
            }
            QPushButton:pressed {
                background-color: #509aed;
            }
            QPushButton:disabled {
                background-color: #5c6370;
                color: #40454e;
                cursor: default;
            }
            QProgressBar {
                border: 1px solid #5c6370;
                border-radius: 5px;
                text-align: center;
                background-color: #3b4048;
                height: 8px;
                margin-top: 5px;
                margin-bottom: 5px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e06c75, stop:1 #be5046);
                border-radius: 4px;
            }
            QStatusBar {
                background-color: #21252b;
                color: #9da5b4;
                font-size: 9pt;
            }
            QStatusBar QLabel {
                 background: transparent;
                 padding-left: 5px;
                 padding-right: 5px;
                 color: #9da5b4;
                 font-size: 9pt;
            }
        """
        self.setStyleSheet(style_sheet)

    def check_model_status_on_init(self):
        """在初始化时检查模型加载状态并更新UI"""
        if not self.model_status["yolo"] or not self.model_status["beauty"]:
            self.uploadButton.setEnabled(False)
            missing = []
            if not self.model_status["yolo"]: missing.append("YOLOv8")
            if not self.model_status["beauty"]: missing.append("颜值打分")
            error_msg = "错误: {} 模型加载失败!".format(', '.join(missing))
            self.statusLabel.setText(error_msg)
            self.statusBar.setStyleSheet("background-color: #e06c75; color: white;")
            QMessageBox.critical(self, "模型加载失败", "以下模型未能成功加载：\n- {}\n请检查文件路径、依赖库和控制台错误信息。".format('\n- '.join(missing)))
        else:
             self.statusLabel.setText("模型加载成功 | 设备: {}".format(config.DEVICE)) # 使用 format 避免潜在 f-string 问题
             self.statusBar.setStyleSheet("")

    def startProcessing(self, file_path=None):
        if self.processing_thread and self.processing_thread.isRunning():
            QMessageBox.warning(self, "提示", "正在处理上一张图片，请稍候...")
            return

        image_to_process = file_path

        if not image_to_process:
            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getOpenFileName(self, "选择图片文件", "",
                                                      "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)",
                                                      options=options)
            if fileName:
                image_to_process = fileName
            else:
                return

        self.image_path = image_to_process
        print("UI: 选择的文件: {}".format(self.image_path))

        base_name = os.path.basename(self.image_path)
        display_name = base_name if len(base_name) < 40 else base_name[:37] + '...'
        self.fileNameLabel.setText("文件: {}".format(display_name)) # 使用 format
        self.statusLabel.setText("处理中...")
        self.scoreLabel.setText("...")
        self.uploadButton.setEnabled(False)
        self.imageLabel.setText('正在加载和处理图片...')

        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.progress_value = 0
        self.progress_timer.start(50)

        if 'ProcessingThread' in globals() and ProcessingThread is not None:
            try:
                self.processing_thread = ProcessingThread(self.image_path)
                if hasattr(self.processing_thread, 'finished') and self.processing_thread.finished:
                     self.processing_thread.finished.connect(self.onProcessingFinished)
                else:
                     raise AttributeError("ProcessingThread 实例缺少 'finished' 信号")
                self.processing_thread.start()
            except Exception as e:
                 print("启动处理线程时出错: {}".format(e))
                 QMessageBox.critical(self, "错误", "无法启动处理线程: {}".format(e))
                 self.resetUIState()
        else:
            QMessageBox.critical(self, "错误", "处理模块未正确加载，无法处理图片。")
            self.resetUIState()

    def update_fake_progress(self):
        if self.progress_value < 95:
            self.progress_value += 2
            self.progressBar.setValue(self.progress_value)

    def onProcessingFinished(self, cv_img, score_text, status_message):
        print("UI: 收到处理结果 - Score: {}, Status: {}".format(score_text, status_message))

        self.progress_timer.stop()
        self.progressBar.setValue(100)
        QTimer.singleShot(800, lambda: self.progressBar.setVisible(False))

        self.scoreLabel.setText(str(score_text)) # 确保是字符串
        status_core = status_message.split('-')[0].strip() if '-' in status_message else status_message
        self.statusLabel.setText(status_core)

        if "错误" in status_message or score_text == "错误":
             QMessageBox.warning(self, "处理错误", status_message)
             self.statusBar.setStyleSheet("background-color: #e06c75; color: white;")
             if cv_img is not None:
                  self.displayCvImage(cv_img)
             else:
                 self.imageLabel.setText('无法显示图片\n({})'.format(status_message)) # 使用 format
        else:
             self.statusBar.setStyleSheet("")
             if cv_img is not None:
                 self.displayCvImage(cv_img)
             else:
                 self.imageLabel.setText('未收到图像结果')

        self.uploadButton.setEnabled(True)
        if self.processing_thread:
             try:
                if hasattr(self.processing_thread, 'finished') and self.processing_thread.finished:
                    # 尝试断开连接，如果信号不存在或未连接，会忽略
                    self.processing_thread.finished.disconnect(self.onProcessingFinished)
             except (TypeError, AttributeError):
                pass # 忽略断开连接时可能出现的错误
             self.processing_thread = None

    def displayCvImage(self, cv_img):
        if 'cv_image_to_qpixmap' in globals() and cv_image_to_qpixmap is not None:
            pixmap, error = cv_image_to_qpixmap(cv_img, self.imageLabel.size())
            if error:
                self.imageLabel.setText(error)
                print("UI: 显示图片错误 - {}".format(error))
            elif pixmap:
                self.imageLabel.setPixmap(pixmap)
                self.imageLabel.setScaledContents(False)
            else:
                 self.imageLabel.setText("无法生成图像预览")
        else:
             self.imageLabel.setText("图像显示工具不可用")


    # --- 拖放事件处理 ---
    def dragEnterEvent(self, event):
        """处理拖动进入事件，必须接受才能触发 dropEvent"""
        if event.mimeData().hasUrls():
            # 只接受包含 URL 的拖动，不改变 UI 外观
            event.acceptProposedAction()
            # print("Drag Enter Accepted (URLs detected)") # 取消调试打印
        else:
            event.ignore()
            # print("Drag Enter Ignored (No URLs)") # 取消调试打印

    def dropEvent(self, event):
        """处理文件放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            supported_formats = ('.png', '.jpg', '.jpeg', '.bmp')
            if file_path.lower().endswith(supported_formats):
                print("UI: 拖放的文件: {}".format(file_path))
                self.startProcessing(file_path)
                event.acceptProposedAction() # 接受这次放置
            else:
                QMessageBox.warning(self, "文件类型错误", "不支持的文件类型: {}\n请选择 PNG, JPG, JPEG, 或 BMP 图片。".format(os.path.basename(file_path)))
                event.ignore() # 忽略无效文件类型
        else:
            event.ignore() # 忽略无效数据

    def resetUIState(self):
        """将UI恢复到空闲状态"""
        self.uploadButton.setEnabled(True)
        self.progressBar.setVisible(False)
        self.statusLabel.setText("就绪")
        self.fileNameLabel.setText("")
        self.scoreLabel.setText("N/A")
        self.imageLabel.setText('拖拽图片到这里或点击下方按钮上传')
        self.statusBar.setStyleSheet("")
        if self.progress_timer.isActive():
            self.progress_timer.stop()
        print("UI已重置到空闲状态。")


    def closeEvent(self, event):
        """确保在关闭窗口时，后台线程也停止"""
        if self.processing_thread and self.processing_thread.isRunning():
            print("UI: 关闭窗口，正在请求处理线程停止...")
            try:
                self.processing_thread.requestInterruption()
                if not self.processing_thread.wait(1000):
                     print("UI: 处理线程未能及时停止。")
                else:
                     print("UI: 处理线程已停止。")
            except AttributeError:
                 print("UI: 处理线程对象似乎不完整或不支持请求停止。")
        event.accept()


if __name__ == '__main__':
     print("正在直接运行 ui_main_window.py 进行测试...")
     app = QApplication(sys.argv)
     model_status = get_model_load_status()
     if not model_status['yolo'] or not model_status['beauty']:
          print("警告：一个或多个模型未能加载，功能将受限。")
     mainWindow = FaceScoringApp()
     mainWindow.show()
     sys.exit(app.exec_())

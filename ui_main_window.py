# ui_main_window.py
import os
import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
                             QFileDialog, QMessageBox, QApplication, QFrame,
                             QSpacerItem, QSizePolicy, QProgressBar, QStatusBar, QMainWindow)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, QSize, QTimer

# 从项目文件中导入
# 假设这些文件在同一目录下或已正确配置 PYTHONPATH
try:
    import config
    from processing import ProcessingThread, get_model_load_status
    from utils import cv_image_to_qpixmap
except ImportError as e:
    print(f"导入错误: {e}. 请确保 config.py, processing.py, utils.py 在正确的位置。")
    # 提供一些默认值或退出，以便至少UI框架能运行（但功能会受限）
    class MockConfig:
        WINDOW_WIDTH = 600
        WINDOW_HEIGHT = 650
        IMAGE_MIN_WIDTH = 550
        IMAGE_MIN_HEIGHT = 450
        DEVICE = "cpu" # 假设
    config = MockConfig()
    # 定义假的 processing 和 utils 函数/类以避免 NameError
    def get_model_load_status(): return {"yolo": False, "beauty": False}
    class ProcessingThread: # Dummy class
        finished = None
        def __init__(self, path): pass
        def start(self): pass
        def isRunning(self): return False
        def requestInterruption(self): pass
        def wait(self, timeout=0): return True
    def cv_image_to_qpixmap(img, size): return None, "工具函数未加载"

class FaceScoringApp(QMainWindow): # 继承 QMainWindow
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.processing_thread = None
        # 在实际应用中，get_model_load_status应该来自 processing.py
        self.model_status = get_model_load_status()
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_fake_progress)
        self.progress_value = 0
        self.initUI()
        self.applyStyles() # 应用 QSS 样式
        self.check_model_status_on_init()

    def initUI(self):
        self.setWindowTitle('颜值打分系统 Pro')
        self.setGeometry(150, 150, config.WINDOW_WIDTH + 50, config.WINDOW_HEIGHT + 50) # 稍微增大窗口
        # 提供一个备用图标路径或移除图标设置，如果找不到图标
        try:
            self.setWindowIcon(QIcon.fromTheme("face-smile", QIcon("icon.png"))) # 尝试加载 icon.png 作为备用
        except:
             print("警告：无法加载窗口图标。")


        # --- 中心部件 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget) # 主垂直布局

        # --- 图片显示标签 ---
        self.imageLabel = QLabel('拖拽图片到这里或点击下方按钮上传')
        self.imageLabel.setObjectName("imageLabel") # 用于 QSS
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setMinimumSize(QSize(config.IMAGE_MIN_WIDTH, config.IMAGE_MIN_HEIGHT))
        # 允许拖放事件到达此控件
        self.imageLabel.setAcceptDrops(True)
        # !!! 不再绑定 dragEnterEvent 和 dragLeaveEvent !!!
        # self.imageLabel.dragEnterEvent = self.dragEnterEvent
        # self.imageLabel.dragLeaveEvent = self.dragLeaveEvent
        # !!! 保留 dropEvent 来处理实际的放下操作 !!!
        self.imageLabel.dropEvent = self.dropEvent
        main_layout.addWidget(self.imageLabel, 1) # 参数 1 使其在垂直方向上优先伸展

        # --- 结果显示框架 ---
        result_frame = QFrame()
        result_frame.setObjectName("resultFrame")
        result_layout = QHBoxLayout(result_frame) # 水平布局放分数

        score_title_label = QLabel("颜值评分:")
        # 可以直接在 QSS 中设置样式，或者在这里设置基础样式
        # score_title_label.setStyleSheet("font-size: 14pt; color: #CCCCCC;")
        self.scoreLabel = QLabel("N/A")
        self.scoreLabel.setObjectName("scoreLabel") # 用于 QSS
        # self.scoreLabel.setStyleSheet("font-size: 28pt; font-weight: bold;") # QSS 会覆盖

        result_layout.addStretch() # 添加伸缩因子
        result_layout.addWidget(score_title_label)
        result_layout.addWidget(self.scoreLabel)
        result_layout.addStretch()
        main_layout.addWidget(result_frame)

        # --- 控制/状态框架 ---
        control_frame = QFrame()
        control_layout = QVBoxLayout(control_frame) # 垂直放按钮和进度条

        # 进度条
        self.progressBar = QProgressBar()
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setRange(0, 100) # 设置范围
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False) # 隐藏百分比文本
        self.progressBar.setVisible(False) # 默认隐藏
        control_layout.addWidget(self.progressBar)

        # 上传按钮
        self.uploadButton = QPushButton(" 上传图片") # 前面加空格给图标留位置
        try:
            self.uploadButton.setIcon(QIcon.fromTheme("document-open", QIcon("upload_icon.png"))) # 尝试加载 upload_icon.png
            self.uploadButton.setIconSize(QSize(24, 24)) # 图标大小
        except:
            print("警告：无法加载上传按钮图标。")
        self.uploadButton.setCursor(Qt.PointingHandCursor) # 手形光标
        self.uploadButton.clicked.connect(self.startProcessing)
        control_layout.addWidget(self.uploadButton)

        main_layout.addWidget(control_frame)

        # --- 状态栏 ---
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusLabel = QLabel("就绪") # 状态栏中的标签
        self.fileNameLabel = QLabel("") # 显示文件名
        self.statusBar.addPermanentWidget(self.fileNameLabel, 1) # 文件名占较多空间
        self.statusBar.addPermanentWidget(self.statusLabel) # 状态信息靠右

    def applyStyles(self):
        """应用 QSS 样式"""
        style_sheet = """
            QMainWindow {
                background-color: #282c34; /* 深色背景 */
            }
            QWidget { /* 应用于中心部件下的所有 QWidget */
                color: #abb2bf; /* 柔和的文字颜色 */
                font-family: 'Verdana', sans-serif; /* 更通用的字体 */
                font-size: 10pt;
            }

            QLabel#imageLabel {
                background-color: #3b4048; /* 图片区域背景 */
                border: 2px dashed #5c6370; /* 保持默认虚线边框 */
                border-radius: 10px;
                color: #5c6370; /* 提示文字颜色 */
                font-size: 12pt;
                padding: 10px; /* 加一点内边距 */
            }
            /* !!! 移除 :hover 规则 !!! */

            QFrame#resultFrame {
                 border: none; /* 结果区域无边框 */
                 margin-top: 10px; /* 与图片区域的间距 */
            }

            /* 可以为结果区域内的标签指定默认样式 */
            QFrame#resultFrame QLabel {
                font-size: 14pt;
                color: #CCCCCC; /* 默认文字颜色 */
                background: transparent; /* 确保背景透明 */
            }

            QLabel#scoreLabel {
                color: #98c379; /* 绿色分数 */
                font-size: 32pt; /* 分数更突出 */
                font-weight: bold;
                min-width: 80px; /* 给分数标签一个最小宽度，避免文字跳动 */
                qproperty-alignment: 'AlignCenter'; /* 确保分数居中 */
            }

            QPushButton {
                background-color: #61afef; /* 蓝色按钮 */
                color: #282c34; /* 深色文字 */
                border: none; /* 无边框 */
                padding: 12px 25px; /* 更大的内边距 */
                border-radius: 5px; /* 圆角 */
                font-size: 11pt;
                font-weight: bold;
                margin-top: 10px; /* 与上方元素的间距 */
                outline: none; /* 去除点击时的虚线框 */
                min-height: 40px; /* 按钮最小高度 */
            }

            QPushButton:hover {
                background-color: #7abfff; /* 悬停时变亮 */
            }

            QPushButton:pressed {
                background-color: #509aed; /* 按下时变暗 */
            }
            QPushButton:disabled { /* 禁用时的样式 */
                background-color: #5c6370; /* 灰色背景 */
                color: #40454e; /* 深灰色文字 */
                cursor: default; /* 恢复默认光标 */
            }

            QProgressBar {
                border: 1px solid #5c6370;
                border-radius: 5px;
                text-align: center;
                background-color: #3b4048;
                height: 8px; /* 细一点的进度条 */
                margin-top: 5px;
                margin-bottom: 5px;
            }

            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e06c75, stop:1 #be5046); /* 红色渐变 */
                border-radius: 4px; /* 进度块圆角 */
            }

            QStatusBar {
                background-color: #21252b; /* 状态栏背景 */
                color: #9da5b4; /* 状态栏文字颜色 */
                font-size: 9pt; /* 稍小字体 */
            }
            QStatusBar QLabel { /* 状态栏内标签样式 */
                 background: transparent; /* 确保背景透明 */
                 padding-left: 5px;
                 padding-right: 5px;
                 color: #9da5b4; /* 继承或明确设置颜色 */
                 font-size: 9pt; /* 继承或明确设置字体 */
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
            error_msg = f"错误: {', '.join(missing)} 模型加载失败!"
            self.statusLabel.setText(error_msg)
            # 通过 objectName 或直接设置样式表来标红状态栏
            self.statusBar.setStyleSheet("background-color: #e06c75; color: white;")
            QMessageBox.critical(self, "模型加载失败", f"请检查文件路径、依赖库和控制台错误信息。")
        else:
             self.statusLabel.setText(f"模型加载成功 | 设备: {config.DEVICE}")
             self.statusBar.setStyleSheet("") # 恢复默认样式

    def startProcessing(self, file_path=None): # 接受可选的文件路径参数 (用于拖放)
        # 检查线程是否已在运行
        if self.processing_thread and self.processing_thread.isRunning():
            QMessageBox.warning(self, "提示", "正在处理上一张图片，请稍候...")
            return

        image_to_process = file_path # 来自拖放

        if not image_to_process: # 如果不是拖放触发，则打开文件对话框
            options = QFileDialog.Options()
            # !!! 不使用 DontUseNativeDialog !!!
            fileName, _ = QFileDialog.getOpenFileName(self, "选择图片文件", "",
                                                      "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)",
                                                      options=options) # 使用默认 options
            if fileName:
                image_to_process = fileName
            else:
                return # 用户取消选择

        # --- 后续处理逻辑 ---
        self.image_path = image_to_process
        print(f"UI: 选择的文件: {self.image_path}")
        base_name = os.path.basename(self.image_path)
        # 截断过长的文件名
        display_name = base_name if len(base_name) < 40 else base_name[:37] + '...'
        self.fileNameLabel.setText(f"文件: {display_name}")
        self.statusLabel.setText("处理中...")
        self.scoreLabel.setText("...") # 用省略号表示处理中
        self.uploadButton.setEnabled(False) # 处理时禁用按钮
        self.imageLabel.setText('正在加载和处理图片...') # 清空旧图片或提示

        # --- 显示并启动进度条 ---
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        self.progress_value = 0
        # 使用模拟进度：
        self.progress_timer.start(50) # 每 50ms 更新一次假进度

        # 创建并启动处理线程
        # 确保 ProcessingThread 类可用
        if 'ProcessingThread' in globals() and ProcessingThread is not None:
            try:
                self.processing_thread = ProcessingThread(self.image_path)
                self.processing_thread.finished.connect(self.onProcessingFinished)
                self.processing_thread.start()
            except Exception as e:
                 print(f"启动处理线程时出错: {e}")
                 QMessageBox.critical(self, "错误", f"无法启动处理线程: {e}")
                 self.resetUIState() # 恢复UI状态
        else:
            QMessageBox.critical(self, "错误", "处理模块未正确加载，无法处理图片。")
            self.resetUIState() # 恢复UI状态

    def update_fake_progress(self):
        """模拟进度条前进"""
        if self.progress_value < 95: # 不要让假进度条直接到100%
            self.progress_value += 2
            self.progressBar.setValue(self.progress_value)

    def onProcessingFinished(self, cv_img, score_text, status_message):
        """处理线程完成后的回调函数"""
        print(f"UI: 收到处理结果 - Score: {score_text}, Status: {status_message}")

        # --- 停止并隐藏进度条 ---
        self.progress_timer.stop()
        self.progressBar.setValue(100) # 完成时设置为100%
        # 延迟隐藏，给用户看到完成状态
        QTimer.singleShot(800, lambda: self.progressBar.setVisible(False))

        self.scoreLabel.setText(f'{score_text}') # 显示最终分数或错误文本
        # 从状态消息中提取核心信息显示在状态栏
        status_core = status_message.split('-')[0].strip() if '-' in status_message else status_message
        self.statusLabel.setText(status_core)

        if "错误" in status_message or score_text == "错误":
             # 如果有错误信息，在对话框中显示完整信息
             QMessageBox.warning(self, "处理错误", status_message)
             self.statusBar.setStyleSheet("background-color: #e06c75; color: white;") # 错误状态栏标红
             # 尝试显示图片（可能是原始图或带框的）
             if cv_img is not None:
                  self.displayCvImage(cv_img)
             else:
                 # 如果图片也无法获取，显示错误文本
                 self.imageLabel.setText(f'无法显示图片\n({status_message})')
        else:
             self.statusBar.setStyleSheet("") # 恢复默认状态栏颜色
             if cv_img is not None:
                 self.displayCvImage(cv_img)
             else:
                 self.imageLabel.setText('未收到图像结果') # 理论上不应发生

        self.uploadButton.setEnabled(True) # 重新启用按钮
        # 清理线程对象引用
        if self.processing_thread:
             # 安全地断开连接，即使之前没有连接也不会出错
             try:
                self.processing_thread.finished.disconnect(self.onProcessingFinished)
             except TypeError:
                pass # Signal has no slots to disconnect.
             self.processing_thread = None

    def displayCvImage(self, cv_img):
        """使用 utils 函数显示 OpenCV 图像"""
        # 确保 cv_image_to_qpixmap 可用
        if 'cv_image_to_qpixmap' in globals() and cv_image_to_qpixmap is not None:
            pixmap, error = cv_image_to_qpixmap(cv_img, self.imageLabel.size())
            if error:
                self.imageLabel.setText(error)
                print(f"UI: 显示图片错误 - {error}")
            elif pixmap:
                self.imageLabel.setPixmap(pixmap)
                self.imageLabel.setScaledContents(False) # 确保我们手动缩放生效
            else:
                 self.imageLabel.setText("无法生成图像预览")
        else:
             self.imageLabel.setText("图像显示工具不可用")


    # --- 拖放事件处理 ---
    # !!! dragEnterEvent 和 dragLeaveEvent 已移除 !!!

    # --- 保留 dropEvent 以处理放下的文件 ---
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            supported_formats = ('.png', '.jpg', '.jpeg', '.bmp')
            if file_path.lower().endswith(supported_formats):
                print(f"UI: 拖放的文件: {file_path}")
                self.startProcessing(file_path) # 使用拖放的文件路径开始处理
                event.acceptProposedAction()
            else:
                QMessageBox.warning(self, "文件类型错误", f"不支持的文件类型: {os.path.basename(file_path)}\n请选择 PNG, JPG, JPEG, 或 BMP 图片。")
                event.ignore()
                # !!! 不再需要恢复样式 !!!
        else:
            event.ignore()
            # !!! 不再需要恢复样式 !!!

    def resetUIState(self):
        """将UI恢复到空闲状态"""
        self.uploadButton.setEnabled(True)
        self.progressBar.setVisible(False)
        self.statusLabel.setText("就绪")
        self.fileNameLabel.setText("")
        self.scoreLabel.setText("N/A")
        self.imageLabel.setText('拖拽图片到这里或点击下方按钮上传')
        self.statusBar.setStyleSheet("") # 恢复状态栏样式
        if self.progress_timer.isActive():
            self.progress_timer.stop()
        print("UI已重置到空闲状态。")


    def closeEvent(self, event):
        """确保在关闭窗口时，后台线程也停止"""
        if self.processing_thread and self.processing_thread.isRunning():
            print("UI: 关闭窗口，正在请求处理线程停止...")
            self.processing_thread.requestInterruption() # 尝试请求中断
            # 等待一小段时间让线程有机会结束
            if not self.processing_thread.wait(1000): # 等待最多1秒
                 print("UI: 处理线程未能及时停止，可能需要强制结束。")
                 # self.processing_thread.terminate() # 强制终止通常不推荐
            else:
                 print("UI: 处理线程已停止。")
        event.accept()

# 这个文件现在只包含 UI 类定义。
# 程序的入口应该在 main.py 中。
# 例如，main.py 的内容：
if __name__ == '__main__':
     # 为了能直接运行这个文件进行测试（不推荐用于最终产品）
     print("正在直接运行 ui_main_window.py 进行测试...")
     app = QApplication(sys.argv)
     # 检查模型加载状态（通常在 main.py 中完成）
     model_status = get_model_load_status()
     if not model_status['yolo'] or not model_status['beauty']:
          print("警告：一个或多个模型未能加载，功能将受限。")

     mainWindow = FaceScoringApp()
     mainWindow.show()
     sys.exit(app.exec_())
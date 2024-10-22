import requests
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import *
from io import BytesIO

class ClickableLabel(QLabel):
    """可点击的标签类"""
    clicked = Signal(object)  # 自定义信号

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)  # 触发点击信号
        super().mousePressEvent(event)

class ImageLabel(ClickableLabel):

    def __init__(self, url=None, size=None):
        super().__init__()

        self.setText('加载...')

        if not size:
            size = (100, 100)
        self.setFixedSize(size[0], size[1])

        # 下载并设置图片
        if url:
            self.load_image_from_url(url)

    def load_image_from_url(self, url):
        try:
            response = requests.get(url)  # 从URL获取图片
            response.raise_for_status()  # 检查请求是否成功
            image = QPixmap()
            image.loadFromData(BytesIO(response.content).read())  # 加载图片数据

            # 清除旧的Pixmap，设置新的Pixmap
            if not image.isNull():
                self.clear()  # 清除旧图像

                # 获取 QLabel 的尺寸，等比例缩放图片
                scaled_image = image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # 设置缩放后的图片
                self.setPixmap(scaled_image)
                # 居中对齐
                self.setAlignment(Qt.AlignCenter)

            else:
                self.setText("Failed to load image")

        except requests.exceptions.RequestException as e:
            self.setText(f"Failed to load image")

    def resizeEvent(self, event):
        # 在窗口大小改变时重新缩放图片
        if self.pixmap():
            scaled_image = self.pixmap().scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_image)

        # 保持父类的事件处理
        super().resizeEvent(event)

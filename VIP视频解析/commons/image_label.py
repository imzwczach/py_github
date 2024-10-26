import requests
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import *
from io import BytesIO

from commons.config import Config

class ClickableLabel(QLabel):
    """可点击的标签类"""
    clicked = Signal(object)  # 自定义信号

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)  # 触发点击信号
        super().mousePressEvent(event)

class ImageDownloadThread(QThread):
    imageDownloaded = Signal(bytes)
    
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            content = Config().request_data(self.url, type='content', expire=None)
            self.imageDownloaded.emit(content)
        except requests.exceptions.RequestException as e:
            self.imageDownloaded.emit(None)

class ImageLabel(ClickableLabel):

    def __init__(self, url=None):
        super().__init__()

        # 下载并设置图片
        if url:
            self.load_image_from_url(url)
        else:
            pixmap = QPixmap('movie_default_small.png')
            # 获取 QLabel 的尺寸，等比例缩放图片
            # scaled_image = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # 设置缩放后的图片
            self.setPixmap(pixmap)
            # 居中对齐
            self.setAlignment(Qt.AlignCenter)

    def load_image_from_url(self, url):
       if url:
            try:
                self.clear()
                self.download_thread = ImageDownloadThread(url)
                self.download_thread.imageDownloaded.connect(self.handle_downloaded_image)
                self.download_thread.start()
            except:
                self.download_thread.quit()
                self.download_thread.wait()

    def handle_downloaded_image(self, content):
       if content:
           image = QPixmap()
           image.loadFromData(BytesIO(content).read())
           if not image.isNull():
               scaled_image = image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
               self.setPixmap(scaled_image)
               self.setAlignment(Qt.AlignCenter)
           else:
               self.setText("Failed to load image")
       else:
           self.setText("Failed to load image")

    def resizeEvent(self, event):
        # 在窗口大小改变时重新缩放图片
        if self.pixmap():
            scaled_image = self.pixmap().scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_image)

        # 保持父类的事件处理
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.download_thread.isRunning():
            self.download_thread.quit()
            self.download_thread.wait()
        super().closeEvent(event)
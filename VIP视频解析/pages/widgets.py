from engine import Album
from commons.image_label import ImageLabel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
import datetime

class CustomWidget(QWidget):
    def __init__(self, album:Album):
        super().__init__()

        self.album = album

        # self.content_layout = QVBoxLayout()
        # # 创建一个水平布局，用于图片和文本标签的组合
        hbox = QHBoxLayout()
        
        # if album.img:
        #     # 创建图片标签 (这里可以设置为真实图片)
        #     image_label = ImageLabel(url=album.img)
        #     # 将 album 数据绑定到 QLabel 的属性中
        #     # image_label.setProperty("id", album.id)
        #     hbox.addWidget(image_label)

        # 创建文本标签，显示 item 中的某个字段
        text = f"<b>{album.title}</b>"
        if album.score:
            text += f"&emsp;<span style='font-size:12px;color:red;'><b>{album.score}</b></span>"
        if album.source:
            text += f"&emsp; <span style='font-size:12px;'>{album.source}</span>"
        if album.update:
            text += f"&emsp; <span style='font-size:12px;'>{album.update}</span>"
        text_label = QLabel(text) 
        hbox.addWidget(text_label)

        if album.date:
            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            color = 'red' if today_str in album.date else 'gray'
            date_label = QLabel(f"<span style='font-size:12px; color:{color};'>{album.date}</span>")
            date_label.setAlignment(Qt.AlignRight)
            hbox.addWidget(date_label)

        self.setLayout(hbox)
    
    def title(self):
        return self.album.title
    

class GridWidget(QWidget):
    def __init__(self, album:Album):
        super().__init__()

        self.album = album
        self.setStyleSheet("background:#f2f2f2;")

        layout = QVBoxLayout()
        
        if album.img:
            # 创建图片标签 (这里可以设置为真实图片)
            image_label = ImageLabel(url=album.img)
            image_label.setFixedSize(100, 115)
            # 将 album 数据绑定到 QLabel 的属性中
            # image_label.setProperty("id", album.id)
            layout.addWidget(image_label)

        # 创建文本标签，显示 item 中的某个字段
        hhbox = QHBoxLayout()
        text = f"<span style='font-size:11px;'><b>{album.title}</b></span>"
        text_label = QLabel(text) 
        hhbox.addWidget(text_label)

        if album.score:
            text = f"<span style='font-size:10px;color:red;'><b>{album.score}</b></span>"
            score_lable = QLabel(text)
            hhbox.addWidget(score_lable)

        layout.addLayout(hhbox)

        self.setLayout(layout)
    
    def title(self):
        return self.album.title
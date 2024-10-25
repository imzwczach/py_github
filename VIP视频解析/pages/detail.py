
from commons.image_label import ClickableLabel, ImageLabel
from engine import *
from commons.page import *
from PySide6.QtCore import Qt
from commons.FlowLayout import FlowLayout
from m3u8.m3u8_gui import M3U8DownloadPage

class MyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("提示")
        # 创建布局
        layout = QVBoxLayout()
        # 内容
        label = QLabel("请选择您想要的操作")
        layout.addWidget(label)
        # 创建按钮
        ok_button = QPushButton("播放")
        cancel_button = QPushButton("下载")
        # 连接按钮的信号与槽函数
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        # 将按钮添加到布局中
        layout.addWidget(ok_button)
        layout.addWidget(cancel_button)
        # 设置对话框的布局
        self.setLayout(layout)


class DetailPage(Page):
    def __init__(self, album: Album, engine: Engine):
        super().__init__()

        self.title = album.title

        # 创建图片标签 (这里可以设置为真实图片)
        image_label = ImageLabel()
        image_label.setFixedSize(QSize(200, 240))

        # 创建文本标签，显示 item 中的某个字段
        text_label = QLabel() 

        buttonAll = QPushButton('下载全集')
        buttonAll.setFixedSize(70,30)
        buttonAll.setVisible(Config().isPC)
        buttonAll.clicked.connect(self.on_download_all_button_clicked)

        # 创建一个水平布局，用于图片和文本标签的组合
        hbox = QHBoxLayout()
        right_box = QVBoxLayout()
        right_box.addWidget(text_label)
        right_box.addWidget(buttonAll)

        hbox.addWidget(image_label)
        hbox.addLayout(right_box)

        self.layout.addLayout(hbox)

        # 创建滚动区域
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 创建内部部件和网格布局
        inner_widget = QWidget()
        self.page_numbers_layout = FlowLayout(inner_widget, margin=10, spacing=10)
        # 将内部部件设置到滚动区域
        self.scroll_area.setWidget(inner_widget)
        self.layout.addWidget(self.scroll_area)
        
        try:
            self.album = engine.get_album_detail(album)
            image_label.load_image_from_url(self.album.img)

        except Exception as e:
                msg_box = QMessageBox()
                msg_box.setText(f"错误：{e}")
                msg_box.setWindowTitle("发生错误")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.exec()
                return

        text = f"<b>{self.album.title}</b><br> {self.album.source}, 更新时间:{self.album.date}"
        text_label.setText(text)

        self.build_page_numbers_layout(self.album)

        if Config().isPC:
            self.m3u8_gui = M3U8DownloadPage()
            self.m3u8_gui.setVisible(False)
            self.layout.addWidget(self.m3u8_gui)        

    def build_page_numbers_layout(self, album:Album):

        for i in range(self.page_numbers_layout.count()):
            item = self.page_numbers_layout.itemAt(i)
            widget = item.widget()
            widget.deleteLater()

        for idx, video in enumerate(album.videos):
            page_number = ClickableLabel(video['title'])
            page_number.setAlignment(Qt.AlignCenter)
            page_number.setProperty('index', idx)
            page_number.setStyleSheet("background-color: lightgray;")
            page_number.clicked.connect(self.on_page_number_clicked)
            self.page_numbers_layout.addWidget(page_number)

    def on_page_number_clicked(self, e):
        idx = e.property('index')

        for i in range(self.page_numbers_layout.count()):
            item = self.page_numbers_layout.itemAt(i)
            widget = item.widget()
            if i == idx:
                widget.setStyleSheet("background-color: gray;")
            else:
                widget.setStyleSheet("background-color: lightgray;")

        video = self.album.videos[idx]
        if Config().isPC:
            # 创建对话框并显示
            dialog = MyDialog()
            if dialog.exec_() == QDialog.Accepted:
                self.open(video)
            else:
                self.download_one(video)

    def open(self, video):
        import webbrowser
        if 'm3u8' in video['url']:
            webbrowser.open(f"https://video.isyour.love/Search/SearchJx?t=&id={video['url']}")
        else:
            webbrowser.open(video['url'])

    def download_one(self, video):
        self.m3u8_gui.setVisible(True)
        self.scroll_area.setVisible(False)

        self.m3u8_gui.input_m3u8.setText(f"{video['title']}${video['url']}")

    def on_download_all_button_clicked(self):
        self.m3u8_gui.setVisible(True)
        self.scroll_area.setVisible(False)

        result = ""
        for video in self.album.videos:
            result += f"{video['title']}${video['url']}\n"
        self.m3u8_gui.input_m3u8.setText(result)


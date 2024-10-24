
from commons.image_label import ClickableLabel, ImageLabel
from engine import *
from commons.page import *
from PySide6.QtCore import Qt
from commons.FlowLayout import FlowLayout

class DetailPage(Page):
    def __init__(self, album: Album, engine: Engine):
        super().__init__()

        self.title = album.title

        # 创建图片标签 (这里可以设置为真实图片)
        image_label = ImageLabel()
        image_label.setFixedSize(QSize(200, 240))

        # 创建文本标签，显示 item 中的某个字段
        text_label = QLabel() 

        # 创建一个水平布局，用于图片和文本标签的组合
        hbox = QHBoxLayout()
        hbox.addWidget(image_label)
        hbox.addWidget(text_label)
        self.layout.addLayout(hbox)

        # 创建滚动区域
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # 创建内部部件和网格布局
        inner_widget = QWidget()
        self.page_numbers_layout = FlowLayout(inner_widget, margin=10, spacing=10)
        # 将内部部件设置到滚动区域
        scroll_area.setWidget(inner_widget)
        self.layout.addWidget(scroll_area)
        
        self.album = engine.get_album_detail(album)

        image_label.load_image_from_url(self.album.img)
        text = f"<b>{self.album.title}</b><br> {self.album.source}, 更新时间:{self.album.date}"
        text_label.setText(text)

        self.build_page_numbers_layout(self.album)
        

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
            if idx == 0:
                page_number.setStyleSheet("background-color: gray;")
            else:
                page_number.setStyleSheet("background-color: lightgray;")

            page_number.clicked.connect(self.on_page_number_clicked)
            self.page_numbers_layout.addWidget(page_number)

    def on_page_number_clicked(self, e):
        page_index = e.property('index')

        for i in range(self.page_numbers_layout.count()):
            item = self.page_numbers_layout.itemAt(i)
            widget = item.widget()
            if i == page_index:
                widget.setStyleSheet("background-color: gray;")
            else:
                widget.setStyleSheet("background-color: lightgray;")

        video = self.album.videos[page_index]
        
        import webbrowser
        if 'm3u8' in video['url']:
            webbrowser.open(f"https://video.isyour.love/Search/SearchJx?t=&id={video['url']}")
        else:
            webbrowser.open(video['url'])

        # vc = PlayerPage(video_title=video['title'], video_url=video['url'])
        # self.push(vc)

        # import pyperclip
        # pyperclip.copy(video['url'])

        # msg_box = QMessageBox()
        # msg_box.setText(f"已复制{video['title']}的链接地址！")
        # msg_box.setWindowTitle("信息对话框")
        # msg_box.setIcon(QMessageBox.Information)
        # msg_box.exec()





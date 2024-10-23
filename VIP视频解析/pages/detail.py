
from commons.image_label import ClickableLabel, ImageLabel
from engine import *
from commons.page import *
from PySide6.QtCore import Qt
from commons.FlowLayout import FlowLayout

kImageHeight = 300
kImageWidth = 200

class DetailPage(Page):
    def __init__(self, album: Album, engine: Engine):
        super().__init__()

        self.title = album.title
        self.album = album

        # 创建图片标签 (这里可以设置为真实图片)
        image_label = ImageLabel(size=(kImageWidth, kImageHeight))
                
        # 将 album 数据绑定到 QLabel 的属性中
        image_label.setProperty("id", album.id)

        # 创建文本标签，显示 item 中的某个字段
        text_label = QLabel() 
        
        # 创建一个水平布局，用于图片和文本标签的组合
        hbox = QHBoxLayout()
        hbox.addWidget(image_label)
        hbox.addWidget(text_label)
        self.layout.addLayout(hbox)

        self.page_numbers_layout = FlowLayout(margin=5, spacing=5)
        self.layout.addLayout(self.page_numbers_layout)
        
        album = engine.get_album_detail(album)
        self.build_page_numbers_layout(album)

        image_label.load_image_from_url(album.img)
        
        text = f"<b>{album.title}</b><br> {album.source}, 更新时间:{album.date}"
        text_label.setText(text)


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
        webbrowser.open(f"https://video.isyour.love/Search/SearchJx?t=&id={video['url']}")

        # vc = PlayerPage(video_title=video['title'], video_url=video['url'])
        # self.push(vc)

        import pyperclip
        pyperclip.copy(video['url'])

        # msg_box = QMessageBox()
        # msg_box.setText(f"已复制{video['title']}的链接地址！")
        # msg_box.setWindowTitle("信息对话框")
        # msg_box.setIcon(QMessageBox.Information)
        # msg_box.exec()





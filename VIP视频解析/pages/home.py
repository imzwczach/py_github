
from commons.image_label import ClickableLabel, ImageLabel
from engine import Album, EngineWKVip
from commons.page import *
from pages.detail import DetailPage

kImageHeight = 120
kImageWidth = 80

class CustomWidget(QWidget):
    def __init__(self, album:Album):
        super().__init__()

        self.album = album

        self.content_layout = QVBoxLayout()

        # 创建图片标签 (这里可以设置为真实图片)
        image_label = ImageLabel(size=(kImageWidth, kImageHeight))
                
        # 将 album 数据绑定到 QLabel 的属性中
        image_label.setProperty("id", album.id)

        # 连接点击信号到处理函数
        image_label.clicked.connect(lambda: self.on_label_clicked(album))

        # 创建文本标签，显示 item 中的某个字段
        text = f"<b>{album.title}</b><br> {album.source}"
        text_label = QLabel(text) 
        
        # 创建一个水平布局，用于图片和文本标签的组合
        hbox = QHBoxLayout()
        hbox.addWidget(image_label)
        hbox.addWidget(text_label)

        self.setLayout(hbox)
    
    def title(self):
        return self.album.title

class HomePage(ListPage):
    def __init__(self, title):
        super().__init__(title)

        top_layout = QHBoxLayout()
        
        self.combo_box = QComboBox()
        self.combo_box.addItem("列表项1")
        self.combo_box.addItem("列表项2")
        
        self.line_edit = QLineEdit()
        self.button = QPushButton("按钮")
        self.button.clicked.connect(self.reload_data)
        
        top_layout.addWidget(self.combo_box)
        top_layout.addWidget(self.line_edit)
        top_layout.addWidget(self.button)
        
        self.layout.addLayout(top_layout)
        
        self.setStyleSheet("background:#dddddd;padding:5px;")
        self.itemHeight = kImageHeight+20
        self.set_delegate(self)
        self.albums = None

    def list_page_items(self, list_widget):
        # self.albums = EngineWKVip().get_albums(self.line_edit.text().strip())
        self.albums = EngineWKVip().get_albums('吞噬星空')
        return [CustomWidget(m) for m in self.albums]

    def list_page_item_selected(self, item, index):
        detail_page = DetailPage(self.albums[index])
        self.push(detail_page)

    def showEvent(self, event):
        self.reload_data()

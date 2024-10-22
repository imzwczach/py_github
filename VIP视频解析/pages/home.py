
from commons.config import Config
from commons.image_label import ClickableLabel, ImageLabel
from engine import Album, EngineWKVip
from commons.page import *
from pages.detail import DetailPage
from PySide6.QtWidgets import QCompleter

kImageHeight = 80
kImageWidth = 70

class CustomWidget(QWidget):
    def __init__(self, album:Album):
        super().__init__()

        self.album = album

        # self.content_layout = QVBoxLayout()

        # # 创建图片标签 (这里可以设置为真实图片)
        # image_label = ImageLabel(size=(kImageWidth, kImageHeight))
                
        # # 将 album 数据绑定到 QLabel 的属性中
        # image_label.setProperty("id", album.id)

        # 创建文本标签，显示 item 中的某个字段
        text = f"<b>{album.title}</b>&emsp; <span style='font-size:12px'>{album.source}</span>"
        text_label = QLabel(text) 
        
        # # 创建一个水平布局，用于图片和文本标签的组合
        hbox = QHBoxLayout()
        # hbox.addWidget(image_label)
        hbox.addWidget(text_label)

        self.setLayout(hbox)
    
    def title(self):
        return self.album.title

class HomePage(ListPage):
    def __init__(self, title):
        super().__init__(title)

        top_layout = QHBoxLayout()
        
        self.combo_box = QComboBox(self)
        self.combo_box.setFixedHeight(30)
        self.combo_box.addItem("我看VIP")
        self.combo_box.addItem("todo")
        top_layout.addWidget(self.combo_box)
        
        # 搜索输入框 (QComboBox)
        self.search_box = QComboBox(self)
        self.search_box.setEditable(True)  # 设置可编辑
        self.search_box.setFixedHeight(30)
        top_layout.addWidget(self.search_box)

        # 搜索按钮
        self.search_button = QPushButton("搜索", self)
        self.search_button.setFixedSize(60, 30)
        self.search_button.clicked.connect(self.reload_data)
        top_layout.addWidget(self.search_button)
                
        self.layout.addLayout(top_layout)
        
        self.setStyleSheet("background:#dddddd;padding:5px;")
        self.itemHeight = 50
        self.set_delegate(self)
        self.albums = None

        # 历史记录
        self.history = Config().search_history
        self.update_completer()  # 初始化自动完成器

    def list_page_items(self, list_widget):
        search_text = self.search_box.currentText()
        self.albums = EngineWKVip().get_albums(search_text)
        # self.albums = EngineWKVip().get_albums('吞噬星空')

        # 更新历史记录
        search_text = self.search_box.currentText()
        if search_text and search_text not in self.history:
            self.history.append(search_text)
            Config().save_search_history(self.history)  # 保存历史记录到文件
            self.update_completer()  # 更新自动完成器

        return [CustomWidget(m) for m in self.albums]

    def list_page_item_selected(self, item, index):
        detail_page = DetailPage(self.albums[index])
        self.push(detail_page)

    def showEvent(self, event):
        self.reload_data()

    def update_completer(self):
        # 更新 QCompleter，用于实时提示用户输入的匹配历史记录
        completer = QCompleter(self.history, self)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.search_box.setCompleter(completer)

        # 更新 QComboBox 的选项
        self.search_box.clear()
        self.search_box.addItems(self.history)

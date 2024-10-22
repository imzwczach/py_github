
from commons.image_label import ClickableLabel, ImageLabel
from engine import EngineWKVip
from commons.page import *
from pages.detail import DetailPage

class HomePage(Page):
    def __init__(self, title):
        super().__init__(title)

        top_layout = QHBoxLayout()
        
        self.combo_box = QComboBox()
        self.combo_box.addItem("列表项1")
        self.combo_box.addItem("列表项2")
        
        self.line_edit = QLineEdit()
        self.button = QPushButton("按钮")
        self.button.clicked.connect(self.fetch_data)
        
        top_layout.addWidget(self.combo_box)
        top_layout.addWidget(self.line_edit)
        top_layout.addWidget(self.button)
        
        self.layout.addLayout(top_layout)
        
        self.content_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        container = QFrame()
        container.setLayout(self.content_layout)
        self.scroll_area.setWidget(container)
        
        self.layout.addWidget(self.scroll_area)

    def fetch_data(self):
        engine = EngineWKVip()
        try:
            # albums = engine.get_albums(self.line_edit.text().strip())
            albums = engine.get_albums('吞噬星空')

            # 清除现有布局中的所有元素
            self.clear_layout(self.content_layout)
            
            # 动态生成新的图片和文本标签
            for album in albums:
                # 创建图片标签 (这里可以设置为真实图片)
                image_label = ImageLabel(size=(80, 140))
                        
                # 将 album 数据绑定到 QLabel 的属性中
                image_label.setProperty("id", album.id)

                # 创建文本标签，显示 item 中的某个字段
                text = f"<b>{album.title}</b><br> {album.source}"
                text_label = ClickableLabel(text) 
                
                # 创建一个水平布局，用于图片和文本标签的组合
                hbox = QHBoxLayout()
                hbox.addWidget(image_label)
                hbox.addWidget(text_label)
                
                # 创建一个小的容器 (QFrame) 来包含这个布局
                frame = QFrame()
                frame.setLayout(hbox)
                
                # 将这个组合容器添加到内容布局中
                self.content_layout.addWidget(frame)

                # 连接点击信号到处理函数
                image_label.clicked.connect(lambda: self.on_label_clicked(album))
            
            # 更新布局以反映变化
            self.update()
            
            # engine.on_got_album_detail_signal.connect(self.on_got_album_detail)

            # thread = threading.Thread(target=lambda: engine.get_albums_details(albums))
            # thread.start()

        except Exception as e:
            print(f"数据获取失败: {e}")

    def clear_layout(self, layout):
        """清除布局中的所有小部件"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


    def on_label_clicked(self, album):
        vc = DetailPage(album)
        self.navigation_controller.push(vc)

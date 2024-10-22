from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import threading
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                               QHBoxLayout, QScrollArea, QStackedWidget, QComboBox, 
                               QLineEdit, QPushButton, QFrame, QLabel)
from PySide6.QtCore import Signal, Slot, QObject
from image_label import ImageLabel, ClickableLabel
from config import Config

class Album:
    def __init__(self, title, nums=None, id=None, source=None, img=None, url=None, flag=None) -> None:
        self.title = title
        self.nums = nums
        self.id = id
        self.source = source
        self.img = img
        self.url = url
        self.videos = None 
        self.flag = flag

    def __str__(self):
        # 返回可读性强的字符串
        # 通过 __dict__ 获取属性和值
        attributes = ', '.join([f"{key}={value!r}" for key, value in self.__dict__.items()])
        return f"{self.__class__.__name__}({attributes})"

class Engine(QObject):
    on_got_album_detail_signal = Signal(object)

    # def get_reponse_data(self, url):
    #     try:
    #         response = requests.get(url)
    #         response.raise_for_status()
    #         data = response.json()  # 解析为 JSON 数据
    #         return data
    #     except Exception as e:
    #         raise Exception(f'请求{url},发生错误:{e}')

    def get_albums(self, keyword):
        pass

    def get_albums_details(self, albums):
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 为每个URL分配任务
            futures = [executor.submit(self.__get_album_detail, album) for album in albums]
            
        for future in as_completed(futures):
            result = future.result()
            if result:  # 如果下载成功，发送信号
                album = self.schedule_album_detail(result[0], result[1])
                self.on_got_album_detail_signal.emit(album)

    def schedule_album_detail(self, album: Album, data: dict):
        pass

    def __get_album_detail(self, album):
        data = Config().request_data(album.url, 60*60)
        return album, data

# https://v.wkvip.net/
class EngineWKVip(Engine):

    def get_albums(self, keyword):
        url = "https://a.wkvip.net/api.php?tp=jsonp&wd="+keyword
        data = Config().request_data(url, 60*60)
        items = data.get('info', [])
        albums = [
            Album(title=item['title'],
                   id=item['id'], 
                   source=item['from'], 
                   flag=item['flag'], 
                   url=f"https://a.wkvip.net/api.php?out=json&flag={item['flag']}&id={item['id']}"
                ) for item in items]        
        return albums
        
    def schedule_album_detail(self, album: Album, data: dict):
        album.img = data['pic']
        items = data.get('info', [])
        if len(items):
            album.nums = items[0]['part']
            videos = items[0]['video']
            arr = []
            for v in videos:
                parts = v.split('$')
                if len(parts) > 1:
                    arr.append({'title': parts[0], 'url': parts[1]})
            album.videos = arr
        return album

class ImageGridApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        self.main_layout = QVBoxLayout()
        
        self.stacked_widget = QStackedWidget()  # 创建堆栈小部件

        self.main_layout.addWidget(self.stacked_widget)

        # 添加首页
        self.home_page = QWidget()
        self.init_home_page()
        self.stacked_widget.addWidget(self.home_page)  # 将首页添加到堆栈
        
        # 设置主布局
        self.setLayout(self.main_layout)
        self.setWindowTitle("图片示例程序")
        self.setGeometry(300, 300, 400, 600)

    def init_home_page(self):
        layout = QVBoxLayout()
        
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
        
        layout.addLayout(top_layout)
        
        self.content_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        container = QFrame()
        container.setLayout(self.content_layout)
        self.scroll_area.setWidget(container)
        
        layout.addWidget(self.scroll_area)
        self.home_page.setLayout(layout)
        
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
                text_label.clicked.connect(lambda: self.on_label_clicked(album))

            
            # 更新布局以反映变化
            self.update()
            
            # engine.on_got_album_detail_signal.connect(self.on_got_album_detail)

            # thread = threading.Thread(target=lambda: engine.get_albums_details(albums))
            # thread.start()

        except Exception as e:
            print(f"数据获取失败: {e}")

    def on_got_album_detail(self, album):
        image_label, text_label = self.find_album_widgets(album)
        image_label.load_image_from_url(album.img)

        text = f"<b>{album.title}</b><br>共{album.nums}集，{album.source}"
        text_label.setText(text)
    
    @Slot(object)
    def find_album_widgets(self, album):
        """
        根据 album 对象找到对应的图片和文本标签
        """
        for i in range(self.content_layout.count()):
            frame = self.content_layout.itemAt(i).widget()
            if frame:
                # 在 frame 中找到图片标签
                image_label = frame.layout().itemAt(0).widget()
                if image_label.property("id") == album.id:
                    # 找到对应的图片和文本标签
                    text_label = frame.layout().itemAt(1).widget()
                    return image_label, text_label
        return None, None

    def clear_layout(self, layout):
        """清除布局中的所有小部件"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    @Slot(object)
    def on_label_clicked(self, album):
        new_page = QWidget()  # 创建新的页面
        new_layout = QVBoxLayout()
        new_layout.addWidget(QLabel(f"你选择了: {album.title}"))
        new_page.setLayout(new_layout)
        
        self.stacked_widget.addWidget(new_page)  # 将新页面添加到堆栈
        self.stacked_widget.setCurrentWidget(new_page)  # 切换到新页面


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageGridApp()
    ex.show()
    sys.exit(app.exec())

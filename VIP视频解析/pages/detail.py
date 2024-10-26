
import threading
import time
from PySide6.QtGui import QCloseEvent
from commons.image_label import ClickableLabel, ImageLabel
from engine import *
from commons.page import *
from PySide6.QtCore import Qt
from commons.FlowLayout import FlowLayout
from m3u8.m3u8_gui import M3U8DownloadPage


class DetailPage(Page):
    def __init__(self, album: Album, engine: Engine):
        super().__init__()

        self.title = album.title

        # 创建一个水平布局，用于图片和文本标签的组合
        hbox = QHBoxLayout()
        self.layout.addLayout(hbox)

        # 创建图片标签 (这里可以设置为真实图片)
        image_label = ImageLabel()
        image_label.setFixedSize(QSize(200, 240))
        hbox.addWidget(image_label)

        right_box = QVBoxLayout()
        text_label = QLabel() 
        right_box.addWidget(text_label)
        hbox.addLayout(right_box)

        if Config().isPC:
            buttons_layout = QHBoxLayout()
            right_box.addLayout(buttons_layout)

            buttonAll = QPushButton('下载全集')
            buttonAll.setFixedSize(70,30)
            buttonAll.setVisible(Config().isPC)
            buttonAll.clicked.connect(self.on_download_all_button_clicked)
            buttons_layout.addWidget(buttonAll)

            self.display_button = QPushButton('显示剧集')
            self.display_button.setFixedSize(70,30)
            self.display_button.clicked.connect(self.on_show_videos_button_clicked)
            buttons_layout.addWidget(self.display_button)
            self.display_button.setVisible(False)

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
        except:
            return

        text = f"<b>{self.album.title}</b><br> {self.album.source}, 更新时间:{self.album.date}"
        text_label.setText(text)
        text_label.setMinimumWidth(200)
        text_label.setWordWrap(True)
        self.text_label = text_label

        self.build_page_numbers_layout(self.album)

        if Config().isPC:
            self.m3u8_gui = M3U8DownloadPage(ban_ads=engine.ban_ads)
            self.m3u8_gui.setVisible(False)
            self.layout.addWidget(self.m3u8_gui)

        self.thread = threading.Thread(target=lambda: (time.sleep(0.2), self.test_speed()))
        self.thread.start()

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

            msgBox = QMessageBox()
            msgBox.setWindowTitle("提示")
            msgBox.setText("选择操作")
            # 添加自定义按钮
            button1 = msgBox.addButton("播放", QMessageBox.AcceptRole)
            button2 = msgBox.addButton("下载", QMessageBox.AcceptRole)
            button3 = msgBox.addButton("取消", QMessageBox.RejectRole)
            # 设置默认按钮
            msgBox.setDefaultButton(button3)
            # 显示对话框并捕获用户的选择
            result = msgBox.exec_()
            # 判断用户选择了哪个按钮
            if msgBox.clickedButton() == button1:
                self.open(video)
            elif msgBox.clickedButton() == button2:
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
        self.display_button.setVisible(True)

        self.m3u8_gui.input_m3u8.setText(f"{video['title']}${video['url']}")

    def on_download_all_button_clicked(self):
        self.m3u8_gui.setVisible(True)
        self.scroll_area.setVisible(False)
        self.display_button.setVisible(True)

        result = ""
        for video in self.album.videos:
            result += f"{video['title']}${video['url']}\n"
        self.m3u8_gui.input_m3u8.setText(result)

    def on_show_videos_button_clicked(self):
        self.m3u8_gui.setVisible(False)
        self.scroll_area.setVisible(True)
        self.display_button.setVisible(False)

    def willDestory(self):
        if self.m3u8_gui.m3u8_downloader:
            self.m3u8_gui.m3u8_downloader.finished.emit()

    def test_speed(self):
        from m3u8.m3u8_downloader import M3u8Downloader
        from m3u8.test_speed import TestSpeedThread

        # self.text_label.setText(self.old_text+"<br><span style='color:red;'>测速: - Mb/s</span>")
        text = self.text_label.text()
        result = ""
        href = None
        for video in self.album.videos:
            if 'm3u8' in video['url']:
                result += f"{video['title']}${video['url']}\n"
            else:
                href = video['url']
        if href:
            text += f"<br><span style='color:red;'>无效链接:{href}</span>"
            self.text_label.setText(text)
            return
        
        self.m3u8_downloader = M3u8Downloader(result)
        m3u8_info = self.m3u8_downloader.m3u8_infos[0]#random.choice(self.m3u8_downloader.m3u8_infos)

        lines = self.m3u8_downloader.get_ts_lines(m3u8_info['url'])
        urls = []
        for line in lines:
            if line.startswith('http'):
                urls.append(line)
        if len(urls):
            text += f"<br><span style='color:red;'>切片数:{len(urls)}</span>"
            self.text_label.setText(text)

            # self.test_speed_thread = TestSpeedThread(urls)
            # self.test_speed_thread.test_speed_done_signal.connect(self.test_speed_done)
            # self.test_speed_thread.start()
        else:
            text += "<br><span style='color:red;'>失效资源</span>"
            self.text_label.setText(text)

    # def test_speed_done(self, avg_speed, ts_count, estimate_mb):
    #     self.text_label.setText(self.old_text+f"<br><span style='color:red;'>测速: {avg_speed:.2f} Mb/S, 切片数:{ts_count}, 估算: {estimate_mb:.0f}MB</span>")
    #     self.test_speed_thread.stop()
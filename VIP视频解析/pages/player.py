from commons.page import *
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
import sys

class PlayerPage(Page):
    def __init__(self, video_title, video_url):
        super().__init__()

        self.title = video_title
        self.url = video_url

        web_view = QWebEngineView(self)

        url = f"https://video.isyour.love/player/getplayer?url={self.url}&title={self.title}"

        # 或者加载在线HTML5播放器网页
        web_view.load(url)
        # https://jx.xmflv.com/?url=
        # https://video.isyour.love/Search/SearchJx?t=&id=
        # https://jiexi.modujx01.com/?url=

        self.layout.addWidget(web_view)


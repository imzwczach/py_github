
from commons.image_label import ClickableLabel, ImageLabel
from engine import EngineWKVip
from commons.page import *

class DetailPage(Page):
    def __init__(self, album):
        super().__init__()

        self.title = album.title

        new_layout = QVBoxLayout()
        new_layout.addWidget(QLabel(f"你选择了: {album.title}"))
        self.layout.addLayout(new_layout)


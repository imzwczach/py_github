import sys
from PySide6.QtWidgets import (QApplication, QWidget)
from commons.page import *
from engine import *
from pages.home import HomePage

class ImageGridApp(QWidget):
    def __init__(self):
        super().__init__()

        # 设置窗口标题和大小
        self.setWindowTitle("VIP视频解析")
        self.resize(430, 932)

        home_page = HomePage('列表')
        self.nav_controller1 = NavigationController(home_page)
        self.setLayout(self.nav_controller1.layout)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = ImageGridApp()
    ex.show()
    sys.exit(app.exec())

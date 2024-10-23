import sys
from PySide6.QtWidgets import (QApplication, QWidget)
from pages.page_etf_list import ETFListPage
from commons.page import *

class App(QWidget):
    def __init__(self):
        super().__init__()

        # 设置窗口标题和大小
        self.setWindowTitle("VIP视频解析")
        self.resize(420, 800)

        home_page = ETFListPage()
        self.nav_controller1 = NavigationController(home_page)
        self.setLayout(self.nav_controller1.layout)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec())

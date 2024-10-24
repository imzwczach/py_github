
from PySide6.QtWidgets import QWidget
from commons.config import Config
from commons.image_label import ClickableLabel, ImageLabel
from engine import *
from commons.page import *
from pages.detail import DetailPage
from pages.search import SearchPage
from pages.widgets import CustomWidget, GridWidget

class HomePage(Page, ListPageDelegate, GridPageDelegate):
    def __init__(self, title):
        super().__init__(title)
        
        top_layout = QHBoxLayout()
        
        self.combo_box = QComboBox(self)
        self.combo_box.setFixedHeight(30)
        
        self.engines = []
        for conf in Config().engines:
            if 'search' in conf and conf['search']:
                pass
            else:
                self.combo_box.addItem(conf['name'])

                cls = globals().get(conf['cls'])
                if cls is Engine or issubclass(cls, Engine):
                    engine = cls(conf)
                    self.engines.append(engine)
        self.engine = self.engines[0]

        top_layout.addWidget(self.combo_box)
        self.combo_box.currentIndexChanged.connect(self.engine_changed_index)
        
        # 搜索按钮
        self.search_button = QPushButton("搜索", self)
        self.search_button.setStyleSheet("background:red; color:white;")
        self.search_button.setFixedSize(60, 30)
        self.search_button.clicked.connect(self.on_search)
        top_layout.addWidget(self.search_button)

        self.layout.addLayout(top_layout)

        self.listPage = ListPage()
        self.listPage.set_delegate(self)
        self.listPage.itemHeight = 100 if self.engine.has_thumb else 50
        self.layout.addWidget(self.listPage)

        self.gridPage = GridPage()
        self.gridPage.set_delegate(self)
        self.gridPage.itemHeight = 100 if self.engine.has_thumb else 50
        self.layout.addWidget(self.gridPage)

        if not self.engine.grid:
            # self.layout.addWidget(self.listPage)
            self.gridPage.setVisible(False)
            self.curPage = self.listPage
        else:
            # self.layout.addWidget(self.gridPage)
            self.listPage.setVisible(False)
            self.curPage = self.gridPage

        hhbox = QHBoxLayout()
        prev_button = QPushButton('上一页')
        prev_button.setEnabled(False)
        prev_button.clicked.connect(self.on_prev_page_button)
        hhbox.addWidget(prev_button)
        self.pre_button = prev_button
        
        next_button = QPushButton('下一页')
        next_button.clicked.connect(self.on_next_page_button)
        hhbox.addWidget(next_button)
        self.layout.addLayout(hhbox)
        self.pageIndex = 1

    def engine_changed_index(self, index):
        self.engine = self.engines[index]
        page = None
        if self.engine.grid:
            page = self.gridPage
        else:
            page = self.listPage

        if page is not self.curPage:
            # self.layout.removeWidget(self.curPage)
            self.curPage.setVisible(False)
            page.setVisible(True)
            # self.layout.addWidget(page)
            self.curPage = page

        page.itemHeight = 100 if self.engine.has_thumb else 50
        self.reload_data()

    def reload_data(self):
        self.albums = self.engine.get_albums(page=self.pageIndex)
        self.curPage.reload_data()

    def list_page_items(self, list_widget):
        return [CustomWidget(m) for m in self.albums]

    def list_page_item_selected(self, item, index):
        detail_page = DetailPage(self.albums[index], self.engine)
        self.push(detail_page)

    def cols_for_grid_page(self):
        return 3
    
    def grid_item_size(self):
        return QSize(120, 150)

    def grid_page_items(self):
        return [GridWidget(m) for m in self.albums]
    
    def grid_item_selected(self, item: QWidget, index):
        album = self.albums[index]
        vc = SearchPage(album.title)
        self.push(vc)

    def showEvent(self, event):
        self.reload_data()

    def on_search(self):
        vc = SearchPage()
        self.push(vc)

    def on_prev_page_button(self):
        self.pageIndex = max(1, self.pageIndex-1)            
        self.pre_button.setEnabled(self.pageIndex>1)
        self.reload_data()

    def on_next_page_button(self):
        self.pageIndex += 1
        self.pre_button.setEnabled(True)
        self.reload_data()

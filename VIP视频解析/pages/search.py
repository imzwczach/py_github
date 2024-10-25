from commons.config import Config
from engine import *
from commons.page import *
from pages.detail import DetailPage
from PySide6.QtWidgets import QCompleter, QLayout

from pages.widgets import CustomWidget

class SearchPage(ListPage):
    def __init__(self, title=None):
        super().__init__(title)

        self.title = title or "搜索"

        top_layout = QHBoxLayout()
        
        self.combo_box = QComboBox(self)
        self.combo_box.setFixedHeight(30)
        
        self.engines = []
        for conf in Config().engines:
            if 'search' in conf and conf['search']:
                self.combo_box.addItem(conf['name'])

                cls = globals().get(conf['cls'])
                if cls is Engine or issubclass(cls, Engine):
                    engine = cls(conf)
                    self.engines.append(engine)

        self.engine = self.engines[0]

        top_layout.addWidget(self.combo_box)
        self.combo_box.currentIndexChanged.connect(self.engine_changed_index)
        
        # 搜索输入框 (QComboBox)
        self.search_box = QComboBox(self)
        self.search_box.setEditable(True)  # 设置可编辑
        self.search_box.setFixedSize(150,30)
        top_layout.addWidget(self.search_box)

        # 搜索按钮
        self.search_button = QPushButton("搜索", self)
        self.search_button.setStyleSheet("background:red; color:white;")
        self.search_button.setFixedSize(60, 30)
        self.search_button.clicked.connect(self.reload_data)
        top_layout.addWidget(self.search_button)
                
        self.layout.addLayout(top_layout)
        
        self.itemHeight = 100 if self.engine.has_thumb else 50
        self.set_delegate(self)
        self.albums = []
        
        # 历史记录
        self.history = Config().search_history
        if title:
            searchText = self._extract_chinese_and_numbers(title)
            self.search_box.setCurrentText(searchText)
        else:
            self.update_completer()  # 初始化自动完成器
            
    def engine_changed_index(self, index):
        self.engine = self.engines[index]
        self.reload_data()

    def reload_data(self):
        search_text = self.search_box.currentText()
        if search_text:
            try:
                albums = self.engine.search_albums(search_text)
                self.albums = []
                ignores = ['解说', '真人', '动态', '粤语', '预告']
                for album in albums:
                    if not any(ignore in album.title for ignore in ignores):
                        self.albums.append(album)
                
                # 更新历史记录
                search_text = self.search_box.currentText()
                if search_text and search_text not in self.history:
                    self.history.append(search_text)
                    Config().save_search_history(self.history)  # 保存历史记录到文件

            except Exception as e:
                print(f'错误{e}')
                msg_box = QMessageBox()
                msg_box.setText(f"错误：{e}")
                msg_box.setWindowTitle("发生错误")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.exec()
                return
            super().reload_data()

    def list_page_items(self, list_widget):
        return [CustomWidget(m) for m in self.albums]

    def list_page_item_selected(self, item, index):
        detail_page = DetailPage(self.albums[index], self.engine)
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

    def _extract_chinese_and_numbers(self, text):
        pattern = r'[\u4e00-\u9fa5]+|[\u3400-\u4DBF\uF900-\uFAFF]+|\d+'
        return "".join(re.findall(pattern, text))

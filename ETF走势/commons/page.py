
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import *
from PySide6.QtCore import *

class Page(QWidget):
    """自定义基础页面类，类似iOS的UIViewController"""
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.title = title or '标题' # 页面标题
        self.navigation_controller = None
        self.setStyleSheet("background-color: #f2f2f2; font-size: 14px;")

        # 创建垂直布局
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)  # 控件间距为 0
        self.layout.setContentsMargins(0, 0, 0, 0)  # 去除边距

    def push(self, page):
        if self.navigation_controller and page:
            self.navigation_controller.push(page)

    def pop(self):
        if self.navigation_controller:
            self.navigation_controller.pop()
        
class ListPageDelegate:
    def list_page_items(list_widget:QListWidget):
        pass
    def list_page_item_selected(item, index):
        pass

class ListPage(Page):

    cell_selected = Signal(object, int)

    """继承自Page的列表页面类，类似iOS的UITableViewController"""
    def __init__(self, title=None):
        super().__init__(title)
        self.__delegate = None
        self.__items = []
        self.itemHeight = 30

        # 创建一个 QListWidget 并添加到布局中
        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)

        # 自定义样式
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #F0F0F0;
            }
            /*QListWidget::item {
                height: 40px;  设置每个项的高度
            } */
            QListWidget::item:selected {
                background-color: #87CEFA;  /* 设置选中项的背景色 */
            }
        """)

        # 绑定列表项点击事件
        self.list_widget.itemClicked.connect(self.select_item)

    def set_delegate(self, delegate):
        self.__delegate = delegate

    def add_items(self, items):
        """添加项目到 QListWidget 并为每个项目生成对应的页面"""
        self.__items = items

        for itm in items:
            # 添加列表项
            list_item = None
            if isinstance(itm, str):
                list_item = QListWidgetItem(itm, self.list_widget)
            elif isinstance(itm, QWidget):
                # 创建 QListWidgetItem
                list_item = QListWidgetItem(self.list_widget)
                # 将自定义小部件添加到 QListWidgetItem 中
                self.list_widget.setItemWidget(list_item, itm)
            elif isinstance(itm, QListWidgetItem):
                list_item = itm
                self.list_widget.addItem(list_item)

            list_item.setSizeHint(QSize(0, self.itemHeight))  # 设置项目的高度为 40 像素

    def select_item(self, item):
        """显示点击的项目对应的页面"""
        # item_text = item.text()
        index = self.list_widget.currentIndex().row()

        self.cell_selected.emit(item, self.__items[index])

        if self.__delegate and hasattr(self.__delegate, 'list_page_item_selected'):
            self.__delegate.list_page_item_selected(self.__items[index], index)

    def reload_data(self):
        if self.__delegate and hasattr(self.__delegate, 'list_page_items'):
            self.list_widget.clear()
            self.add_items(self.__delegate.list_page_items(self.list_widget))

class NavigationBar(QWidget):
    """自定义导航栏，管理标题和返回按钮"""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(40)
        self.setStyleSheet("background-color: #2C3E50; color: white; font-size: 16px;")
        self.layout = QHBoxLayout(self)

        # 去除布局内的间距和边距
        self.layout.setSpacing(0)  # 控件间距为 0
        self.layout.setContentsMargins(0, 0, 0, 0)  # 去除边距

        # 返回按钮
        self.back_button = QLabel("  <", self)
        self.back_button.setFixedSize(36, 40)
        self.back_button.setVisible(False)  # 初始隐藏
        self.layout.addWidget(self.back_button)

        # 页面标题
        self.title_label = QLabel("", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFixedHeight(40)
        self.layout.addWidget(self.title_label)

    def set_title(self, title):
        """设置导航栏标题"""
        self.title_label.setText(title)

    def show_back_button(self, show):
        """显示或隐藏返回按钮"""
        self.back_button.setVisible(show)

class NavigationController(QWidget):
    """自定义导航控制器，类似iOS的UINavigationController"""
    def __init__(self, initial_page, parent=None):
        super().__init__(parent)
        
        initial_page.navigation_controller = self
        self.title = initial_page.title

        # 创建垂直布局
        self.layout = QVBoxLayout(self)
        self.page_stack = []  # 页面栈

        # 创建导航栏
        self.nav_bar = NavigationBar(self)
        self.nav_bar.back_button.mousePressEvent = self.onMouseClick
        self.layout.addWidget(self.nav_bar)

        # 创建堆叠窗口，用于管理多个页面
        self.stacked_widget = QStackedWidget(self)
        self.layout.addWidget(self.stacked_widget)

        # 推入初始页面
        self.push(initial_page)

    def onMouseClick(self, event):
        if event.button() == Qt.LeftButton:
            self.pop()

    def push(self, page):
        """将页面推入堆栈，并更新导航栏"""
        self.page_stack.append(page)
        self.stacked_widget.addWidget(page)
        self.stacked_widget.setCurrentWidget(page)
        self.nav_bar.set_title(page.title)
        page.navigation_controller = self

        # 如果是根页面，隐藏返回按钮
        self.nav_bar.show_back_button(len(self.page_stack) > 1)

    def pop(self):
        """弹出顶部页面，并更新导航栏"""
        if len(self.page_stack) > 1:
            # 弹出当前页面
            popped_page = self.page_stack.pop()
            self.stacked_widget.removeWidget(popped_page)

            # 显示前一个页面
            current_page = self.page_stack[-1]
            self.stacked_widget.setCurrentWidget(current_page)
            self.nav_bar.set_title(current_page.title)

            # 如果返回到根页面，隐藏返回按钮
            self.nav_bar.show_back_button(len(self.page_stack) > 1)
    
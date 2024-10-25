import re

import pyperclip
from PyQt5.QtWidgets import QLineEdit


class AutoPasteLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(AutoPasteLineEdit, self).__init__(parent)

    def mousePressEvent(self, event):
        # 检查鼠标点击的按钮是否是左右键
        if event.button() == 1 or event.button() == 2:  # 2 是 Qt.RightButton
            if self.find_http_url(pyperclip.paste()):
                self.setText(pyperclip.paste())
            event.accept()  # 阻止事件的进一步传播
        else:
            # 处理其他鼠标事件
            super(AutoPasteLineEdit, self).mousePressEvent(event)

    def contextMenuEvent(self, event):
        # 禁用默认的右键上下文菜单
        event.accept()

    def find_http_url(self, text):
        # 正则表达式匹配 http 开头并以 .m3u8 结尾的字符串
        pattern = r'http[s]?://[^\s]+?\.m3u8'
        # 查找所有匹配的字符串
        matches = re.findall(pattern, text)
        # 输出结果
        for match in matches:
            return match
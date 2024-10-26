import os
from PySide6.QtWidgets import QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QProgressBar, QMessageBox
from PySide6.QtCore import QThread

from commons.page import Page
from m3u8.m3u8_downloader import DownloadState, M3u8Downloader

class M3U8DownloadPage(Page):
    def __init__(self, ban_ads=False):
        super().__init__()

        self.init_config()

        # 第一行：输入m3u8链接
        layout1 = QHBoxLayout()
        label_m3u8 = QLabel('输入链接:\n(可多行)')
        label_m3u8.setFixedWidth(80)
        self.input_m3u8 = QTextEdit()
        self.input_m3u8.setMinimumHeight(40)
        self.input_m3u8.setMaximumHeight(200)
        self.input_m3u8.setPlaceholderText("文件名$m3u8链接")
        self.input_m3u8.textChanged.connect(self.m3u8_text_changed)
        layout1.addWidget(label_m3u8)
        layout1.addWidget(self.input_m3u8)

        # 第二行：保存目录
        layout2 = QHBoxLayout()
        label_save = QLabel('保存目录:')
        label_save.setFixedWidth(80)
        self.input_save = QLineEdit()
        btn_browse = QPushButton('选择')
        btn_browse.clicked.connect(self.select_directory)
        layout2.addWidget(label_save)
        layout2.addWidget(self.input_save)
        layout2.addWidget(btn_browse)

        # 第三行：载取时间段
        layout3 = QHBoxLayout()
        label_time = QLabel('截取时间段:')
        label_time.setFixedWidth(80)
        self.time_start = QLineEdit()
        self.time_start.setPlaceholderText("0:00")
        self.time_end = QLineEdit()
        self.time_end.setPlaceholderText("0:00")
        layout3.addWidget(label_time)
        layout3.addWidget(self.time_start)
        layout3.addWidget(QLabel('到'))
        layout3.addWidget(self.time_end)

        # 第四行：文本区域
        layout4 = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlainText("就绪")
        self.input_m3u8.setMinimumHeight(40)
        layout4.addWidget(self.text_area)

        # 第五行：进度条和按钮水平布局
        layout5 = QHBoxLayout()
        # 创建进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)  # 初始值为0
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setVisible(False)
        layout5.addWidget(self.progress_bar)
        self.label_progress = QLabel('0/0')
        self.label_progress.setVisible(False)
        layout5.addWidget(self.label_progress)
        
        layout6 = QHBoxLayout()
        self.lbl_speed = QLabel()
        self.lbl_speed.setStyleSheet("color:red;")
        layout6.addWidget(self.lbl_speed)

        self.btn_download = QPushButton('开始下载')
        self.btn_download.setFixedSize(120, 30)
        self.btn_download.clicked.connect(self.start_download)
        self.btn_download.setEnabled(False)
        layout6.addWidget(self.btn_download)

        # 将所有行添加到主布局中
        self.layout.addLayout(layout1)
        self.layout.addLayout(layout2)
        self.layout.addLayout(layout3)
        self.layout.addLayout(layout4)
        self.layout.addLayout(layout5)
        self.layout.addLayout(layout6)

        # 初始化 configparser
        import configparser
        self.config = configparser.ConfigParser()

        # 读取 ini 文件并设置到第二个文本框
        self.config.read('config.ini')
        if 'settings' in self.config and 'save_directory' in self.config['settings']:
            self.input_save.setText(self.config['settings']['save_directory'])

        # QThread 实例
        self.thread = None
        self.m3u8_downloader = None
        self.ban_ads = ban_ads

    def init_config(self):
        # 获取 AppData\Roaming 目录
        # appdata_roaming = Path(os.getenv('APPDATA'))
        exe_dir = os.getcwd()
        download_dir = os.path.join(exe_dir, 'downloads')
        ini_file_path = os.path.join(exe_dir, 'config.ini')
        if not os.path.exists(ini_file_path):
            with open(ini_file_path, 'w') as f:
                f.write(f"[settings]\nsave_directory = {download_dir}")

    def willDestory(self):
        # 在关闭窗体时，确保停止线程
        if self.thread and self.thread.isRunning():
            self.m3u8_downloader.cancel() # 取消下载任务
            self.thread.quit()  # 发送退出信号
            self.thread.wait()  # 等待线程结束

    def m3u8_text_changed(self):
        if self.input_m3u8.toPlainText().startswith('http'):
            self.input_m3u8.setText('未命名$'+self.input_m3u8.toPlainText())

        is_ready = 'http' in self.input_m3u8.toPlainText()
        self.btn_download.setEnabled(is_ready)

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, '选择文件夹', dir=self.input_save.text())
        if directory:
            self.input_save.setText(directory)

            # 保存选定的目录到 ini 文件
            self.config['settings'] = {'save_directory': directory}
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)

    def start_download(self):
        if self.btn_download.text() == '暂停':
            self.m3u8_downloader.pause()
            self.btn_download.setText('继续')
            return
        elif self.btn_download.text() == '继续':
            self.m3u8_downloader.resume()
            self.btn_download.setText('暂停')
            return

        # 创建 MyWorker 实例并传递参数
        self.m3u8_downloader = M3u8Downloader(
            inputString=self.input_m3u8.toPlainText(),
            dir_path=self.input_save.text(),
            head_time=self.time_start.text(),
            tail_time=self.time_end.text(),
            ban_ads=self.ban_ads
        )
        
        if not self.thread:
            # 创建 QThread 实例
            self.thread = QThread()
            # 在线程开始时，执行 实例 的 run_task 方法
            self.thread.started.connect(self.m3u8_downloader.download_ts_files)
            self.thread.finished.connect(self.thread.deleteLater)

        # 将 实例 移动到 QThread 中运行
        self.m3u8_downloader.moveToThread(self.thread)

        # 连接信号槽，更新 UI
        self.m3u8_downloader.info_signal.connect(self.update_infos_text)
        self.m3u8_downloader.progress_signal.connect(self.update_progress)
        self.m3u8_downloader.download_state_signal.connect(self.download_state_updated)
        self.m3u8_downloader.avg_speed_signal.connect(self.update_speed)
        # 手动关闭线程 接收信号
        self.m3u8_downloader.finished.connect(self.on_m3u8_downloader_finished)

        # 启动线程
        self.thread.start()

        self.input_m3u8.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.label_progress.setVisible(True)
        self.btn_download.setText('暂停')
    
    def on_m3u8_downloader_finished(self):
        self.m3u8_downloader.cancel()
        self.m3u8_downloader = None
        self.thread.quit()
        self.thread.wait()
        self.thread = None

        self.input_m3u8.setEnabled(True)
        self.btn_download.setText("开始下载")
        self.btn_download.setEnabled(True)
        self.progress_bar.setValue(0)
        self.label_progress.setText("0/0")

    def update_infos_text(self, message):
        self.text_area.append(message)

    def update_progress(self, progress_ext):
        self.progress_bar.setValue(progress_ext['value'])
        self.label_progress.setText(f"{progress_ext['current']}/{progress_ext['total']}")

    def update_speed(self, avg_speed):
        self.lbl_speed.setText(f"{avg_speed:.2f} Mb/S")

    def download_state_updated(self, info:tuple):
        (state, download_dir) = info
        if state == DownloadState.DoneAll:
            self.input_m3u8.setEnabled(True)
            self.btn_download.setText('开始下载')
            self.btn_download.setEnabled(False)

            self.open_explorer(self.input_save.text())
        elif state == DownloadState.Lost:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("提示")
            msgBox.setText("部分视频切片下载失败")

            # 添加自定义按钮
            merge_button = msgBox.addButton("确定", QMessageBox.AcceptRole)
            # redownload_button = msgBox.addButton("重新下载", QMessageBox.RejectRole)

            # 设置默认按钮
            msgBox.setDefaultButton(merge_button)

            # 显示对话框并捕获用户的选择
            result = msgBox.exec_()

            # 判断用户选择了哪个按钮
            # if msgBox.clickedButton() == merge_button:
            #     self.m3u8_downloader.process_ffmpeg(download_dir)
            # elif msgBox.clickedButton() == redownload_button:
            #     print("用户选择了重新下载")
            #     self.start_download()

    def open_explorer(self, path):
        rpath = path.replace("\\", "/")
        # 确保路径存在
        if os.path.exists(rpath):
            # 使用explorer打开指定路径 windows
            os.startfile(rpath)
            # 使用open命令打开Finder Mac
            # subprocess.Popen(['open', path])
            # 使用xdg-open打开文件管理器 Linux
            # subprocess.Popen(['xdg-open', path])
        else:
            print(f"路径不存在: {rpath}")

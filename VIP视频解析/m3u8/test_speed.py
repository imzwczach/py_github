import random
import requests
import time
from PySide6.QtCore import QThread, Signal
from concurrent.futures import ThreadPoolExecutor, as_completed

from m3u8.m3u8_downloader import M3u8Downloader

class TestSpeedThread(QThread):
    test_speed_done_signal = Signal(float, int, float)
    
    def __init__(self, inputString):
        super().__init__()
        self.inputString = inputString
        self._stop_flag = False

    def run(self):
        try:
            self.m3u8_downloader = M3u8Downloader(self.inputString)
            m3u8_info = self.m3u8_downloader.m3u8_infos[-1]#random.choice(self.m3u8_downloader.m3u8_infos)

            lines = self.m3u8_downloader.get_ts_lines(m3u8_info['url'])

            if self._stop_flag:
                return

            urls = []
            for line in lines:
                if line.startswith('http'):
                    urls.append(line)
            if len(urls):
                self.urls_total = len(urls)
                self.urls = urls if len(urls)<6 else random.sample(urls, 5)

                average_speed, estimate_total = self.get_download_files_infos(self.urls)
                self.test_speed_done_signal.emit(average_speed, self.urls_total, estimate_total)
            else:
                self.test_speed_done_signal.emit(None, None, None)
                
        except requests.exceptions.RequestException as e:
            self.test_speed_done_signal.emit(None, self.urls_total, None)
    
    def stop(self):
        self._stop_flag = True
        self.quit()
        self.wait()
        self.deleteLater()

    def download_file(self, url):
        response = requests.get(url, stream=True, timeout=5)
        total_size = int(response.headers.get('content-length', 0))
        downloaded_data = b''
        for data in response.iter_content(chunk_size=1024):
            downloaded_data += data
        return len(downloaded_data), url

    def get_download_files_infos(self, urls):
        start_time = time.time()
        download_size = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            # speeds = list(executor.map(self.download_file, urls))
            futures = [executor.submit(self.download_file, url) for url in urls]

        for future in as_completed(futures):
            size, _url = future.result() 
            mb_size = size*8/(1024*1024)
            # print(f'文件{_url}大小：{size}')
            download_size += mb_size

        end_time = time.time()
        speed_in_mbps = download_size / (end_time - start_time)        
        # 估算总大小MB
        estimate_total = download_size/len(urls) * self.urls_total

        return speed_in_mbps, estimate_total

# import sys
# from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout)

# class App11(QWidget):
#     def __init__(self):
#         super().__init__()

#         # 设置窗口标题和大小
#         self.setWindowTitle("VIP视频解析")
#         self.resize(420, 800)

#         layout = QVBoxLayout()

#         str = """第08集$https://bfikuncdn.com/20221102/P6Ud00te/index.m3u8
# 第09集$https://bfikuncdn.com/20221102/D9fVR70H/index.m3u8
# 第10集$https://bfikuncdn.com/20221102/zgvjOZOm/index.m3u8"""

#         self.m3u8_downloader = M3u8Downloader(str)
#         m3u8_info = random.choice(self.m3u8_downloader.m3u8_infos)

#         lines = self.m3u8_downloader.get_ts_lines(m3u8_info['url'])
#         urls = []
#         for line in lines:
#             if line.startswith('http'):
#                 urls.append(line)
#         test_urls = random.sample(urls, 3)

#         self.download_thread = TestSpeedThread(test_urls)
#         self.download_thread.test_speed_done_signal.connect(self.test_done)
#         self.download_thread.start()


#         self.setLayout(layout)
    
#     def test_done(self, speed):
#         print(f'下载的平均速度是:{speed}')
        

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     ex = App11()
#     ex.show()
#     sys.exit(app.exec())

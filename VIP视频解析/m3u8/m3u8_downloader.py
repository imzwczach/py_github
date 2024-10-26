import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import os
from urllib.parse import urlparse
import subprocess
import shutil
from tenacity import retry, stop_after_attempt, wait_fixed, RetryError
import re

from PySide6.QtCore import QObject, Signal

from enum import Enum

class DownloadState(Enum):
    DoneAll = 1
    Lost = 2

class M3u8Downloader(QObject):
    # 定义一个信号
    info_signal = Signal(str)
    progress_signal = Signal(dict)
    avg_speed_signal = Signal(float)
    download_state_signal = Signal(tuple)
    got_video_duration_signal = Signal(float, str)
    finished = Signal()

    maxWorkers = 5

    def __init__(self, inputString, ban_ads=False, dir_path='D:\\', head_time='0:0', tail_time='999999:0'):
        super().__init__()

        # Split the content into lines
        lines = inputString.strip().splitlines()

        # Initialize an array to store the extracted data
        infos = []
        for line in lines:
            info = {}
            parts = line.split('$')

            if len(parts) == 1 :
                info['name'] = '未命名'
                info['url'] = parts[0]
            elif len(parts) >= 2:
                info['name'] = parts[0]
                info['url'] = parts[1]
            else:
                continue
            info['lines'] = None
            infos.append(info)
        
        self.m3u8_infos = infos
        self.baned_ads = ban_ads
        self.dir_path = dir_path
        self.head_time = re.sub(r"[-： _]", ":", head_time) or '0:0'
        self.tail_time = re.sub(r"[-： _]", ":", tail_time) or '999999:0'
        self.baned_head_tail = not (head_time=='0:0'and tail_time=='999999:0')

        self.executor = ThreadPoolExecutor(max_workers=self.maxWorkers)
        self.futures = []  # 用于存储任务的引用
        self._is_cancelled = False  # 用于控制任务是否被取消
        self._is_paused = False  # 控制是否暂停

    def cancel(self):
        self._is_cancelled = True
        self._is_paused = False
        self.executor.shutdown(wait=False)  # 非阻塞地关闭线程池

    def pause(self):
        self._is_paused = True
        self.info_signal.emit("下载已暂停。")

    def resume(self):
        self._is_paused = False
        self.info_signal.emit("下载已恢复。")

    def _bake_correct_url(self, m3u8_url, part_url):
        if 'https:' in part_url or 'http:' in part_url:
            return part_url
        else:
            # 构建最后一个斜杠前的部分
            url_without_last_part = m3u8_url
            last_slash_index = m3u8_url.rfind('/')
            if last_slash_index!= -1:
                url_without_last_part = m3u8_url[:last_slash_index] + '/'

            str1 = url_without_last_part
            str2 = part_url# if part_url[0] == '/' else '/'+part_url
            common_part = ""
            for i in range(len(str1)):
                if str1[i:] == str2[:len(str1)-i]:
                    common_part = str1[i:]
                    break
            correct_url = str1[:len(str1)-len(common_part)] + str2
            return correct_url

    def get_ts_lines(self, url):
        # print(f'fetched url: {url}')
        # Fetch the m3u8 content from the provided URL
        try:
            # 发送HTTP GET请求获取文件内容
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 检查请求是否成功

            m3u8_content = response.text

            # Split the content by lines
            lines = m3u8_content.splitlines()

            # 遍历所有行
            for i in range(len(lines)):
                # 将url修改成带域名的链接
                good_lines = []
                # 遍历lines数组
                i = 0
                while i < len(lines):
                    # 如果元素是#EXTINF开头的，意味着我们找到了一组
                    if lines[i].startswith("#EXTINF"):
                        ts_url = lines[i + 1]  # ts 文件应该紧跟在 #EXTINF 之后
                        ts_url = self._bake_correct_url(url, ts_url)
                        good_lines.append(lines[i])
                        good_lines.append(ts_url)
                        # 跳过已处理的两行
                        i += 2
                    # 如果当前行以 "#EXT-X-STREAM-INF:" 开头
                    elif lines[i].startswith("#EXT-X-STREAM-INF:"):
                        # 检查下一行是否存在并提取出来
                        if i + 1 < len(lines):
                            stream_url = lines[i + 1]
                            stream_url = self._bake_correct_url(url, stream_url)
                            return self.get_ts_lines(stream_url)
                    else:
                        # 如果当前元素不是#EXTINF开头的，就直接加入结果中
                        good_lines.append(lines[i])
                        i += 1
                return good_lines

        except requests.Timeout:
            self.info_signal.emit("❌下载m3u8文件超时！")
            return []
        except requests.ConnectionError:
            self.info_signal.emit(f"❌下载m3u8文件连接错误！")
            return []
        except requests.HTTPError as e:
            self.info_signal.emit(f"❌下载m3u8文件时服务器返回错误：{e.response.status_code}")
            return []
        except requests.RequestException as e:
            print(url)
            self.info_signal.emit(f"❌下载m3u8文件时出现未知错误:{e}")
            return []

    def get_trim_head_tail_lines(self, lines, head, tail):
        if not self.baned_head_tail:
            return lines
        
        # 分割时间为分钟和秒
        minutes1, seconds1 = map(int, head.split(":"))
        minutes2, seconds2 = map(int, tail.split(":"))
        # 计算总秒数
        head_seconds = minutes1 * 60 + seconds1
        tail_seconds = minutes2 * 60 + seconds2

        # 用来保存处理后的lines
        result_lines = []
        # 处理组的计数
        total_duration = 0.0
        # 遍历lines时的指针
        i = 0
        # 遍历lines数组
        while i < len(lines):
            # 如果元素是#EXTINF开头的，意味着我们找到了一组
            if lines[i].startswith("#EXTINF"):
                # 提取#EXTINF后的数字
                ext_inf_line = lines[i]
                ts_file = lines[i + 1]  # ts 文件应该紧跟在 #EXTINF 之后

                # 提取时长并转换为浮点数
                duration = float(ext_inf_line.split(":")[1].strip(","))

                if head_seconds < total_duration + duration < tail_seconds:
                    result_lines.append(ext_inf_line)
                    result_lines.append(ts_file)

                # 更新总时长
                total_duration += duration

                # 跳过已处理的两行
                i += 2
            else:
                # 如果当前元素不是#EXTINF开头的，就直接加入结果中
                result_lines.append(lines[i])
                i += 1

        # 输出最终的结果
        return result_lines

    def get_ignore_ads_lines(self, lines):
        if not self.baned_ads:
            return lines
        # Initialize a variable to keep track if we are inside the block to remove
        inside_discontinuity_block = False
        result_lines = []
        for line in lines:
            if "#EXT-X-DISCONTINUITY" in line:
                inside_discontinuity_block = not inside_discontinuity_block  # Toggle block state
                continue  # Skip the line
            if "#EXT-X-KEY:METHOD=NONE" in line:
                continue  # Skip this line
            if not inside_discontinuity_block:
                result_lines.append(line)
        return result_lines

    def get_video_duration(self, url):
        lines = self.get_ts_lines(url)

        # 添加这行很不好，但是为了防止重复请求不改原来代码就加了
        for info in self.m3u8_infos:
            if url == info['url']:
                info['lines'] = lines
                break

        if lines is None or len(lines) == 0:
            return

        total_duration = 0.0
        # 遍历lines时的指针
        i = 0
        # 遍历lines数组
        while i < len(lines):
            # 如果元素是#EXTINF开头的，意味着我们找到了一组
            if lines[i].startswith("#EXTINF"):
                # 提取#EXTINF后的数字
                ext_inf_line = lines[i]
                ts_file = lines[i + 1]  # ts 文件应该紧跟在 #EXTINF 之后
                # 提取时长并转换为浮点数
                duration = float(ext_inf_line.split(":")[1].strip(","))
                # 更新总时长
                total_duration += duration
                # 跳过已处理的两行
                i += 2
            else:
                # 如果当前元素不是#EXTINF开头的，跳过
                i += 1

        self.got_video_duration_signal.emit(total_duration, url)

    # 定义一个函数，负责下载URL并保存文件
    @retry(stop=stop_after_attempt(8), wait=wait_fixed(2))  # 尝试8次，每次间隔2秒
    def download_file(self, url, index, download_dir):
        # 文件名为索引号
        file_name = os.path.join(download_dir, str(index) + '.ts')
        dir = os.path.basename(download_dir)

        if os.path.exists(file_name):
            self.info_signal.emit(f'😀️{index}.ts 已存在')
            return 1 #1字节，表示已下载

        try:
            # 发送HTTP GET请求获取文件内容
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}
            response = requests.get(url, timeout=5, headers=headers)
            response.raise_for_status()  # 检查请求是否成功
            # 将文件内容保存到本地
            with open(file_name, "wb") as file:
                file.write(response.content)
                self.info_signal.emit(f"😀下载 {dir}/{index}.ts 成功！")
            return len(response.content)

        except requests.Timeout:
            self.info_signal.emit(f"⚠下载 {dir}/{index}.ts 时超时，2秒后重试！")
            raise  # 抛出异常以触发重试

        except requests.ConnectionError:
            self.info_signal.emit(f"⚠下载 {dir}/{index}.ts 时连接错误，2秒后重试！")
            raise  # 抛出异常以触发重试

        except requests.HTTPError as e:
            self.info_signal.emit(f"❌下载 {dir}/{index}.ts 时服务器返回错误：{e.response.status_code}，不再重试。")
            return False  # 不重试

        except requests.RequestException:
            self.info_signal.emit(f"⚠下载 {dir}/{index}.ts 时出现未知错误，2秒后重试！")
            raise  # 抛出异常以触发重试

    def handle_download(self, url, index, download_dir):
        if self._is_cancelled:
            return 0
        else:
            while self._is_paused:  # 如果被暂停，则等待
                time.sleep(0.1)  # 确保不会占用 CPU 资源

            try:
                return self.download_file(url, index, download_dir)
            except RetryError:
                # print(f"❌下载 {index}.ts 重试次数已用完，下载失败！")  # 当重试次数用完时打印
                self.info_signal.emit(f"❌下载 {index}.ts 重试次数已用完，下载失败！")  # 当重试次数用完时打印
                return 0

    def download_ts_files(self):

        for urls, m3u8_info in self.ts_urls_generater():
            if len(urls) == 0:
                self.finished.emit()
                return

            m3u8_url = m3u8_info['url']
            download_dir = os.path.join(self.dir_path, m3u8_info["name"])

            total_count = len(urls)
            completed_count = 0
            self.futures = []

            downloaded_size = 0
            start_time = time.time()

            self.info_signal.emit(f'\n\n————准备下载《{m3u8_info["name"]}》视频切片')

            while self._is_paused:
                time.sleep(0.1)

            if self._is_cancelled:
                self.info_signal.emit("下载已被取消。")
                self.finished.emit()
                return

            # 为每个URL分配任务
            for index, url in enumerate(urls):
                future = self.executor.submit(self.handle_download, url, index, download_dir)
                self.futures.append(future)

            # 使用 as_completed 来跟踪任务完成情况
            for future in as_completed(self.futures):
                
                if self._is_cancelled:
                    self.info_signal.emit("下载已被取消。")
                    self.finished.emit()
                    return

                data_size = future.result()
                if data_size > 0:
                    completed_count += 1

                    # 计算进度百分比
                    progress = int((completed_count / total_count) * 100)
                    ext = {'value': progress, 'total': total_count, 'current': completed_count}
                    self.progress_signal.emit(ext)  # 发射进度信号

                    # 计算下载速度
                    downloaded_size += data_size
                    if completed_count%self.maxWorkers==0: # 每n个切片计算平均速度
                        end_time = time.time()
                        if end_time != start_time:
                            speed_in_mbps = (downloaded_size*8/(1024 * 1024)) / (end_time - start_time)  # MB每秒
                            self.avg_speed_signal.emit(speed_in_mbps)
                            # print(f'平均下载速度: {speed_in_mbps:.2f} Mb/S')
                            downloaded_size = 0
                            start_time = time.time()

            if not self._is_cancelled:
                if completed_count < total_count:
                    self.download_state_signal.emit((DownloadState.Lost, download_dir))
                else:
                    # 此处的代码在任务全部完成后才会继续执行
                    self.process_ffmpeg(download_dir)

        # 全部m3u8链接下载完后
        self.finished.emit()
        self.download_state_signal.emit((DownloadState.DoneAll, None))
        self.info_signal.emit('全部下载完成。')

    def ts_urls_generater(self):
        for m3u8_info in self.m3u8_infos:
            lines = m3u8_info['lines'] or self.get_ts_lines(m3u8_info['url'])
            if len(lines) > 0:
                trim_head_tail_lines = self.get_trim_head_tail_lines(lines, self.head_time, self.tail_time)
                ignore_ads_lines = self.get_ignore_ads_lines(trim_head_tail_lines)

                save_path = os.path.join(self.dir_path, m3u8_info["name"])
                os.makedirs(save_path, exist_ok=True)

                self.save_m3u8_file(ignore_ads_lines, save_path)
                self.download_m3u8_key(m3u8_info, ignore_ads_lines, save_path)
                ts_urls = self.get_ts_urls(ignore_ads_lines)

                yield ts_urls, m3u8_info  # 每次返回一个 m3u8_info 和对应的 urls
            else:
                yield [], {}

    def save_m3u8_file(self, lines, download_dir):
        result_lines = []
        # 遍历lines时的指针
        i = 0
        f = 0
        # 遍历lines数组
        while i < len(lines):
            # 如果元素是#EXTINF开头的，意味着我们找到了一组
            if lines[i].startswith("#EXTINF"):
                result_lines.append(lines[i])
                result_lines.append(f"{f}.ts")
                i = i + 2
                f = f + 1
            else:
                result_lines.append(lines[i])
                i = i + 1

        # Join the filtered lines
        filtered_m3u8_content = "\n".join(result_lines)
        # Save the result to a local file
        output_file_path = os.path.join(download_dir, 'ts.m3u8')
        with open(output_file_path, "w") as file:
            file.write(filtered_m3u8_content)

    def download_m3u8_key(self, m3u8_info, lines, download_dir):
        secret_key_name = None
        # 遍历lines时的指针
        i = 0
        # 遍历lines数组
        while i < len(lines):
            if lines[i].startswith('#EXT-X-KEY'):
                # 使用正则表达式提取 URI
                uri_pattern = r'URI="([^"]+)"'
                match = re.search(uri_pattern, lines[i])
                secret_key_name = match.group(1) if match else None
                break
            i = i + 1

        # 如果有加密文件则下载
        if secret_key_name:
            m3u8_url = m3u8_info['url']
            # 查找最后一个 '/' 的位置
            last_slash_index = m3u8_url.rfind('/')
            # 截取最后一个 '/' 之前的字符串
            part_url = m3u8_url[:last_slash_index + 1]
            secret_key_url = part_url + '/' + secret_key_name

            try:
                response = requests.get(secret_key_url)
                response.raise_for_status()  # 检查请求是否成功
                file_name = os.path.join(download_dir, secret_key_name)
                with open(file_name, "wb") as file:
                    file.write(response.content)

            except requests.RequestException:
                # print("下载密钥文件出错！！")
                self.info_signal.emit("下载密钥文件出错！！")

    def get_ts_urls(self, lines):
        ts_urls = []
        # 遍历lines时的指针
        i = 0
        # 遍历lines数组
        while i < len(lines):
            # 如果元素是#EXTINF开头的，意味着我们找到了一组
            if lines[i].startswith("#EXTINF"):
                url = lines[i + 1]  # ts 文件应该紧跟在 #EXTINF 之后
                ts_urls.append(url)
                i = i + 2
            else:
                i = i + 1
        return ts_urls

    def process_ffmpeg(self, download_dir):
        # 定义ffmpeg命令的参数
        m3u8_file = os.path.join(download_dir, 'ts.m3u8')  # 输入的m3u8文件
        parent_dir = os.path.dirname(download_dir)
        # 获取最后一个目录名称
        last_dir = os.path.basename(download_dir)
        output_file = os.path.join(parent_dir, f'{last_dir}.mp4')  # 输出的mp4文件

        # 合并前判断有同命名文件
        if os.path.exists(output_file):
            output_file = os.path.join(parent_dir, f'{last_dir}_1.mp4')

        # 构建ffmpeg命令
        command = [
            "ffmpeg",
            "-allowed_extensions", "ALL",
            "-protocol_whitelist", "file,http,crypto,tcp",
            "-i", m3u8_file,
            "-c", "copy",
            "-y", output_file
        ]

        # 执行命令
        try:
            # 使用subprocess运行命令，并捕获输出
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 检查任务是否完成
            if result.returncode == 0:
                # print(f"———————— {output_file} 文件已生成 ————————")
                self.info_signal.emit(f"———————— {output_file} 文件已生成")

                # 删除本地ts文件
                # 使用rmtree递归删除目录及其内容
                shutil.rmtree(download_dir)
                # print(f'清理本地目录 {download_dir} done.')
                self.info_signal.emit(f'清理本地目录 {download_dir} done.')
            else:
                # 手动解码输出（处理非ASCII字符）
                self.info_signal.emit("命令输出:", result.stdout.decode('utf-8', errors='ignore'))
                self.info_signal.emit("命令错误信息:", result.stderr.decode('utf-8', errors='ignore'))
        except subprocess.CalledProcessError as e:
            # 如果执行命令时发生错误，捕获并打印错误信息
            self.info_signal.emit("执行命令时发生错误:", e.stderr.decode('utf-8', errors='ignore'))
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import Signal, QObject
import requests
from commons.config import Config

class Album:
    def __init__(self, title, nums=None, id=None, source=None, img=None, url=None, flag=None) -> None:
        self.title = title
        self.nums = nums
        self.id = id
        self.source = source
        self.img = img
        self.url = url
        self.videos = None 
        self.flag = flag

    def __str__(self):
        # 返回可读性强的字符串
        # 通过 __dict__ 获取属性和值
        attributes = ', '.join([f"{key}={value!r}" for key, value in self.__dict__.items()])
        return f"{self.__class__.__name__}({attributes})"

class Engine(QObject):

    on_got_album_detail_signal = Signal(object)

    _instance = None  # 类变量，存储单例实例

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Engine, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, 'initialized'):  # 确保文件只读取一次
            self.initialized = True  # 标记为已初始化

    def get_reponse_data(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()  # 解析为 JSON 数据
            return data
        except Exception as e:
            raise Exception(f'请求{url},发生错误:{e}')

    def request_album_url(self, keyword):
        pass

    def request_album_detail_url(self, album):
        pass

    def get_albums(self, keyword):
        data = Config().request_data(self.request_album_url(keyword), 3600 * 6)
        return data

    def get_album_detail(self, album):
        data = Config().request_data(self.request_album_detail_url(album), 3600 * 6)
        return data


# https://v.wkvip.net/
class EngineWKVip(Engine):

    def request_album_url(self, keyword):
        return "https://a.wkvip.net/api.php?tp=jsonp&wd="+keyword

    def request_album_detail_url(self, album):
        return f"https://a.wkvip.net/api.php?out=json&flag={album.flag}&id={album.id}"

    def get_albums(self, keyword):
        data = super().get_albums(keyword)
        items = data.get('info', [])
        albums = [
            Album(title=item['title'],
                   id=item['id'], 
                   source=item['from'], 
                   flag=item['flag'], 
                   url=f"https://a.wkvip.net/api.php?out=json&flag={item['flag']}&id={item['id']}"
                ) for item in items]        
        return albums
        
    def get_album_detail(self, album):
        data = super().get_album_detail(album)
        album.img = data['pic']
        items = data.get('info', [])
        if len(items):
            album.nums = items[0]['part']
            videos = items[0]['video']
            arr = []
            for v in videos:
                parts = v.split('$')
                if len(parts) > 1:
                    arr.append({'title': parts[0], 'url': parts[1]})
            album.videos = arr
        return album

from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import Signal, QObject
import requests
from commons.config import Config
from lxml import etree

class Album:
    def __init__(self, title, id=None, source=None, img=None, url=None) -> None:
        self.title = title
        self.id = id
        self.source = source
        self.img = img
        self.url = url
        self.videos = None 
        self.date = None
        self.nums = None

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

    def get_reponse_josn(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()  # 解析为 JSON 数据
        except Exception as e:
            raise Exception(f'请求{url},发生错误:{e}')
        
    def get_reponse_text(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text.encode('utf-8')
        except Exception as e:
            raise Exception(f'请求{url},发生错误:{e}')

    def request_album_url(self, keyword):
        pass

    def get_albums(self, keyword):
        data = Config().request_data(self.request_album_url(keyword), 3600 * 12)
        return data

    def get_album_detail(self, album):
        data = Config().request_data(album.url, 3600 * 12)
        return data


# https://v.wkvip.net/
class EngineWKVip(Engine):

    def request_album_url(self, keyword):
        return "https://a.wkvip.net/api.php?tp=jsonp&wd="+keyword

    def get_albums(self, keyword):
        data = super().get_albums(keyword)
        items = data.get('info', [])
        albums = [
            Album(title=item['title'],
                   id=item['id'], 
                   source=item['from'],
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

# https://moduzy1.com/list1/
class EngineMoDu(Engine):

    def request_album_url(self, keyword=None):
        return "https://moduzy1.com/list1/"

    def get_albums(self, keyword):
        data = self.get_reponse_text(self.request_album_url())
        # 将字符串转换为 HTML 树结构
        html_tree = etree.HTML(data)

        # 使用 xpath 提取元素
        titles = html_tree.xpath('//tbody/tr//a/text()')
        sources = html_tree.xpath('//tbody/tr//small/text()')
        hrefs =  html_tree.xpath('//tbody/tr//a/@href')
        dates = html_tree.xpath('//tbody/tr/td[3]/text()')
        albums = []
        for i in range(len(titles)):
            album = Album(title=titles[i], source=sources[i], url='https://moduzy1.com' + hrefs[i])
            album.date = dates[i]
            albums.append(album)
        return albums
        
    def get_album_detail(self, album):
        data = self.get_reponse_text(album.url)

        # 将字符串转换为 HTML 树结构
        html_tree = etree.HTML(data)

        elms = html_tree.xpath("//ul/li/a[@class='copy_text']/text()")
        videos = []
        for elm in elms:
            parts = elm.split('$')
            if len(parts)>1:
                videos.append({'title': parts[0], 'url': parts[1]})
        album.videos = videos

        srcs = html_tree.xpath("//p[@class='thumb']/img/@src")
        if len(srcs):
            album.img = srcs[0]

        return album


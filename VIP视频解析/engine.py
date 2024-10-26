from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from PySide6.QtCore import Signal, QObject
import requests
from commons.config import Config
from lxml import etree
import parsel

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}

class Album:
    def __init__(self, title, source=None, img=None, url=None) -> None:
        self.title = title
        self.id = id
        self.source = source
        self.img = img
        self.url = url
        self.videos = None 
        self.date = None
        self.nums = None
        self.update = None
        self.desc = None
        self.score = None
        self.speed = None

    def __str__(self):
        # 返回可读性强的字符串
        # 通过 __dict__ 获取属性和值
        attributes = ', '.join([f"{key}={value!r}" for key, value in self.__dict__.items()])
        return f"{self.__class__.__name__}({attributes})"

class Engine(QObject):

    on_got_album_detail_signal = Signal(object)

    def __init__(self, config) -> None:
        self.isShow = config['show'] if 'show' in config else False
        self.support_search = config['search'] if 'search' in config else False
        self.has_thumb = config['thumb'] if 'thumb' in config else False
        self.grid = config['grid'] if 'grid' in config else False
        self.ban_ads = config['ban_ads'] if 'ban_ads' in config else False

    def get_reponse_josn(self, url):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()  # 解析为 JSON 数据
        except Exception as e:
            raise Exception(f'请求{url},发生错误:{e}')
        
    def get_reponse_text(self, url):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            raise Exception(f'请求{url},发生错误:{e}')

    def request_album_url(self, keyword=None):
        pass

    def get_albums(self, page=None):
        data = Config().request_data(self.request_album_url(page), expire=3600 * 12)
        return data

    def search_albums(self, keyword=None):
        data = Config().request_data(self.request_album_url(keyword), expire=3600 * 12)
        return data

    def get_album_detail(self, album):
        data = Config().request_data(album.url, expire=3600 * 12)
        return data

# https://v.wkvip.net/
class EngineWKVip(Engine):

    def request_album_url(self, keyword=None):
        return "https://a.wkvip.net/api.php?tp=jsonp&wd="+keyword

    def search_albums(self, keyword):
        data = super().search_albums(keyword)
        items = data.get('info', [])
        albums = [
            Album(title=item['title'],
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

import execjs
class EngineVideoLove(Engine):
    
    def search_albums(self, keyword):
        albums = []
        for i in range(1): #最多取5页
            pidx = i+1
            page_albums = self._get_albums_by_page(keyword=keyword, page=pidx)
            if len(page_albums) == 0:
                break
            albums.extend(page_albums)
        return sorted(albums, key=lambda obj: obj.nums, reverse=True)

    def _get_albums_by_page(self, keyword, page):
        try:
            # 尝试调用在js文件中定义的函数
            res = Config().ctx.call('getargs')

            parts = res.split('|')
            tt = parts[0]
            kk = parts[1]
            token = parts[2]
            
            data_list =  Config().request_data(f"https://video.isyour.love/player/getSource?name={keyword}&pg={page}", 
                                                type="json", 
                                                headers={'token': token, 't': tt, 'k': kk},
                                                expire=3600*6)
            albums = []
            for item in data_list:
                album = Album(title=item['Name'], img=item['Img'])
                album.date = item['lastUpDate']
                album.desc = item['Describe']
                album.source = item['TypeId']
                album.videos = [{'title': itm['N'], 'url':itm['S']} for itm in item['Data']]
                album.nums = len(album.videos)
                albums.append(album)
            return albums
        except execjs._exceptions.ProgramError as e:
            raise Exception(f"执行函数出错:{e}")

    def get_album_detail(self, album):
        return album        


# https://moduzy1.com/list1/
class EngineMoDu(Engine):

    def request_album_url(self, page):
        return f"https://moduzy1.com/list1-{page}/"

    def get_albums(self, page=1):
        data = self.get_reponse_text(self.request_album_url(page)).encode('utf-8')
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

class EngineBanguMi(Engine):

    def request_album_url(self, page=1):
        return f"https://bangumi.tv/anime/browser/?sort=rank&page={page}"
    
    def get_albums(self, page=None):
        data = Config().request_data(self.request_album_url(page), type='text', expire=3600*24*7)
        # 使用 xpath 提取元素
        selector = parsel.Selector(data)
        links = selector.xpath("//ul[@id='browserItemList']/li")
        albums = []
        for el in links:
            title = el.xpath(".//div/h3/a/text()").extract_first()
            img = 'https:' + el.xpath(".//a/span[@class='image']/img/@src").extract_first()
            score = el.xpath(".//div/p[@class='rateInfo']/small/text()").extract_first()
            album = Album(title=title, img=img)
            album.score = score
            albums.append(album)
        return albums


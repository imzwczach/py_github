from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import Signal, QObject
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

    # def get_reponse_data(self, url):
    #     try:
    #         response = requests.get(url)
    #         response.raise_for_status()
    #         data = response.json()  # 解析为 JSON 数据
    #         return data
    #     except Exception as e:
    #         raise Exception(f'请求{url},发生错误:{e}')

    def get_albums(self, keyword):
        pass

    def get_albums_details(self, albums):
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 为每个URL分配任务
            futures = [executor.submit(self.__get_album_detail, album) for album in albums]
            
        for future in as_completed(futures):
            result = future.result()
            if result:  # 如果下载成功，发送信号
                album = self.schedule_album_detail(result[0], result[1])
                self.on_got_album_detail_signal.emit(album)

    def schedule_album_detail(self, album: Album, data: dict):
        pass

    def __get_album_detail(self, album):
        data = Config().request_data(album.url, 60*60)
        return album, data

# https://v.wkvip.net/
class EngineWKVip(Engine):

    def get_albums(self, keyword):
        url = "https://a.wkvip.net/api.php?tp=jsonp&wd="+keyword
        data = Config().request_data(url, 60*60)
        items = data.get('info', [])
        albums = [
            Album(title=item['title'],
                   id=item['id'], 
                   source=item['from'], 
                   flag=item['flag'], 
                   url=f"https://a.wkvip.net/api.php?out=json&flag={item['flag']}&id={item['id']}"
                ) for item in items]        
        return albums
        
    def schedule_album_detail(self, album: Album, data: dict):
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

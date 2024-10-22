import json
import diskcache as dc
import requests

class Config:
    _instance = None  # 类变量，存储单例实例

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:

        if not hasattr(self, 'initialized'):  # 确保文件只读取一次
            self.initialized = True  # 标记为已初始化

            try:
                with open('config.json', 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.etfs = data['etfs']
            except FileNotFoundError:
                print("配置文件未找到。")
                self.etfs = []
            except json.JSONDecodeError:
                print("配置文件格式错误。")
                self.etfs = []

            # 创建一个缓存对象
            self.cache = dc.Cache('shared_cache')  # 是缓存存放的目录

    def get_reponse_data(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()  # 解析为 JSON 数据
            return data
        except Exception as e:
            raise Exception(f'请求{url},发生错误:{e}')

    def request_data(self, url, expire=60):

        # 首先检查缓存中是否存在该 symbol 的数据
        if url in self.cache:
            # print("Fetching from cache.. " + symbol)
            return self.cache[url]
        
        print(f'request {url}')

        # from datetime import datetime, timedelta

        # # 获取今日日期
        # end_date = datetime.today().strftime('%Y%m%d')
        # # 获取35天前的日期
        # start_date = (datetime.today() - timedelta(days=50)).strftime('%Y%m%d')

        data = self.get_reponse_data(url)
        self.cache.set(url, data, expire=expire)
        return data

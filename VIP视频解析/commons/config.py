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

            # 创建一个缓存对象
            self.cache = dc.Cache('shared_cache')  # 是缓存存放的目录

            self.search_history = self.cache['search_history'] if 'search_history' in self.cache else []

            import platform
            current_system = platform.system()
            self.isPC = (current_system == "Windows" or current_system == "Linux" or current_system == "Darwin")

            try:
                with open('configs.json', 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.engines = data['engines']
            except FileNotFoundError:
                print("配置文件未找到。")
                self.engines = []
            except json.JSONDecodeError:
                print("配置文件格式错误。")
                self.engines = []

            self.loadScripts()

    def save_search_history(self, history):
        self.cache.set('search_history', history, expire=3600*24*30*6)  # 设为None，永不过期

    def request_data(self, url, type='json', headers=None, key=None, expire=60):

        # 首先检查缓存中是否存在该 symbol 的数据
        key = key or url
        if key in self.cache:
            # print("Fetching from cache.. " + key)
            return self.cache[key]
        
        # print(f'request {url}')

        # from datetime import datetime, timedelta

        # # 获取今日日期
        # end_date = datetime.today().strftime('%Y%m%d')
        # # 获取35天前的日期
        # start_date = (datetime.today() - timedelta(days=50)).strftime('%Y%m%d')

        data = None
        try:
            headers_ = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0'}
            if headers:
                headers_.update(headers)
            response = requests.get(url, headers=headers_)
            response.raise_for_status()
            response.encoding = 'utf-8'
            if type=='json':
                data = response.json()
            elif type == 'content':
                data = response.content
            elif type == 'text':
                data = response.text

            self.cache.set(key, data, expire=expire)
            return data
        
        except Exception as e:
            raise Exception(f'请求{url},发生错误:{e}')
    

    def loadScripts(self):
        import execjs
        with open('engine_video_isyour_love.js', 'r', encoding='utf-8') as file:
            js_content = file.read()
            # 使用execjs编译包含函数的JavaScript代码
            self.ctx = execjs.compile(js_content)

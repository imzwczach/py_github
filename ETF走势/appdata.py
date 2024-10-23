import json
import diskcache as dc
import akshare as ak

class AppData:
    _instance = None  # 类变量，存储单例实例

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppData, cls).__new__(cls)
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

    def get_etf_data(self, symbol, expire=600):

        # 首先检查缓存中是否存在该 symbol 的数据
        if symbol in self.cache:
            # print("Fetching from cache.. " + symbol)
            return self.cache[symbol]
        
        print(f'request {symbol}')

        from datetime import datetime, timedelta

        # 获取今日日期
        end_date = datetime.today().strftime('%Y%m%d')
        # 获取35天前的日期
        start_date = (datetime.today() - timedelta(days=50)).strftime('%Y%m%d')

        etf_data = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
        self.cache.set(symbol, etf_data, expire=expire)

        return etf_data

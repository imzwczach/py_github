import json
import random

import diskcache as dc
# import akshare as ak
import efinance as ef
import requests


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

    def get_reponse_json(self, url, cookies=None):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
        }
        try:
            response = requests.get(url, headers=headers, cookies=cookies)
            response.raise_for_status()
            return response.json()  # 解析为 JSON 数据
        except Exception as e:
            raise Exception(f'请求{url},发生错误:{e}')

    def get_etf_data(self, symbol, expire=3600):

        # 首先检查缓存中是否存在该 symbol 的数据
        if symbol in self.cache:
            print("Fetching from cache.. " + symbol)
            return self.cache[symbol]
        
        print(f'request {symbol}')

        from datetime import datetime, timedelta

        # 获取今日日期
        end_date = datetime.today().strftime('%Y%m%d')
        # 获取35天前的日期
        start_date = (datetime.today() - timedelta(days=40)).strftime('%Y%m%d')

        # etf_data = ak.fund_etf_hist_em(symbol=symbol, period="daily", start_date=start_date, end_date=end_date)
        etf_data = ef.stock.get_quote_history(symbol, beg=start_date, end=end_date)
        self.cache.set(symbol, etf_data, expire=expire * random.randint(1, 6))

        return etf_data

    def _get_xiuqiu_cookie(self):
        if 'xueqiu_cookie' in self.cache:
            return self.cache['xueqiu_cookie']

        url = "https://www.xueqiu.com"
        response = requests.get(url)
        cookies_dict = response.cookies.get_dict()
        self.cache.set('xueqiu_cookie', cookies_dict, expire=3600*24)
        return cookies_dict

    def get_etfs_realtime_data(self, etfs):
        codes = [obj.code for obj in etfs]
        search_str = ",".join(map(str, codes))
        result = self.get_reponse_json("https://stock.xueqiu.com/v5/stock/realtime/quotec.json?symbol="+search_str)
        items = result['data']
        for idx, item in enumerate(items):
            model = etfs[idx]
            model.day_growth = item['percent']



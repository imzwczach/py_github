import re
from appdata import AppData
# import numpy as np

class ETFModel:
    def __init__(self, **kwargs):
        # self.__dict__.update(kwargs)
        self.name = kwargs.get('name', None)
        self.code = kwargs.get('code', None).upper()
                
        flag = '1' if self.code.lower().startswith('sh') else '0'
        self.nid = f"{flag}.{self.code[2:]}"

        symbol = re.findall(r'\d+', self.code)[0]
        etf_data = AppData().get_etf_data(symbol)
        if etf_data.empty:
            print(f"{self.code} No data available for the given date range.")
        else:
            lastest = etf_data.iloc[-1]
            # self.day_growth = lastest['涨跌幅']
            self.date = lastest['日期']

            self.etf_data = calculate_bollinger_bands(etf_data)
            self.k_slope = k_boll_mid(etf_data)
            self.distance_mid = distance_mid(etf_data)

def calculate_bollinger_bands(etf_data, window=20, num_std=2):
    """计算 Bollinger Bands"""
    etf_data['BOLL_MID'] = etf_data['收盘'].rolling(window).mean()
    etf_data['BOLL_STD'] = etf_data['收盘'].rolling(window).std()
    etf_data['BOLL_UP'] = etf_data['BOLL_MID'] + (etf_data['BOLL_STD'] * num_std)
    etf_data['BOLL_DOWN'] = etf_data['BOLL_MID'] - (etf_data['BOLL_STD'] * num_std)

    # 过滤掉VWAP为NaN的行，并且确保收盘价和VWAP数据长度一致
    etf_data = etf_data.dropna(subset=['BOLL_MID'])
    
    return etf_data

def is_bollinger_bands_expanding(etf_data):
    # 检查中轨是否上升
    mid_ascending = etf_data['BOLL_MID'].iloc[-1] > etf_data['BOLL_MID'].iloc[-2]

    # 检查上轨和下轨的距离是否增大
    upper_lower_distance_increasing = (etf_data['BOLL_UP'].iloc[-1] - etf_data['BOLL_DOWN'].iloc[-1] > 
                                       etf_data['BOLL_UP'].iloc[-2] - etf_data['BOLL_DOWN'].iloc[-2])

    return mid_ascending and upper_lower_distance_increasing

def k_boll_mid(etf_data):
    # 获取最后一个点和倒数第二个点的 BOLL 中轨值
    last_mid = etf_data['BOLL_MID'].iloc[-1]
    prev_mid = etf_data['BOLL_MID'].iloc[-3]

    # 计算最后一个点的斜率
    slope = (last_mid - prev_mid)/prev_mid * 100
    return slope

def distance_mid(etf_data):
    last_mid = etf_data['BOLL_MID'].iloc[-1]
    close = etf_data['收盘'].iloc[-1]
    distance = (close - last_mid)/last_mid * 100
    return distance
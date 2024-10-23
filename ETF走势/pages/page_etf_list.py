
from commons.page import *
from models import ETFModel
from appdata import AppData
from pages.page_etf_detail import ETFDetailPage

class CustomWidget(QWidget):
    def __init__(self, model:ETFModel):
        super().__init__()

        hbox = QHBoxLayout()

        # 创建文本标签，显示 item 中的某个字段
        self.etf_model = model
        color_growth = 'red' if float(model.day_growth) > 0 else 'green'
        color_k = 'red' if model.k_slope > 0 else 'green'

        text = f"<span style='color:{color_growth};font-size:12px;'><b>{model.day_growth}%</b></span>\
            &ensp;<b>{model.name}</b>\
            &emsp;<span style='color:{color_k};font-size:10px;'>k: {model.k_slope:.1f}%</span>\
            <br><span style='font-size:10px;'>{model.date}</span>\
            &emsp;<span style='font-size:10px;'>距中轨: {model.distance_mid:.1f}%</span>\
            "
        text_label = QLabel(text) 
        hbox.addWidget(text_label)

        self.setLayout(hbox)
    
    def title(self):
        return self.etf_model.name

class ETFListPage(ListPage):
    def __init__(self):
        super().__init__()
        self.title = 'ETF列表'
        self.setStyleSheet("background:#dddddd;padding:5px;")
        self.itemHeight = 80
        self.set_delegate(self)
        self.etf_models = None

    def list_page_items(self, list_widget):
        etfs = AppData().etfs
        self.etf_models = []
        for etf in etfs:
            etf_model = ETFModel(**etf)
            if etf_model.distance_mid > 0:
                self.etf_models.append(etf_model)

        self.etf_models = sorted(self.etf_models, key=lambda obj: -obj.k_slope)

        AppData().get_etfs_realtime_data(self.etf_models)

        return [CustomWidget(m) for m in self.etf_models]

    def list_page_item_selected(self, item, index):
        detail_page = ETFDetailPage(self.etf_models[index])
        self.push(detail_page)
        pass

    def showEvent(self, event):
        self.reload_data()

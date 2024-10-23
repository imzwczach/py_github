from commons.image_label import ImageLabel
from commons.page import *
from models import *

class ETFDetailPage(Page):
    def __init__(self, etf_model: ETFModel, parent=None):
        super().__init__(None, parent)
 
        self.title = etf_model.name
        self.etf_model = etf_model

        self.img_label = ImageLabel()
        self.img_label.clicked.connect(self.on_clicked_img_label) 
        self.layout.addWidget(self.img_label)

        self.__flag = 0
        self.on_clicked_img_label()

    def on_clicked_img_label(self):

        if self.__flag == 0:
            self.img_label.load_image_from_url(f"https://webquoteklinepic.eastmoney.com/GetPic.aspx?nid={self.etf_model.nid}&type=&unitWidth=-6&ef=EXTENDED_BOLL&formula=MACD&AT=1&imageType=KXL")
            self.__flag = 1
        elif self.__flag == 1:
            self.img_label.load_image_from_url(f"https://webquotepic.eastmoney.com/GetPic.aspx?imageType=r&type=&nid={self.etf_model.nid}")
            self.__flag = 2
        else:
            self.img_label.load_image_from_url(f"https://webquoteklinepic.eastmoney.com/GetPic.aspx?nid={self.etf_model.nid}&type=W&unitWidth=-6&ef=EXTENDED_BOLL&formula=MACD&AT=1&imageType=KXL")
            self.__flag = 0


from .base_loader import BaseLoader
import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime

class SPRevListLoader(BaseLoader):
    """
    上場銘柄一覧（Master Data）を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Updating sp_rev_list...")
        try:
            url = 'https://www.secjp.co.jp/products/stock/brand/merger/'
            html = urlopen(url)
            soup = BeautifulSoup(html,'html.parser')
        except Exception as e:
            self.logger.error(f"Error occurred while scraping: {e}")
            return

        list_date = []
        list_scode = []
        list_sname = []
        list_ratio = []
        list_index = []
        list_type = []

        for row in soup.findAll("table")[0].findAll("tr")[3:]:
            col = row.findAll("td")
            if col[8].text == '分割':
                list_date.append(datetime.strptime(col[1].string,"%Y/%m/%d"))
                list_scode.append(col[2].string)
                list_sname.append(col[3].string)
                ratio = col[9].string.replace('：',':')
                list_ratio.append(float(ratio[ratio.find(u':')+1:]))
                list_index.append(col[2].string+"-"+col[1].string)
                list_type.append(u'株式分割')
            if col[8].text == '併合':
                list_date.append(datetime.strptime(col[1].string,"%Y/%m/%d"))
                list_scode.append(col[2].string)
                list_sname.append(col[3].string)
                ratio = col[9].string.replace('：',':')
                ratio_bf = ratio[:ratio.find(":")]
                ratio_af = ratio[ratio.find(":")+1:]
                list_ratio.append(float(ratio_af)/float(ratio_bf))
                list_index.append(col[2].string+"-"+col[1].string)
                list_type.append(u'株式併合')
        self.logger.info("Num of scodes in List = %d", len(list_scode))
        df = pd.DataFrame({'date':list_date,'scode':list_scode,'sname':list_sname,'ratio':list_ratio,'type':list_type},index=list_index)
        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for r in df.index:
            record = {
                "ID": r,
                "exe_date": df.loc[r]['date'],
                "scode": df.loc[r]['scode'],
                "sname": df.loc[r]['sname'],
                "ratio": df.loc[r]['ratio'],
                "type": df.loc[r]['type'],
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("sp_rev_list", records)

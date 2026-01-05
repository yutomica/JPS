from datetime import datetime, date
from .base_loader import BaseLoader

class ListedInfoLoader(BaseLoader):
    """
    上場銘柄一覧（Master Data）を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Fetching listed info (v2)...")
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        response = self.api_client.get("/equities/master", params={"date": date_str})
        if len(response) == 0:
            self.logger.warning("No listed info data received.")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            record = {
                "Code": item.get("Code"),
                "Date": item.get("Date"),
                "CompanyName": item.get("CoName"),
                "CompanyNameEnglish": item.get("CoNameEn"),
                "Sector17Code": item.get("S17"),
                "Sector17CodeName": item.get("S17Nm"),
                "Sector33Code": item.get("S33"),
                "Sector33CodeName": item.get("S33Nm"),
                "ScaleCategory": item.get("ScaleCat"),
                "MarketCode": item.get("Mkt"),
                "MarketCodeName": item.get("MktNm"),
                "MarginCode": item.get("Mrgn"),
                "MarginCodeName": item.get("MrgnNm"),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("listed_info", records)
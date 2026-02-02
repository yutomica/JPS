from datetime import datetime, date
from .base_loader import BaseLoader

class ShortRatioLoader(BaseLoader):
    """
    業種別空売り比率（Short Ratio）を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Fetching short ratio data...")
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        response = self.api_client.get("/markets/short-ratio", params={"date": date_str})
        if len(response) == 0:
            self.logger.warning("No short ratio data received.")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            record = {
                "Date": item.get("Date"),
                "S33": item.get("S33"),
                "SellExShortVa": item.get("SellExShortVa"),
                "ShrtWithResVa": item.get("ShrtWithResVa"),
                "ShrtNoResVa": item.get("ShrtNoResVa"),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("short_ratio", records)
from datetime import datetime, date
from .base_loader import BaseLoader

class IndicesOHLCLoader(BaseLoader):
    """
    指数四本値（Indices OHLC）を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Fetching indices OHLC data...")
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        response = self.api_client.get("/indices/bars/daily", params={"date": date_str})
        if len(response) == 0:
            self.logger.warning("No indices OHLC data received.")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            record = {
                "Date": item.get("Date"),
                "Code": item.get("Code"),
                "Open": item.get("O"),
                "High": item.get("H"),
                "Low": item.get("L"),
                "Close": item.get("C"),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("indices_ohlc", records)
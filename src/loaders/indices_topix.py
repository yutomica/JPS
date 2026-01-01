
from datetime import datetime, date
from .base_loader import BaseLoader

class IndicesTopixLoader(BaseLoader):
    """
    TOPIX指数データを取得・更新するローダー
    """
    def run(self, target_date=None):
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        self.logger.info("Fetching TOPIX index data...")
        response = self.api_client.get("/indices/bars/daily/topix", params={"from": date_str, "to": date_str})
        if len(response) == 0:
            self.logger.warning("No TOPIX index data received.")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            record = {
                "Date": item.get("Date"),
                "Open": item.get("O"),
                "High": item.get("H"),
                "Low": item.get("L"),
                "Close": item.get("C"),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("indices_topix", records)
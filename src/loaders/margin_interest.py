from datetime import datetime, date
from .base_loader import BaseLoader

class MarginInterestLoader(BaseLoader):
    """
    信信用週取引残高（Margin Interest）を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Fetching margin interest data...")
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        response = self.api_client.get("/markets/margin-interest", params={"date": date_str})
        if len(response) == 0:
            self.logger.warning("No margin interest data received.")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            record = {
                "Date": item.get("Date"),
                "Code": item.get("Code"),
                "ShrtVol": item.get("ShrtVol"),
                "LongVol": item.get("LongVol"),
                "ShrtNegVol": item.get("ShrtNegVol"),
                "LongNegVol": item.get("LongNegVol"),
                "ShrtStdVol": item.get("ShrtStdVol"),
                "LongStdVol": item.get("LongStdVol"),
                "IssType": item.get("IssType"),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("margin_interest", records)
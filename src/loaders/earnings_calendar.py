
from .base_loader import BaseLoader

class EarningsCalendarLoader(BaseLoader):
    """
    決算発表予定日を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Fetching earnings calendar (v2)...")
        response = self.api_client.get("/equities/earnings-calendar", params={"date": target_date})
        if len(response) == 0:
            self.logger.warning("No earnings calendar data received.")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            record = {
                "Code": item.get("Code"),
                "Date": item.get("Date"),
                "CompanyName": item.get("CoName"),
                "FiscalYear": item.get("FY"),
                "SectorName": item.get("SectorNm"),
                "FQ": item.get("FQ"),
                "Section": item.get("Section"),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("earnings_calendar", records)
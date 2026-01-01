from datetime import datetime, date
from .base_loader import BaseLoader

class PricesLoader(BaseLoader):
    """
    日足株価（Daily Quotes）を取得・更新するローダー
    """
    def run(self, target_date=None):
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        self.logger.info(f"Fetching daily prices (v2) for date: {date_str}")
        response = self.api_client.get("/equities/bars/daily", params={"date": date_str})
        if len(response) == 0:
            self.logger.warning(f"No price data found for {date_str}. (Market holiday?)")
            return

        # DB用データリストの作成
        records = []
        for q in response['data']:
            # APIの戻り値は全て文字列の場合があるため、適切な型変換を行うと安全ですが、
            # SQLAlchemyがある程度吸収してくれます。ここでは明示的にキーを選択します。
            record = {
                "Date": datetime.strptime(q.get("Date"), "%Y-%m-%d").date(), # DB側がDate型の場合
                "Code": q.get("Code"),
                "Open": q.get("O"),
                "High": q.get("H"),
                "Low": q.get("L"),
                "Close": q.get("C"),
                "UpperLimit": q.get("UL"),
                "LowerLimit": q.get("LL"),
                "Volume": q.get("Vo"),
                "Turnover": q.get("Va"),
                "AdjustmentFactor": q.get("AdjFactor"),
                "AdjustmentOpen": q.get("AdjO"),
                "AdjustmentHigh": q.get("AdjH"),
                "AdjustmentLow": q.get("AdjL"),
                "AdjustmentClose": q.get("AdjC"),
                "AdjustmentVolume": q.get("AdjVo"),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("daily_prices", records)
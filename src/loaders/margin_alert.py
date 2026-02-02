from datetime import datetime, date
from .base_loader import BaseLoader

class MarginAlertLoader(BaseLoader):
    """
    日々公表信用取引残高（Margin Alert）を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Fetching margin alert data...")
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        response = self.api_client.get("/markets/margin-alert", params={"date": date_str})
        if len(response) == 0:
            self.logger.warning("No margin alert data received.")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            pubreason = item.get("PubReason", {})
            pubreason_val = None
            for k, v in pubreason.items():
                if v=="1": pubreason_val = k
            record = {
                "PubDate": item.get("PubDate"),
                "Code": item.get("Code"),
                "AppDate": item.get("AppDate"),
                "PubReason": pubreason_val if pubreason_val else None,
                "ShrtOut": item.get("ShrtOut"),
                "ShrtOutChg": item.get("ShrtOutChg"),
                "ShrtOutRatio": item.get("ShrtOutRatio"),   
                "LongOut": item.get("LongOut"),
                "LongOutChg": item.get("LongOutChg"),
                "LongOutRatio": item.get("LongOutRatio"),
                "SLRatio": item.get("SLRatio"),
                "ShrtNegOut": item.get("ShrtNegOut"),
                "ShrtNegOutChg": item.get("ShrtNegOutChg"),
                "ShrtStdOut": item.get("ShrtStdOut"),
                "ShrtStdOutChg": item.get("ShrtStdOutChg"),
                "LongNegOut": item.get("LongNegOut"),
                "LongNegOutChg": item.get("LongNegOutChg"),
                "LongStdOut": item.get("LongStdOut"),
                "LongStdOutChg": item.get("LongStdOutChg"),
                "TSEMrgnRegCls": item.get("TSEMrgnRegCls"),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("margin_alert", records)
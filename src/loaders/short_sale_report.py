from datetime import datetime, date
from .base_loader import BaseLoader

class ShortSaleReportLoader(BaseLoader):
    """
    空売り残高報告（Short Sale Report）を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Fetching short sale report data...")
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        response = self.api_client.get("/markets/short-sale-report", params={"calc_date": date_str})
        if len(response) == 0:
            self.logger.warning("No short sale report data received.")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            record = {
                "DiscDate": item.get("DiscDate"),
                "CalcDate": item.get("CalcDate"),
                "Code": item.get("Code"),
                "SSName": item.get("SSName"),
                "SSAddr": item.get("SSAddr"),
                "DICName": item.get("DICName"),
                "DICAddr": item.get("DICAddr"),
                "FundName": item.get("FundName"),
                "ShrtPosToSO": item.get("ShrtPosToSO"),
                "ShrtPosShares": item.get("ShrtPosShares"),
                "ShrtPosUnits": item.get("ShrtPosUnits"),
                "PrevRptDate": item.get("PrevRptDate"),
                "PrevRptRatio": item.get("PrevRptRatio"),
                "Notes": item.get("Notes")
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("short_sale_report", records)
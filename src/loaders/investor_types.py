from datetime import datetime, date
from .base_loader import BaseLoader

class InvestorTypesLoader(BaseLoader):
    """
    投資部門別売買動向（Trading by Investor Type）を取得・更新するローダー
    API Endpoint: /markets/trades_spec
    """
    def run(self, target_date=None):
        # 日付文字列の取得 (YYYYMMDD形式)
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = str(date_to_fetch).replace("-", "")

        self.logger.info(f"Fetching investor trading types (v2) for date: {date_str}")

        # APIリクエスト
        params = {"from": date_str, "to": date_str}
        response = self.api_client.get("/equities/investor-types", params=params)
        if len(response) == 0:
            self.logger.warning(f"No data found for {date_str}.")
            return

        # DB用データリストの作成
        records = []
        for item in response['data']:
            # 空文字やNoneを変換するヘルパー
            def clean_val(val):
                if val == "" or val is None:
                    return None
                return float(val)
            record = {
                # --- 日付・区分 ---
                "PubDate": item.get("PubDate"), # 公表日
                "StDate": item.get("StDate"),   # 開始日
                "EnDate": item.get("EnDate"),   # 終了日
                "Section": item.get("Section"), # 市場区分
                # --- 自己計 (Proprietary) ---
                "PropSell": clean_val(item.get("PropSell")),
                "PropBuy": clean_val(item.get("PropBuy")),
                "PropTot": clean_val(item.get("PropTot")),
                "PropBal": clean_val(item.get("PropBal")),
                # --- 委託計 (Brokerage) ---
                "BrkSell": clean_val(item.get("BrkSell")),
                "BrkBuy": clean_val(item.get("BrkBuy")),
                "BrkTot": clean_val(item.get("BrkTot")),
                "BrkBal": clean_val(item.get("BrkBal")),
                # --- 総計 (Total) ---
                "TotSell": clean_val(item.get("TotSell")),
                "TotBuy": clean_val(item.get("TotBuy")),
                "TotTot": clean_val(item.get("TotTot")),
                "TotBal": clean_val(item.get("TotBal")),
                # --- 個人 (Individuals) ---
                "IndSell": clean_val(item.get("IndSell")),
                "IndBuy": clean_val(item.get("IndBuy")),
                "IndTot": clean_val(item.get("IndTot")),
                "IndBal": clean_val(item.get("IndBal")),
                # --- 海外投資家 (Foreigners) ---
                "FrgnSell": clean_val(item.get("FrgnSell")),
                "FrgnBuy": clean_val(item.get("FrgnBuy")),
                "FrgnTot": clean_val(item.get("FrgnTot")),
                "FrgnBal": clean_val(item.get("FrgnBal")),
                # --- 証券会社 (Securities Cos) ---
                "SecCoSell": clean_val(item.get("SecCoSell")),
                "SecCoBuy": clean_val(item.get("SecCoBuy")),
                "SecCoTot": clean_val(item.get("SecCoTot")),
                "SecCoBal": clean_val(item.get("SecCoBal")),
                # --- 投資信託 (Investment Trusts) ---
                "InvTrSell": clean_val(item.get("InvTrSell")),
                "InvTrBuy": clean_val(item.get("InvTrBuy")),
                "InvTrTot": clean_val(item.get("InvTrTot")),
                "InvTrBal": clean_val(item.get("InvTrBal")),
                # --- 事業法人 (Business Cos) ---
                "BusCoSell": clean_val(item.get("BusCoSell")),
                "BusCoBuy": clean_val(item.get("BusCoBuy")),
                "BusCoTot": clean_val(item.get("BusCoTot")),
                "BusCoBal": clean_val(item.get("BusCoBal")),
                # --- その他法人 (Other Cos) ---
                "OthCoSell": clean_val(item.get("OthCoSell")),
                "OthCoBuy": clean_val(item.get("OthCoBuy")),
                "OthCoTot": clean_val(item.get("OthCoTot")),
                "OthCoBal": clean_val(item.get("OthCoBal")),
                # --- 生保・損保 (Insurance Cos) ---
                "InsCoSell": clean_val(item.get("InsCoSell")),
                "InsCoBuy": clean_val(item.get("InsCoBuy")),
                "InsCoTot": clean_val(item.get("InsCoTot")),
                "InsCoBal": clean_val(item.get("InsCoBal")),
                # --- 銀行 (Banks / City & Regional) ---
                "BankSell": clean_val(item.get("BankSell")),
                "BankBuy": clean_val(item.get("BankBuy")),
                "BankTot": clean_val(item.get("BankTot")),
                "BankBal": clean_val(item.get("BankBal")),
                # --- 信託銀行 (Trust Banks) ---
                "TrstBnkSell": clean_val(item.get("TrstBnkSell")),
                "TrstBnkBuy": clean_val(item.get("TrstBnkBuy")),
                "TrstBnkTot": clean_val(item.get("TrstBnkTot")),
                "TrstBnkBal": clean_val(item.get("TrstBnkBal")),
                # --- その他金融機関 (Other Financials) ---
                "OthFinSell": clean_val(item.get("OthFinSell")),
                "OthFinBuy": clean_val(item.get("OthFinBuy")),
                "OthFinTot": clean_val(item.get("OthFinTot")),
                "OthFinBal": clean_val(item.get("OthFinBal")),
            }
            records.append(record)
        # DBへ保存 (テーブル名は investor_types とします)
        self.db_manager.upsert("investor_types", records)
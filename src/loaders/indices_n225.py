from datetime import datetime, date, timedelta
import yfinance as yf
import pandas as pd
from .base_loader import BaseLoader

def fetch_nikkei_225_daily(start_date, end_date):
    """
    Nikkei 225の日足データを取得する。
    Args:
        start_date (str): 開始日 (YYYY-MM-DD)
        end_date (str): 終了日 (YYYY-MM-DD)
    Returns:
        pd.DataFrame: 取得したデータ
    Raises:
        RuntimeError: データの取得に失敗した場合、またはデータが空の場合
    """
    ticker_symbol = "^N225"
    try:
        # yfinanceを使用してデータをダウンロード
        # interval="1d" で日足データを指定
        df = yf.download(ticker_symbol, start=start_date, end=end_date, interval="1d")
        return df
    except Exception as e:
        # 2. ネットワークエラー、レート制限(Rate Limit)、APIの仕様変更などによるエラー処理
        # 先ほど発生していた 'Too Many Requests' もここでキャッチされます
        raise RuntimeError(f"APIコール中にエラーが発生しました: {str(e)}")


class IndicesN225Loader(BaseLoader):
    """
    日経平均株価四本値（N225 OHLC）を取得・更新するローダー
    """
    def run(self, target_date=None):
        self.logger.info("Fetching N225 index data...")
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
            dt_obj = date_to_fetch
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
            dt_obj = datetime.strptime(date_str, "%Y%m%d")
        # yfinanceからダウンロード
        start = dt_obj.strftime("%Y-%m-%d")
        end = (dt_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            nikkei_data = fetch_nikkei_225_daily(start, end)
        except RuntimeError as error:
            # ここでスクリプト内のエラーメッセージをキャッチして表示します
            self.logger.warning(f"Cannot fetch Nikkei 225 data: {error}")
            return

        # データが空（祝日など）の場合はスキップ
        if nikkei_data.empty:
            self.logger.info(f"No Nikkei 225 data found for {start}. (Market holiday?)")
            return

        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for dt, row in nikkei_data.iterrows():
            record = {
                "Date": dt.strftime('%Y-%m-%d'),
                "Open": float(row['Open']),
                "High": float(row['High']),
                "Low": float(row['Low']),
                "Close": float(row['Close']),
                "Volume": float(row['Volume']),
            }
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("indices_n225", records)
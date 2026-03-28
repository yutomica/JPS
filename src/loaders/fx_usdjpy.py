import yfinance as yf
import pandas as pd

def get_aligned_usdjpy(start_date, end_date):
    """
    日本株市場の引け(15:00)時点のドル円レートを抽出する
    """
    # 1時間足(またはそれ以上の解像度)で取得
    data = yf.download("USDJPY=X", start=start_date, end=end_date, interval="1h")
    
    # タイムゾーンをJSTに変換 (UTCで取得されるため)
    data.index = data.index.tz_convert('Asia/Tokyo')
    
    # 各日の 15:00 に最も近いデータのみを抽出
    # (yfinanceの1h足は15:00開始の足などを利用)
    aligned_data = data.between_time('14:59', '15:01')[['Close']]
    
    # 日付のみのインデックスに変更して、株価データとマージ可能にする
    aligned_data.index = aligned_data.index.date
    aligned_data.columns = ['usdjpy_1500_mid']
    
    return aligned_data

# 推論時に「今」の値を安全に取る場合
def get_current_usdjpy_safe():
    # 取得に失敗するリスクを考え、最新の数件を取得して最後の一件を採用
    ticker = yf.Ticker("USDJPY=X")
    current_data = ticker.history(period="1d", interval="1m")
    if not current_data.empty:
        return current_data['Close'].iloc[-1]
    return None
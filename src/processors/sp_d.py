
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import text

class SPDProcessor:

    def __init__(self, db_manager_org, db_manager_jps):
        self.db_manager_org = db_manager_org
        self.db_manager_jps = db_manager_jps
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self, target_date=None):
        self.logger.info("Updating sp_d ...")
        sql = """
            SELECT t1.Code, 'T' as mcode, t1.CompanyName as sname, t1.MarketCodeName as market,
                t2.Open, t2.High, t2.Low, t2.Close, t2.Volume, t2.Turnover as Volume_p,t2.Date as date
            FROM org.listed_info t1 INNER JOIN org.daily_prices t2 ON t1.Code = t2.Code
            WHERE t1.Date = :target_date AND t2.Date = :target_date AND t2.Code like '%%0'
        """
        with self.db_manager_org.engine.connect() as conn:
            df = pd.read_sql(text(sql), con=conn, params={"target_date": target_date})
        df['scode'] = [x[:4] for x in df['Code']]

        # ---------------------------------------------------------
        # 取引なし銘柄（VolumeがNULL）の補完処理
        # ---------------------------------------------------------
        # 1. VolumeがNULL（NaN）になっている行を特定
        no_trade_mask = df['Volume'].isnull()
        # 取引なし銘柄が存在する場合のみ実行
        if no_trade_mask.any():
            self.logger.info(f"Found {no_trade_mask.sum()} records with NULL Volume. Filling with previous close prices.")
            # 2. 前営業日の終値を jps.sp_d から取得するためのSQL
            # date < target_date の条件で最も新しい日付（前営業日）のデータを取得します
            # ※全銘柄分取得しても軽量なため、IN句で絞り込まず日付で一括取得します
            prev_sql = """
                SELECT scode, Close as prev_close
                FROM jps.sp_d
                WHERE date = (
                    SELECT MAX(date) FROM jps.sp_d WHERE date < :target_date
                )
            """
            with self.db_manager_jps.engine.connect() as conn:
                prev_df = pd.read_sql(text(prev_sql), con=conn, params={"target_date": target_date})
            # 3. メインのdfに前日終値をマージ（scodeをキーにする）
            # how='left'で元のdfの行数を維持します
            df = df.merge(prev_df, on='scode', how='left')
            # 4. VolumeがNULLの行に対して、OHLCを前日終値(prev_close)で埋める
            target_cols = ['Open', 'High', 'Low', 'Close']
            for col in target_cols:
                # 対象カラムがNULLの場合、prev_closeの値で埋める
                df[col] = df[col].fillna(df['prev_close'])
            # 5. VolumeとTurnover(Volume_p)は0で埋める
            df['Volume'] = df['Volume'].fillna(0)
            df['Volume_p'] = df['Volume_p'].fillna(0)
            # 6. 不要になった一時カラム(prev_close)を削除
            df = df.drop(columns=['prev_close'])
            # df = df.dropna()
        df = df[['scode', 'mcode', 'sname', 'market', 'Open', 'High', 'Low', 'Close', 'Volume', 'Volume_p', 'date']]

        # ---------------------------------------------------------
        # TOPIX指数データの追加
        # ---------------------------------------------------------
        sql = """
            SELECT Date as date, Open, High, Low, Close
            FROM org.indices_topix
            WHERE date = :target_date
        """
        with self.db_manager_org.engine.connect() as conn:
            _df = pd.read_sql(text(sql), con=conn, params={"target_date": target_date})
        _df['scode'] = '0002'
        _df['sname'] = 'TOPIX（東証株価指数）'
        _df['mcode'] = 'T'
        _df['market'] = '東証'
        _df['Volume'] = 0
        _df['Volume_p'] = 0
        df = pd.concat([df, _df[['scode', 'mcode', 'sname', 'market', 'Open', 'High', 'Low', 'Close', 'Volume', 'Volume_p', 'date']]], ignore_index=True)

        # ---------------------------------------------------------
        # N225データの追加
        # ---------------------------------------------------------
        sql = """
            SELECT Date as date, Open, High, Low, Close, Volume
            FROM org.indices_n225
            WHERE date = :target_date
        """
        with self.db_manager_org.engine.connect() as conn:
            _df = pd.read_sql(text(sql), con=conn, params={"target_date": target_date})
        _df['scode'] = '0001'
        _df['sname'] = '日経平均株価（日経225）'
        _df['mcode'] = 'T'
        _df['market'] = '東証'
        _df['Volume'] = 0
        _df['Volume_p'] = 0
        df = pd.concat([df, _df[['scode', 'mcode', 'sname', 'market', 'Open', 'High', 'Low', 'Close', 'Volume', 'Volume_p', 'date']]], ignore_index=True)

        # DB用データリストの作成
        records = []
        for _, row in df.iterrows():
            # NaN (Not a Number) を None に変換するヘルパー関数
            def clean_float(val):
                if pd.isna(val): return None
                return float(val)
            record = {
                "scode": str(row['scode']),
                "mcode": str(row['mcode']),
                "sname": str(row['sname']),
                "market": str(row['market']),
                "Open": clean_float(row['Open']),
                "High": clean_float(row['High']),
                "Low": clean_float(row['Low']),
                "Close": clean_float(row['Close']),
                "Volume": int(row['Volume']),
                "Volume_p": int(row['Volume_p']),
                "date": row['date']
            }
            records.append(record)
        
        # DBへ保存
        self.db_manager_jps.upsert("sp_d", records)

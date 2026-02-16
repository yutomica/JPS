
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import text

class SectorReturnProcessor:

    def __init__(self, db_manager_org, db_manager_jps):
        self.db_manager_org = db_manager_org
        self.db_manager_jps = db_manager_jps
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self, target_date=None):
        self.logger.info("Updating sector_return ...")
        sql = """
            SELECT LEFT(t1.Code,4) as scode, t1.Sector33Code as sector33_code, t2.Close, t2.Date
            FROM org.listed_info t1 INNER JOIN org.daily_prices t2 ON t1.Code = t2.Code
            WHERE t1.Date = :target_date 
            AND t2.Code like '%%0'
            AND t2.Date IN (
                :target_date, 
                (SELECT MAX(Date) FROM org.daily_prices WHERE Date < :target_date)
            ) ORDER BY t2.Date;
        """
        with self.db_manager_org.engine.connect() as conn:
            df = pd.read_sql(text(sql), con=conn, params={"target_date": target_date})

        # ---------------------------------------------------------
        # セクターリターン算出
        # ---------------------------------------------------------
        df['ret'] = df.groupby('scode')['Close'].pct_change()
        df = df.groupby(['Date', 'sector33_code'])['ret'].mean().reset_index().rename(columns={'ret': 'sector_return'}).dropna()

        # DB用データリストの作成
        records = []
        for _, row in df.iterrows():
            # NaN (Not a Number) を None に変換するヘルパー関数
            def clean_float(val):
                if pd.isna(val): return None
                return float(val)
            record = {
                "sector33_code": str(row['sector33_code']),
                "date": row['Date'],
                "sector_return": clean_float(row['sector_return']),
            }
            records.append(record)
        
        # DBへ保存
        self.db_manager_jps.upsert("sector_return", records)

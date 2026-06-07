
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.types import CHAR, DATE, FLOAT, BIGINT, VARCHAR

class scode_listProcessor:

    def __init__(self, db_manager_org, db_manager_jps):
        self.db_manager_org = db_manager_org
        self.db_manager_jps = db_manager_jps
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self, target_date=None):
        self.logger.info("Updating scode_list ...")
        sql = """
            WITH li AS (
                SELECT Left(Code,4) as scode, Close, Date as date
                FROM org.daily_prices
                WHERE Date = :target_date AND Right(Code,1) = '0'
            ),
            fin_latest AS (
                SELECT *
                FROM (
                    SELECT 
                        Left(f.Code, 4) as scode, 
                        f.ShOutFY, 
                        ROW_NUMBER() OVER (PARTITION BY f.Code ORDER BY f.DiscDate DESC, f.DiscTime DESC, f.DiscNo DESC) AS rn
                    FROM financials f
                    WHERE f.DiscDate <= :target_date AND f.ShOutFY IS NOT NULL
                ) x
                WHERE x.rn = 1
            ),
            stock_info AS (
                SELECT Left(Code,4) as scode, CompanyName as sname, MarketCodeName as market, Sector33CodeName as gyoshu, Sector33Code as sector33_code
                FROM org.listed_info 
                WHERE Date = :target_date AND Right(Code,1) = '0'
            )
            SELECT 
                li.scode,
                li.Close,
                li.date,
                stock_info.sname,
                stock_info.market,
                fin_latest.ShOutFY,
                stock_info.gyoshu,
                stock_info.sector33_code
            FROM li
            JOIN fin_latest ON li.scode = fin_latest.scode
            JOIN stock_info ON li.scode = stock_info.scode
        """
        # 1. データ取得
        with self.db_manager_org.engine.connect() as conn:
            df = pd.read_sql(text(sql), con=conn, params={"target_date": target_date})
        if df.empty:
            self.logger.warning("No data found for scode_list.")
            return

        # 2. データ加工
        df['mcode'] = 'T'
        # 時価総額計算 (終値 * 発行済株式数)
        df['Zikasougaku'] = df['Close'] * df['ShOutFY']
        
        # カラムの選択と並べ替え
        target_cols = ['scode', 'mcode', 'sname', 'market', 'sector33_code', 'gyoshu', 'Close', 'Zikasougaku', 'date']
        df = df[target_cols]

        # 3. テーブル作成とインサート (jps.scode_list)
        # to_sqlを使用すると、テーブル作成(CREATE)とインサートを同時に行えます
        # if_exists='replace' により、既存テーブルがあれば削除して作り直します
        # カラムの型定義 (適切な型でテーブルを作成するため)
        dtype_mapping = {
            'scode': CHAR(4),
            'mcode': CHAR(1),
            'sname': VARCHAR(255),
            'market': VARCHAR(255),
            'sector33_code': CHAR(4),
            'gyoshu': VARCHAR(255),
            'Close': FLOAT(),
            'Zikasougaku': BIGINT(), # 時価総額は桁が大きいためBIGINT推奨
            'date': DATE()
        }
        try:
            df.to_sql(
                name='scode_list',
                con=self.db_manager_jps.engine,
                if_exists='replace', # 既存テーブルをDROPしてCREATE
                index=False,
                dtype=dtype_mapping
            )
            self.logger.info("Successfully updated jps.scode_list.")
            
        except Exception as e:
            self.logger.error(f"Failed to update scode_list: {e}")


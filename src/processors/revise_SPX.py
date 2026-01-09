
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import text

class revise_SPXProcessor:

    def __init__(self, db_manager_jps):
        self.db_manager_jps = db_manager_jps
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run(self, target_date=None):
        self.logger.info("Revising SPX ...")

        # SP_D_REVLOGの最新日を確認 -> latest_rev
        sql = "SELECT DISTINCT EXE_DATE FROM SP_REV_LOG ORDER BY EXE_DATE DESC LIMIT 1"
        with self.db_manager_jps.engine.connect() as conn:
            df = pd.read_sql(text(sql), con=conn)
        latest_rev = df.iloc[0, 0] if not df.empty else None

        # 修正実行リスト作成
        sql = "SELECT ID,EXE_DATE,SCODE,SNAME,RATIO,TYPE FROM ORG.SP_REV_LIST WHERE EXE_DATE > '" 
        sql += datetime.strftime(latest_rev, "%Y-%m-%d") + "' AND EXE_DATE <= '" + datetime.strftime(target_date, "%Y-%m-%d") + "' ORDER BY EXE_DATE"
        with self.db_manager_jps.engine.connect() as conn:
            exe_list = pd.read_sql(text(sql), con=conn)
        if exe_list.empty:
            self.logger.info("No SPX revisions to process.")
            return
        self.logger.info("Num of candidates = "+str(len(exe_list)))

        # 修正処理実行
        cntr = 1
        for r in exe_list.index:
            try:
                ratio = exe_list.loc[r,'RATIO']
                amend_point = exe_list.loc[r]['EXE_DATE']
                sql = "SELECT DATE FROM SP_D WHERE SCODE = '" + exe_list.loc[r]['SCODE'] + "' ORDER BY DATE LIMIT 1"
                with self.db_manager_jps.engine.connect() as conn:
                    dd = pd.read_sql(text(sql), con=conn)
                dd = dd.iloc[0, 0]
                sql = "SELECT SCODE,SNAME,MCODE,MARKET,OPEN,HIGH,LOW,CLOSE,VOLUME,VOLUME_P,DATE FROM SP_D WHERE SCODE = '" 
                sql += exe_list.loc[r]['SCODE'] + "' AND DATE BETWEEN '" + dd.strftime('%Y-%m-%d') + "' AND '" + amend_point.strftime('%Y-%m-%d') + "'"
                with self.db_manager_jps.engine.connect() as conn:
                    _a = pd.read_sql(text(sql), con=conn)
                _a['OPEN'] = [x/ratio for x in _a['OPEN']]
                _a['HIGH'] = [x/ratio for x in _a['HIGH']]
                _a['LOW'] = [x/ratio for x in _a['LOW']]
                _a['CLOSE'] = [x/ratio for x in _a['CLOSE']]
                _a['VOLUME'] = [x for x in _a['VOLUME']]
                _a['VOLUME_P'] = [x for x in _a['VOLUME_P']]
                # 一旦削除
                sql = "DELETE FROM SP_D WHERE SCODE = '"
                sql += exe_list.loc[r]['SCODE'] + "' AND DATE BETWEEN '" + dd.strftime('%Y-%m-%d') + "' AND '" + amend_point.strftime('%Y-%m-%d') + "'"
                with self.db_manager_jps.engine.connect() as conn:
                    conn.execute(text(sql))
                # DBへ保存
                records = []
                for _, row in _a.iterrows():
                    # NaN (Not a Number) を None に変換するヘルパー関数
                    def clean_float(val):
                        if pd.isna(val): return None
                        return float(val)
                    record = {
                        "scode": str(row['SCODE']),
                        "mcode": str(row['MCODE']),
                        "sname": str(row['SNAME']),
                        "market": str(row['MARKET']),
                        "Open": clean_float(row['OPEN']),
                        "High": clean_float(row['HIGH']),
                        "Low": clean_float(row['LOW']),
                        "Close": clean_float(row['CLOSE']),
                        "Volume": int(row['VOLUME']),
                        "Volume_p": int(row['VOLUME_P']),
                        "date": row['DATE']
                    }
                    records.append(record)
                self.db_manager_jps.upsert("sp_d", records)
                self.logger.info(f"{cntr}/{len(exe_list)}: Revised SP_D for SCODE {exe_list.loc[r]['SCODE']} up to {amend_point.strftime('%Y-%m-%d')}")
                cntr += 1
            except:
                self.logger.error(f"Error revising SP_D for SCODE {exe_list.loc[r]['SCODE']}")
                continue

        # SP_REV_LOGに修正済みレコードを登録
        records = []
        for r in exe_list.index:
            record = {
                "ID": exe_list.loc[r]['ID'],
                "exe_date": exe_list.loc[r]['EXE_DATE'],
                "scode": exe_list.loc[r]['SCODE'],
                "sname": exe_list.loc[r]['SNAME'],
                "ratio": exe_list.loc[r]['RATIO'],
                "type": exe_list.loc[r]['TYPE'],
            }
            records.append(record)
        self.db_manager_jps.upsert("sp_rev_log", records)
        self.logger.info("SPX revision process completed.")

from datetime import datetime, date
from .base_loader import BaseLoader

class FinancialsLoader(BaseLoader):
    """
    財務情報サマリを取得・更新するローダー
    """
    def run(self, target_date=None):
        date_to_fetch = self.get_target_date(target_date)
        if isinstance(date_to_fetch, (datetime, date)):
            date_str = date_to_fetch.strftime("%Y%m%d")
        else:
            date_str = date_to_fetch.replace("-", "") # v2もYYYYMMDD形式
        self.logger.info(f"Fetching financial info (v2) for date: {date_str}")
        response = self.api_client.get("/fins/summary", params={"date": date_str})
        if len(response) == 0:
            self.logger.warning("No financial data received.")
            return
        # DB用データリストの作成
        # APIのレスポンスキーとDBのカラム名が一致しているか確認しながらマッピング
        records = []
        for item in response['data']:
            record = {
                'DiscDate': item.get('DiscDate'),
                'DiscTime': item.get('DiscTime'),
                'Code': item.get('Code'),
                'DiscNo': item.get('DiscNo'),
                'DocType': item.get('DocType'),
                'CurPerType': item.get('CurPerType'),
                'CurPerSt': item.get('CurPerSt'),
                'CurPerEn': item.get('CurPerEn'),
                'CurFYSt': item.get('CurFYSt'),
                'CurFYEn': item.get('CurFYEn'),
                'NxtFYSt': item.get('NxtFYSt'),
                'NxtFYEn': item.get('NxtFYEn'),
                'Sales': item.get('Sales'),
                'OP': item.get('OP'),
                'OdP': item.get('OdP'),
                'NP': item.get('NP'),
                'EPS': item.get('EPS'),
                'DEPS': item.get('DEPS'),
                'TA': item.get('TA'),
                'Eq': item.get('Eq'),
                'EqAR': item.get('EqAR'),
                'BPS': item.get('BPS'),
                'CFO': item.get('CFO'),
                'CFI': item.get('CFI'),
                'CFF': item.get('CFF'),
                'CashEq': item.get('CashEq'),
                'Div1Q': item.get('Div1Q'),
                'Div2Q': item.get('Div2Q'),
                'Div3Q': item.get('Div3Q'),
                'DivFY': item.get('DivFY'),
                'DivAnn': item.get('DivAnn'),
                'DivUnit': item.get('DivUnit'),
                'DivTotalAnn': item.get('DivTotalAnn'),
                'PayoutRatioAnn': item.get('PayoutRatioAnn'),
                'FDiv1Q': item.get('FDiv1Q'),
                'FDiv2Q': item.get('FDiv2Q'),
                'FDiv3Q': item.get('FDiv3Q'),
                'FDivFY': item.get('FDivFY'),
                'FDivAnn': item.get('FDivAnn'),
                'FDivUnit': item.get('FDivUnit'),
                'FDivTotalAnn': item.get('FDivTotalAnn'),
                'FPayoutRatioAnn': item.get('FPayoutRatioAnn'),
                'NxFDiv1Q': item.get('NxFDiv1Q'),
                'NxFDiv2Q': item.get('NxFDiv2Q'),
                'NxFDiv3Q': item.get('NxFDiv3Q'),
                'NxFDivFY': item.get('NxFDivFY'),
                'NxFDivAnn': item.get('NxFDivAnn'),
                'NxFDivUnit': item.get('NxFDivUnit'),
                'NxFPayoutRatioAnn': item.get('NxFPayoutRatioAnn'),
                'FSales2Q': item.get('FSales2Q'),
                'FOP2Q': item.get('FOP2Q'),
                'FOdP2Q': item.get('FOdP2Q'),
                'FNP2Q': item.get('FNP2Q'),
                'FEPS2Q': item.get('FEPS2Q'),
                'NxFSales2Q': item.get('NxFSales2Q'),
                'NxFOP2Q': item.get('NxFOP2Q'),
                'NxFOdP2Q': item.get('NxFOdP2Q'),
                'NxFNp2Q': item.get('NxFNp2Q'),
                'NxFEPS2Q': item.get('NxFEPS2Q'),
                'FSales': item.get('FSales'),
                'FOP': item.get('FOP'),
                'FOdP': item.get('FOdP'),
                'FNP': item.get('FNP'),
                'FEPS': item.get('FEPS'),
                'NxFSales': item.get('NxFSales'),
                'NxFOP': item.get('NxFOP'),
                'NxFOdP': item.get('NxFOdP'),
                'NxFNp': item.get('NxFNp'),
                'NxFEPS': item.get('NxFEPS'),
                'MatChgSub': item.get('MatChgSub'),
                'SigChgInC': item.get('SigChgInC'),
                'ChgByASRev': item.get('ChgByASRev'),
                'ChgNoASRev': item.get('ChgNoASRev'),
                'ChgAcEst': item.get('ChgAcEst'),
                'RetroRst': item.get('RetroRst'),
                'ShOutFY': item.get('ShOutFY'),
                'TrShFY': item.get('TrShFY'),
                'AvgSh': item.get('AvgSh'),
                'NCSales': item.get('NCSales'),
                'NCOP': item.get('NCOP'),
                'NCOdP': item.get('NCOdP'),
                'NCNP': item.get('NCNP'),
                'NCEPS': item.get('NCEPS'),
                'NCTA': item.get('NCTA'),
                'NCEq': item.get('NCEq'),
                'NCEqAR': item.get('NCEqAR'),
                'NCBPS': item.get('NCBPS'),
                'FNCSales2Q': item.get('FNCSales2Q'),
                'FNCOP2Q': item.get('FNCOP2Q'),
                'FNCOdP2Q': item.get('FNCOdP2Q'),
                'FNCNP2Q': item.get('FNCNP2Q'),
                'FNCEPS2Q': item.get('FNCEPS2Q'),
                'NxFNCSales2Q': item.get('NxFNCSales2Q'),
                'NxFNCOP2Q': item.get('NxFNCOP2Q'),
                'NxFNCOdP2Q': item.get('NxFNCOdP2Q'),
                'NxFNCNP2Q': item.get('NxFNCNP2Q'),
                'NxFNCEPS2Q': item.get('NxFNCEPS2Q'),
                'FNCSales': item.get('FNCSales'),
                'FNCOP': item.get('FNCOP'),
                'FNCOdP': item.get('FNCOdP'),
                'FNCNP': item.get('FNCNP'),
                'FNCEPS': item.get('FNCEPS'),
                'NxFNCSales': item.get('NxFNCSales'),
                'NxFNCOP': item.get('NxFNCOP'),
                'NxFNCOdP': item.get('NxFNCOdP'),
                'NxFNCNP': item.get('NxFNCNP'),
                'NxFNCEPS': item.get('NxFNCEPS'),
            }
            # 【重要】空文字("")をNoneに変換して、DBのNULLとして扱えるようにする
            for k, v in record.items():
                if v == "":
                    record[k] = None
            records.append(record)

        # DBへ保存
        self.db_manager.upsert("financials", records)
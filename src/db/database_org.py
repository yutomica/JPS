import logging
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, Date, BigInteger, Text, inspect
from sqlalchemy.dialects.mysql import insert, INTEGER, BIGINT, VARCHAR, CHAR
from sqlalchemy.engine import Engine

class DatabaseManager_ORG:
    """
    MySQLデータベースへの接続、テーブル作成、データ登録（Upsert）を管理するクラス。
    SQLAlchemy Coreを使用しています。
    """
    def __init__(self, connection_string: str):
        """
        Args:
            connection_string (str): DB接続文字列 (例: mysql+pymysql://user:pass@host/dbname)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        # echo=False にしてSQLログの大量出力を防ぎます
        self.engine: Engine = create_engine(connection_string, echo=False, pool_pre_ping=True)
        self.metadata = MetaData()
        # テーブル定義の読み込み
        self._define_tables()

    def _define_tables(self):
        """
        テーブルのスキーマ定義を行います。
        J-Quants API (Lightプラン) の仕様に基づき、全カラムを定義しています。
        """
        # ==============================================================================
        # 1. 銘柄情報 (Listed Info)
        # API Reference: https://jquants.com/api/v1/notes/#/Listed/get_listed_info
        # ==============================================================================
        self.listed_info = Table(
            'listed_info', self.metadata,
            Column('Code', String(10), primary_key=True, comment='銘柄コード'),
            Column('Date', Date, primary_key=True, comment='日付'),
            Column('CompanyName', String(255), comment='会社名'),
            Column('CompanyNameEnglish', String(255), comment='会社名(英)'),
            Column('Sector17Code', String(10), comment='17業種コード'),
            Column('Sector17CodeName', String(255), comment='17業種名'),
            Column('Sector33Code', String(10), comment='33業種コード'),
            Column('Sector33CodeName', String(255), comment='33業種名'),
            Column('ScaleCategory', String(50), comment='規模区分'),
            Column('MarketCode', String(10), comment='市場コード'),
            Column('MarketCodeName', String(255), comment='市場名'),
            Column('MarginCode', String(10), comment='信用区分コード'),
            Column('MarginCodeName', String(50), comment='信用区分名'),
        )

        # ==============================================================================
        # 2. 日足株価 (Daily Prices)
        # API Reference: https://jquants.com/api/v1/notes/#/Prices/get_prices_daily_quotes
        # ==============================================================================
        self.daily_prices = Table(
            'daily_prices', self.metadata,
            # 複合主キー: 日付 + 銘柄コード
            Column('Date', Date, primary_key=True, comment='日付'),
            Column('Code', String(10), primary_key=True, comment='銘柄コード'),
            Column('Open', Float, comment='始値'),
            Column('High', Float, comment='高値'),
            Column('Low', Float, comment='安値'),
            Column('Close', Float, comment='終値'),
            Column('UpperLimit', String(10), comment='日通ストップ高フラグ（0：ストップ高以外, 1：ストップ高）'),
            Column('LowerLimit', String(10), comment='日通ストップ安フラグ（0：ストップ安以外, 1：ストップ安）'),
            Column('Volume', Float, comment='出来高'), # API仕様上はNumberだが、大きな値になるためFloatかBigInt推奨
            Column('Turnover', Float, comment='売買代金'),
            Column('AdjustmentFactor', Float, comment='調整係数'),
            Column('AdjustmentOpen', Float, comment='調整後始値'),
            Column('AdjustmentHigh', Float, comment='調整後高値'),
            Column('AdjustmentLow', Float, comment='調整後安値'),
            Column('AdjustmentClose', Float, comment='調整後終値'),
            Column('AdjustmentVolume', Float, comment='調整後出来高'),
        )
        
        # ==============================================================================
        # 3. 財務情報 (Financial Summary)
        # API Reference: https://jpx-jquants.com/ja/spec/fin-summary
        # ==============================================================================
        self.financials = Table(
            'financials', self.metadata,
            Column('DiscDate',String(255), comment='開示日'),
            Column('DiscTime',String(255), comment='開示時刻'),
            Column('Code',String(255), primary_key=True, comment='銘柄コード'),
            Column('DiscNo',String(255), primary_key=True, comment='開示番号'),
            Column('DocType',String(255), comment='開示資料種別'),
            Column('CurPerType',String(255), comment='当期区分（1Q/2Q/3Q/FY）'),
            Column('CurPerSt',String(255), comment='当期開始日'),
            Column('CurPerEn',String(255), comment='当期終了日'),
            Column('CurFYSt',String(255), comment='当事業年度開始日'),
            Column('CurFYEn',String(255), comment='当事業年度終了日'),
            Column('NxtFYSt',String(255), comment='次事業年度開始日'),
            Column('NxtFYEn',String(255), comment='次事業年度終了日'),
            Column('Sales',Float, comment='売上高（連結・実績）'),
            Column('OP',Float, comment='営業利益（連結・実績）'),
            Column('OdP',Float, comment='経常利益（連結・実績）'),
            Column('NP',Float, comment='当期純利益（連結・実績）'),
            Column('EPS',Float, comment='1株当たり利益（EPS）'),
            Column('DEPS',Float, comment='希薄化後EPS'),
            Column('TA',Float, comment='総資産'),
            Column('Eq',Float, comment='純資産'),
            Column('EqAR',Float, comment='自己資本比率'),
            Column('BPS',Float, comment='1株当たり純資産'),
            Column('CFO',Float, comment='営業キャッシュフロー'),
            Column('CFI',Float, comment='投資キャッシュフロー'),
            Column('CFF',Float, comment='財務キャッシュフロー'),
            Column('CashEq',Float, comment='現金及び現金同等物'),
            Column('Div1Q',Float, comment='第1四半期配当（実績）'),
            Column('Div2Q',Float, comment='第2四半期配当（実績）'),
            Column('Div3Q',Float, comment='第3四半期配当（実績）'),
            Column('DivFY',Float, comment='期末配当（実績）'),
            Column('DivAnn',Float, comment='年間配当（実績）'),
            Column('DivUnit',String(255), comment='配当単位'),
            Column('DivTotalAnn',Float, comment='年間配当総額'),
            Column('PayoutRatioAnn',Float, comment='配当性向'),
            Column('FDiv1Q',Float, comment='第1四半期配当予想'),
            Column('FDiv2Q',Float, comment='第2四半期配当予想'),
            Column('FDiv3Q',Float, comment='第3四半期配当予想'),
            Column('FDivFY',Float, comment='期末配当予想'),
            Column('FDivAnn',Float, comment='年間配当予想'),
            Column('FDivUnit',String(255), comment='配当単位（予想）'),
            Column('FDivTotalAnn',Float, comment='年間配当総額予想'),
            Column('FPayoutRatioAnn',Float, comment='配当性向予想'),
            Column('NxFDiv1Q',Float, comment='次期1Q配当予想'),
            Column('NxFDiv2Q',Float, comment='次期2Q配当予想'),
            Column('NxFDiv3Q',Float, comment='次期3Q配当予想'),
            Column('NxFDivFY',Float, comment='次期期末配当予想'),
            Column('NxFDivAnn',Float, comment='次期年間配当予想'),
            Column('NxFDivUnit',String(255), comment='次期配当単位'),
            Column('NxFPayoutRatioAnn',Float, comment='次期配当性向'),
            Column('FSales2Q',Float, comment='2Q累計売上予想'),
            Column('FOP2Q',Float, comment='2Q累計営業利益予想'),
            Column('FOdP2Q',Float, comment='2Q累計経常利益予想'),
            Column('FNP2Q',Float, comment='2Q累計純利益予想'),
            Column('FEPS2Q',Float, comment='2Q累計EPS予想'),
            Column('NxFSales2Q',Float, comment='次期2Q累計売上予想'),
            Column('NxFOP2Q',Float, comment='次期2Q累計営業利益予想'),
            Column('NxFOdP2Q',Float, comment='次期2Q累計経常利益予想'),
            Column('NxFNp2Q',Float, comment='次期2Q累計純利益予想'),
            Column('NxFEPS2Q',Float, comment='次期2Q累計EPS予想'),
            Column('FSales',Float, comment='通期売上予想'),
            Column('FOP',Float, comment='通期営業利益予想'),
            Column('FOdP',Float, comment='通期経常利益予想'),
            Column('FNP',Float, comment='通期純利益予想'),
            Column('FEPS',Float, comment='通期EPS予想'),
            Column('NxFSales',Float, comment='次期通期売上予想'),
            Column('NxFOP',Float, comment='次期通期営業利益予想'),
            Column('NxFOdP',Float, comment='次期通期経常利益予想'),
            Column('NxFNp',Float, comment='次期通期純利益予想'),
            Column('NxFEPS',Float, comment='次期通期EPS予想'),
            Column('MatChgSub',String(255), comment='重要な子会社異動有無'),
            Column('SigChgInC',String(255), comment='経営成績の重要な変動'),
            Column('ChgByASRev',String(255), comment='会計基準変更による修正'),
            Column('ChgNoASRev',String(255), comment='会計基準変更なし'),
            Column('ChgAcEst',String(255), comment='会計上の見積変更'),
            Column('RetroRst',String(255), comment='遡及修正'),
            Column('ShOutFY',Float, comment='期末発行済株式数'),
            Column('TrShFY',Float, comment='期末自己株式数'),
            Column('AvgSh',Float, comment='期中平均株式数'),
            Column('NCSales',Float, comment='非連結売上高'),
            Column('NCOP',Float, comment='非連結営業利益'),
            Column('NCOdP',Float, comment='非連結経常利益'),
            Column('NCNP',Float, comment='非連結純利益'),
            Column('NCEPS',Float, comment='非連結EPS'),
            Column('NCTA',Float, comment='非連結総資産'),
            Column('NCEq',Float, comment='非連結純資産'),
            Column('NCEqAR',Float, comment='非連結自己資本比率'),
            Column('NCBPS',Float, comment='非連結BPS'),
            Column('FNCSales2Q',Float, comment='非連結2Q売上予想'),
            Column('FNCOP2Q',Float, comment='非連結2Q営業利益予想'),
            Column('FNCOdP2Q',Float, comment='非連結2Q経常利益予想'),
            Column('FNCNP2Q',Float, comment='非連結2Q純利益予想'),
            Column('FNCEPS2Q',Float, comment='非連結2Q EPS予想'),
            Column('NxFNCSales2Q',Float, comment='次期非連結2Q売上予想'),
            Column('NxFNCOP2Q',Float, comment='次期非連結2Q営業利益予想'),
            Column('NxFNCOdP2Q',Float, comment='次期非連結2Q経常利益予想'),
            Column('NxFNCNP2Q',Float, comment='次期非連結2Q純利益予想'),
            Column('NxFNCEPS2Q',Float, comment='次期非連結2Q EPS予想'),
            Column('FNCSales',Float, comment='非連結通期売上予想'),
            Column('FNCOP',Float, comment='非連結通期営業利益予想'),
            Column('FNCOdP',Float, comment='非連結通期経常利益予想'),
            Column('FNCNP',Float, comment='非連結通期純利益予想'),
            Column('FNCEPS',Float, comment='非連結通期EPS予想'),
            Column('NxFNCSales',Float, comment='次期非連結通期売上予想'),
            Column('NxFNCOP',Float, comment='次期非連結通期営業利益予想'),
            Column('NxFNCOdP',Float, comment='次期非連結通期経常利益予想'),
            Column('NxFNCNP',Float, comment='次期非連結通期純利益予想'),
            Column('NxFNCEPS',Float, comment='次期非連結通期EPS予想'),       
        )
        
        # ==============================================================================
        # 4. 決算発表予定日 (Earnings Calendar)
        # API Reference: https://jpx-jquants.com/ja/spec/eq-earnings-cal
        # ==============================================================================
        self.earnings_calendar = Table(
            'earnings_calendar', self.metadata,
            Column('Date', Date, primary_key=True, comment='決算発表予定日'),
            Column('Code', String(10), primary_key=True, comment='銘柄コード'),
            Column('CompanyName', String(255), comment='会社名'),
            Column('FiscalYear', String(10), comment='決算期末'),
            Column('SectorName', String(255), comment='業種名'),
            Column('FQ', String(10), comment='決算種別)'),
            Column('Section', String(255), comment='市場区分'),
        )
        
        # ==============================================================================
        # 5. 指数日足: TOPIX (Indices - TOPIX Daily)
        # API Reference: https://jpx-jquants.com/ja/spec/idx-bars-daily-topix
        # ==============================================================================
        self.indices_topix = Table(
            'indices_topix', self.metadata,
            Column('Date', Date, primary_key=True, comment='日付'),
            Column('Open', Float, comment='始値'),
            Column('High', Float, comment='高値'),
            Column('Low', Float, comment='安値'),
            Column('Close', Float, comment='終値'),
        )

        # ==============================================================================
        # 6. 株式分割＆併合銘柄リスト: TOPIX (Indices - TOPIX Daily)
        # API Reference: 
        # ==============================================================================
        self.indices_topix = Table(
            'sp_rev_list', self.metadata,
            Column('ID', CHAR(15), primary_key=True),
            Column('exe_date', Date),
            Column('scode', CHAR(4)),
            Column('sname', VARCHAR(255)),
            Column('ratio', Float),
            Column('type', CHAR(10)),
        )

    def init_database(self):
        """
        テーブルが存在しない場合に作成します。
        """
        try:
            self.metadata.create_all(self.engine)
            self.logger.info("Tables initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize database tables: {e}")
            raise

    def upsert(self, table_name: str, records: list):
        """
        MySQLの 'INSERT ... ON DUPLICATE KEY UPDATE' 構文を使用してデータを登録します。
        既存のレコード（主キー重複）がある場合は値を更新します。
        Args:
            table_name (str): 対象のテーブル名 ('listed_info', 'daily_prices', 'financials')
            records (list): 辞書のリスト [{'col': val, ...}, ...]
        """
        if not records:
            self.logger.info(f"No records to upsert for {table_name}.")
            return
        # テーブルオブジェクトの取得
        target_table = self.metadata.tables.get(table_name)
        if target_table is None:
            raise ValueError(f"Table '{table_name}' is not defined.")
        try:
            with self.engine.begin() as conn:
                # MySQL固有のInsertオブジェクトを作成
                stmt = insert(target_table).values(records)
                # 重複時の更新用辞書を作成
                # {カラム名: stmt.inserted.カラム名} の形式にすることで、
                # 「新しい値で既存の値を上書きする」という動作になります。
                update_dict = {
                    c.name: stmt.inserted[c.name]
                    for c in target_table.columns
                    if not c.primary_key # 主キー以外の全カラムを更新対象にする
                }
                # ON DUPLICATE KEY UPDATE 句を付与
                upsert_stmt = stmt.on_duplicate_key_update(update_dict)
                # 実行
                result = conn.execute(upsert_stmt)
                self.logger.info(f"Upserted {len(records)} records into '{table_name}'.")
        except Exception as e:
            self.logger.error(f"Failed to upsert data into {table_name}: {e}")
            raise
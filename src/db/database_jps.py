
import logging
from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, Date, BigInteger, Text, inspect
from sqlalchemy.dialects.mysql import insert, INTEGER, BIGINT, VARCHAR, CHAR
from sqlalchemy.engine import Engine

class DatabaseManager_JPS:
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
        """
        # ==============================================================================
        # 日足データ (sp_d)
        # ==============================================================================
        self.listed_info = Table(
            'sp_d', self.metadata,
            Column('scode', CHAR(4), primary_key=True),
            Column('mcode', CHAR(2)),
            Column('sname', VARCHAR(255)),
            Column('market', VARCHAR(255)),
            Column('Open', Float),
            Column('High', Float),
            Column('Low', Float),
            Column('Close', Float),
            Column('Volume', INTEGER(unsigned=True)),
            Column('Volume_p', BIGINT(unsigned=True)),
            Column('date', Date, primary_key=True),
        )
        
        # ==============================================================================
        # 銘柄コードリスト (scode_list)
        # ==============================================================================
        self.listed_info = Table(
            'scode_list', self.metadata,
            Column('scode', CHAR(4), primary_key=True),
            Column('mcode', CHAR(2)),
            Column('sname', VARCHAR(255)),
            Column('market', VARCHAR(255)),
            Column('gyoshu', VARCHAR(255)),
            Column('Close', Float),
            Column('Zikasougaku', BIGINT(unsigned=True)),
            Column('date', Date, primary_key=True),
        )

        # ==============================================================================
        # 株式分割＆併合対応済みコードリスト (sp_rev_log)
        # ==============================================================================
        self.sp_rev_log = Table(
            'sp_rev_log', self.metadata,
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

import logging
from datetime import datetime, timedelta

class BaseLoader:
    """
    全てのデータローダーの基底クラス。
    """
    def __init__(self, api_client, db_manager):
        self.api_client = api_client
        self.db_manager = db_manager
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self, target_date=None):
        """
        実行のエントリーポイント。サブクラスでオーバーライドしてください。
        """
        raise NotImplementedError("Subclasses must implement run()")

    def get_target_date(self, target_date):
        """
        target_dateがNoneの場合、昨日の日付をデフォルトとして返します。
        （日次バッチ処理の一般的なデフォルト動作）
        """
        if target_date:
            return target_date
        # デフォルトは昨日（当日分は夜間まで確定しない場合が多いため）
        return datetime.now() - timedelta(days=1)
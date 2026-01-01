import os
import sys
import logging
import logging.config
import argparse
from datetime import datetime
from dotenv import load_dotenv

try:
    # 通常のスクリプト実行時（python src/main.py とした時）
    file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(file_path))
except NameError:
    # Jupyter Notebookやインタラクティブモード時
    # 現在の作業ディレクトリ（カレントディレクトリ）をプロジェクトルートとみなす
    project_root = os.path.abspath(os.getcwd())
if project_root not in sys.path:
    sys.path.append(project_root)

# 【注意】 以下のモジュールは、提案したフォルダ構成に基づいて
# 今後作成していくファイルをimportしています。
# 現時点ではファイルが存在しないためエラーになりますが、設計図として参照してください。
from src.api.client import JQuantsApiClient
from src.db.database import DatabaseManager
from src.loaders.listed_info import ListedInfoLoader
from src.loaders.prices import PricesLoader
from src.loaders.financials import FinancialsLoader
from src.loaders.earnings_calendar import EarningsCalendarLoader
from src.loaders.indices_topix import IndicesTopixLoader

def setup_logging():
    """
    ログ設定を初期化します。
    コンソール出力とファイル出力（logs/daily_log.log）の両方を行います。
    """
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'daily_log.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )

def validate_date(date_str):
    """
    引数がYYYY-MM-DD形式であるか検証し、datetimeオブジェクトを返します。
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_str}'. Expected format is YYYY-MM-DD.")

def parse_args():
    """
    コマンドライン引数を解析します。
    """
    parser = argparse.ArgumentParser(description="J-Quants Daily Data Loader")
    parser.add_argument(
        "--date",
        type=validate_date,
        help="Target date for data retrieval (Format: YYYY-MM-DD). If omitted, automatic date determination is used.",
        default=None
    )
    return parser.parse_args()

def main():
    # 1. 初期設定
    setup_logging()
    logger = logging.getLogger('JQuantsLoader')
    
    # 引数の解析
    args = parse_args()
    target_date = args.date
    
    if target_date:
        logger.info(f"=== J-Quants Data Loader Started (Target Date: {target_date.strftime('%Y-%m-%d')}) ===")
    else:
        logger.info("=== J-Quants Daily Data Loader Started (Auto Mode) ===")

    # .envファイルから環境変数を読み込み
    load_dotenv(os.path.join(project_root, '.env'))
    jq_api_key = os.getenv("JQ_API_KEY")
    api_client = JQuantsApiClient(api_key=jq_api_key)

    try:
        # 2. 共通コンポーネントの初期化
        
        # DBマネージャー（接続確立）
        # logger.info("Initializing Database Connection...")
        # DB接続情報は .env や settings.yaml から読み込む想定
        db_manager = DatabaseManager(os.getenv("DB_CONNECTION_STRING", "sqlite:///jquants.db"))
        db_manager.init_database()

        # 3. 各ローダーの実行
        # データの依存関係を考慮して実行順序を決定します。
        # 各ローダーの run メソッドには target_date を渡します。
        # Noneの場合はローダー側で自動判定するロジックを実装します。
        
        # Step 1: 銘柄情報 (Master Data)
        # 上場廃止や新規上場があるため、一番最初に更新します。
        # logger.info(">>> Processing Listed Info...")
        # loader_info = ListedInfoLoader(api_client, db_manager)
        # loader_info.run(target_date=target_date) # 全銘柄リストの更新

        # Step 2: 日足株価 (Transaction Data)
        logger.info(">>> Processing Daily Prices...")
        loader_prices = PricesLoader(api_client, db_manager)
        loader_prices.run(target_date=target_date) 

        # Step 3: 財務情報 (Event Data)
        logger.info(">>> Processing Financial Statements...")
        loader_financials = FinancialsLoader(api_client, db_manager)
        loader_financials.run(target_date=target_date)

        # Step 4: 決算カレンダー (Event Data)
        logger.info(">>> Processing Earnings Calendar...")
        loader_earnings = EarningsCalendarLoader(api_client, db_manager)
        loader_earnings.run(target_date=target_date)

        # Step 5: TOPIX指数 (Event Data)
        logger.info(">>> Processing TOPIX Index...")
        loader_indices_topix = IndicesTopixLoader(api_client, db_manager)
        loader_indices_topix.run(target_date=target_date)

        logger.info("=== All tasks completed successfully ===")

    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        # エラー時は非ゼロで終了し、スケジューラ（cron等）に失敗を通知する
        sys.exit(1)
    finally:
        # DB切断などの後処理が必要な場合
        if 'db_manager' in locals():
            # db_manager.close() # 実装に応じて
            pass

if __name__ == "__main__":
    main()
import requests
import logging
import time

class JQuantsApiClient:
    """
    J-Quants API v2 クライアント
    APIキー方式による認証とリクエスト管理を行います。
    """
    BASE_URL = "https://api.jquants.com/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)

    def get(self, endpoint: str, params: dict = None):
        """
        GETリクエストを送信します。
        自動的に x-api-key ヘッダーを付与します。
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        # v2認証ヘッダー
        headers = {
            "x-api-key": self.api_key
        }
        
        self.logger.debug(f"Fetching data from {url} with params: {params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # 403 Forbidden: APIキーの間違いや権限不足
            if response.status_code == 403:
                self.logger.error("403 Forbidden: API Key is invalid or plan restriction.")
                response.raise_for_status()
                
            # 429 Too Many Requests: レートリミット（Lightプランは60回/分）
            if response.status_code == 429:
                self.logger.warning("Rate limit exceeded. Waiting for retry...")
                time.sleep(10) # 簡易的なリトライ待機
                return self.get(endpoint, params) # 再帰呼び出し

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"API Request Failed: {response.status_code} - {response.text}")
                response.raise_for_status()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error occurred: {e}")
            raise
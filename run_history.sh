#!/bin/bash

# ==========================================
# J-Quants Historical Data Loader (MacOS版)
# ==========================================

# 設定
START_DATE="2016-01-31"
END_DATE="2026-01-20"
LOG_FILE="history_load.log"
PYTHON_CMD="python" # 環境に合わせて "python3" や "venv/bin/python" に変更してください

# 実行開始ログ
echo "=== Batch Process Started: $START_DATE to $END_DATE ===" > "$LOG_FILE"
echo "Log file: $LOG_FILE"

# ループ変数の初期化
CURRENT_DATE="$START_DATE"

# ループ処理 (現在日付が終了日付を過ぎるまで)
while [[ "$CURRENT_DATE" < "$END_DATE" ]] || [[ "$CURRENT_DATE" == "$END_DATE" ]]; do
    
    echo "Processing Date: $CURRENT_DATE" | tee -a "$LOG_FILE"
    
    # ---------------------------------------------------------
    # Pythonスクリプト実行
    # 標準出力(1)と標準エラー出力(2)をログファイルに追記(>>)する
    # ---------------------------------------------------------
    $PYTHON_CMD src/main.py --date "$CURRENT_DATE" >> "$LOG_FILE" 2>&1
    
    # 実行結果の簡易チェック（直前のコマンドが成功したか）
    if [ $? -eq 0 ]; then
        echo "  -> Success" | tee -a "$LOG_FILE"
    else
        echo "  -> Failed (Check logs)" | tee -a "$LOG_FILE"
    fi

    # ---------------------------------------------------------
    # 日付のインクリメント (MacOS / BSD dateコマンド仕様)
    # -j: 日付を設定せず変換のみ
    # -v+1d: 1日進める
    # -f: 入力フォーマット指定
    # ---------------------------------------------------------
    CURRENT_DATE=$(date -j -v+1d -f "%Y-%m-%d" "$CURRENT_DATE" +%Y-%m-%d)

    # ---------------------------------------------------------
    # レートリミット対策 (重要)
    # APIへの負荷を避けるため、次のリクエストまで少し待機します
    # ---------------------------------------------------------
    sleep 2

done

echo "=== Batch Process Completed ===" | tee -a "$LOG_FILE"
#!/bin/bash

# ========================================================
# 設定エリア: 環境に合わせてパスを確認・修正してください
# ========================================================

# 1. プロジェクトのルートディレクトリ
PROJECT_DIR="/Users/yuu/JPS"

# 2. Pythonの実行パス
PYTHON_EXE="/Users/yuu/.pyenv/versions/3.10.0/bin/python"

# 3. ログファイルの保存場所
LOG_FILE="${PROJECT_DIR}/logs/cron_execution.log"

# ========================================================
# 実行処理
# ========================================================

# ログディレクトリがない場合は作成
mkdir -p "${PROJECT_DIR}/logs"

# 実行日時点の日付を取得 (YYYY-MM-DD形式)
TARGET_DATE=$(date "+%Y-%m-%d")

# 開始ログ
echo "-----------------------------------------------------" >> "$LOG_FILE"
echo "Daily Batch Started at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "Target Date: $TARGET_DATE" >> "$LOG_FILE"

# プロジェクトディレクトリに移動
cd "$PROJECT_DIR" || {
    echo "Error: Failed to change directory to $PROJECT_DIR" >> "$LOG_FILE"
    exit 1
}

# Pythonスクリプトの実行
# 【修正箇所】取得した日付を --date 引数で渡す
"$PYTHON_EXE" src/main.py --date "$TARGET_DATE" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

# 終了ログ
if [ $EXIT_CODE -eq 0 ]; then
    echo "Daily Batch Completed Successfully at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
else
    echo "Daily Batch Failed with exit code $EXIT_CODE at: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
fi

exit $EXIT_CODE
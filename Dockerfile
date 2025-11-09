# ============================================
# ES診断ツール - Cloud Run Optimized Dockerfile
# ============================================

# ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリ
WORKDIR /app

# 環境変数
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

# システム依存パッケージのインストール
# Cloud Run用に必要最小限に
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Pythonパッケージの依存関係をコピーしてインストール
COPY requirements.txt .

# Cloud Storage クライアントライブラリを追加
RUN echo "google-cloud-storage>=2.10.0" >> requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY src/ ./src/
COPY templates/ ./templates/

# 前処理済みデータをコピー（高速起動のため）
COPY es_preprocessed_data/ ./es_preprocessed_data/

# dataディレクトリは作成のみ（前処理済みデータを優先使用）
RUN mkdir -p ./data

# ポート公開（Cloud RunはPORT環境変数を使用）
EXPOSE $PORT

# ヘルスチェック（Cloud Runは独自のヘルスチェックを使用するため不要だがローカルテスト用に残す）
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/docs')" || exit 1

# 非rootユーザーで実行（セキュリティベストプラクティス）
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 起動スクリプトを作成
RUN echo '#!/bin/bash\n\
uvicorn src.app:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh \
    && chmod +x /app/start.sh

# アプリケーション起動（Cloud RunのPORT環境変数を使用）
CMD ["sh", "-c", "uvicorn src.app:app --host 0.0.0.0 --port ${PORT:-8000}"]

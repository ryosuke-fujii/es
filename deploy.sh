#!/bin/bash

# ============================================
# ES診断ツール - GCP Cloud Run デプロイスクリプト
# ============================================

set -e  # エラーが発生したら即座に終了

# 色付きログ出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ出力関数
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================
# 設定
# ============================================

# デフォルト値
DEFAULT_REGION="asia-northeast1"  # 東京リージョン
DEFAULT_SERVICE_NAME="es-diagnosis-tool"
DEFAULT_REPOSITORY="es-diagnosis-tool"
DEFAULT_MEMORY="4Gi"
DEFAULT_CPU="2"
DEFAULT_MAX_INSTANCES="10"
DEFAULT_MIN_INSTANCES="0"

# 環境変数から読み込むか、対話的に入力
echo ""
echo "======================================"
echo "🚀 ES診断ツール GCP デプロイ"
echo "======================================"
echo ""

# プロジェクトIDの確認
if [ -z "$PROJECT_ID" ]; then
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [ -n "$CURRENT_PROJECT" ]; then
        log_info "現在のプロジェクト: $CURRENT_PROJECT"
        read -p "このプロジェクトでデプロイしますか？ (y/n): " use_current
        if [ "$use_current" = "y" ] || [ "$use_current" = "Y" ]; then
            PROJECT_ID=$CURRENT_PROJECT
        fi
    fi

    if [ -z "$PROJECT_ID" ]; then
        read -p "GCPプロジェクトIDを入力してください: " PROJECT_ID
    fi
fi

log_success "プロジェクトID: $PROJECT_ID"

# リージョンの確認
if [ -z "$REGION" ]; then
    read -p "リージョン (デフォルト: $DEFAULT_REGION): " REGION
    REGION=${REGION:-$DEFAULT_REGION}
fi

log_success "リージョン: $REGION"

# サービス名
SERVICE_NAME=${SERVICE_NAME:-$DEFAULT_SERVICE_NAME}
REPOSITORY=${REPOSITORY:-$DEFAULT_REPOSITORY}

# イメージタグ
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/app:latest"

echo ""
log_info "デプロイ設定:"
echo "  - プロジェクトID: $PROJECT_ID"
echo "  - リージョン: $REGION"
echo "  - サービス名: $SERVICE_NAME"
echo "  - イメージ: $IMAGE_TAG"
echo ""

read -p "この設定でデプロイを開始しますか？ (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    log_warning "デプロイをキャンセルしました"
    exit 0
fi

# ============================================
# 前処理
# ============================================

log_info "gcloud CLIの設定を確認中..."

# プロジェクトを設定
gcloud config set project $PROJECT_ID

log_success "プロジェクト設定完了"

# ============================================
# APIの有効化
# ============================================

log_info "必要なAPIを有効化中..."

gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  storage-api.googleapis.com \
  --quiet

log_success "API有効化完了"

# ============================================
# Artifact Registryリポジトリの作成
# ============================================

log_info "Artifact Registryリポジトリを確認中..."

if ! gcloud artifacts repositories describe $REPOSITORY --location=$REGION &>/dev/null; then
    log_info "Artifact Registryリポジトリを作成中..."
    gcloud artifacts repositories create $REPOSITORY \
      --repository-format=docker \
      --location=$REGION \
      --description="ES診断ツール Dockerイメージ" \
      --quiet
    log_success "リポジトリ作成完了"
else
    log_success "リポジトリは既に存在します"
fi

# ============================================
# Docker認証の設定
# ============================================

log_info "Docker認証を設定中..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
log_success "Docker認証設定完了"

# ============================================
# Dockerイメージのビルドとプッシュ
# ============================================

echo ""
log_info "Dockerイメージをビルド中..."
echo ""

# Cloud Buildを使用してビルド
log_info "Cloud Buildでビルドを実行します（数分かかります）..."

gcloud builds submit \
  --tag $IMAGE_TAG \
  --timeout=20m \
  --machine-type=e2-highcpu-8

log_success "イメージビルド完了"

# ============================================
# Cloud Storageバケットの作成（オプション）
# ============================================

BUCKET_NAME="${PROJECT_ID}-es-data"

log_info "Cloud Storageバケットを確認中..."

if ! gsutil ls gs://$BUCKET_NAME &>/dev/null; then
    read -p "前処理済みデータ用のCloud Storageバケットを作成しますか？ (y/n): " create_bucket
    if [ "$create_bucket" = "y" ] || [ "$create_bucket" = "Y" ]; then
        log_info "Cloud Storageバケットを作成中..."
        gsutil mb -l $REGION gs://$BUCKET_NAME
        log_success "バケット作成完了: gs://$BUCKET_NAME"

        if [ -d "es_preprocessed_data" ]; then
            read -p "前処理済みデータをアップロードしますか？ (y/n): " upload_data
            if [ "$upload_data" = "y" ] || [ "$upload_data" = "Y" ]; then
                log_info "データをアップロード中..."
                gsutil -m cp -r es_preprocessed_data/* gs://$BUCKET_NAME/preprocessed/
                log_success "データアップロード完了"
            fi
        fi
    fi
else
    log_success "バケットは既に存在します: gs://$BUCKET_NAME"
fi

# ============================================
# Cloud Runにデプロイ
# ============================================

echo ""
log_info "Cloud Runにデプロイ中..."
echo ""

gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE_TAG \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --port=8000 \
  --memory=$DEFAULT_MEMORY \
  --cpu=$DEFAULT_CPU \
  --timeout=300 \
  --max-instances=$DEFAULT_MAX_INSTANCES \
  --min-instances=$DEFAULT_MIN_INSTANCES \
  --set-env-vars="PYTHONUNBUFFERED=1,PROJECT_ID=$PROJECT_ID,GCS_BUCKET=$BUCKET_NAME" \
  --update-secrets="OPENAI_API_KEY=openai-api-key:latest" \
  --quiet

log_success "デプロイ完了！"

# ============================================
# デプロイ情報の表示
# ============================================

echo ""
echo "======================================"
echo "🎉 デプロイ成功！"
echo "======================================"
echo ""

# サービスURLを取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo "📍 サービスURL:"
echo "   $SERVICE_URL"
echo ""
echo "📚 APIドキュメント:"
echo "   $SERVICE_URL/docs"
echo ""
echo "📊 Cloud Runコンソール:"
echo "   https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
echo ""
echo "📝 ログ:"
echo "   https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
echo ""

if [ -n "$BUCKET_NAME" ]; then
    echo "💾 Cloud Storageバケット:"
    echo "   gs://$BUCKET_NAME"
    echo ""
fi

echo "======================================"
echo ""

log_info "次のステップ:"
echo "  1. $SERVICE_URL にアクセスしてアプリを確認"
echo "  2. $SERVICE_URL/docs でAPIドキュメントを確認"
echo "  3. Cloud Runコンソールでメトリクスを確認"
echo ""

# 完了
log_success "すべての処理が完了しました！"

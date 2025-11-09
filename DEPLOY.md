# ES診断ツール - GCPデプロイガイド

## 概要

このガイドでは、ES診断ツールをGoogle Cloud Platform (GCP) にデプロイする方法を説明します。
**推奨デプロイ先: Cloud Run**（サーバーレス、自動スケーリング、簡単なデプロイ）

## 前提条件

- Google Cloud アカウント
- gcloud CLI がインストールされていること
- プロジェクトが作成されていること
- 必要なAPIが有効化されていること

### 必要なAPIの有効化

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  storage-api.googleapis.com
```

## Cloud Run へのデプロイ（推奨）

### 方法1: 自動デプロイスクリプトを使用

最も簡単な方法です：

```bash
# デプロイスクリプトを実行
./deploy.sh
```

### 方法2: 手動デプロイ

#### ステップ1: Artifact Registry にリポジトリを作成

```bash
# リージョンを設定
export REGION="asia-northeast1"  # 東京リージョン

# Artifact Registry リポジトリを作成
gcloud artifacts repositories create es-diagnosis-tool \
  --repository-format=docker \
  --location=$REGION \
  --description="ES診断ツール Docker イメージ"
```

#### ステップ2: Cloud Build でイメージをビルド

```bash
# イメージをビルド＆プッシュ
gcloud builds submit \
  --tag $REGION-docker.pkg.dev/$PROJECT_ID/es-diagnosis-tool/app:latest
```

または、ローカルでビルドしてプッシュ：

```bash
# Docker認証
gcloud auth configure-docker $REGION-docker.pkg.dev

# ローカルでビルド
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/es-diagnosis-tool/app:latest .

# プッシュ
docker push $REGION-docker.pkg.dev/$PROJECT_ID/es-diagnosis-tool/app:latest
```

#### ステップ3: Cloud Run にデプロイ

```bash
gcloud run deploy es-diagnosis-tool \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/es-diagnosis-tool/app:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8000 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "PYTHONUNBUFFERED=1"
```

デプロイが完了すると、URLが表示されます：
```
https://es-diagnosis-tool-xxxxxxxxxx-an.a.run.app
```

## データの準備

### Cloud Storage に前処理済みデータをアップロード

前処理済みデータをCloud Storageに保存することで、起動時間を短縮できます：

```bash
# バケットを作成
gsutil mb -l $REGION gs://${PROJECT_ID}-es-data

# 前処理済みデータをアップロード
gsutil -m cp -r es_preprocessed_data/* gs://${PROJECT_ID}-es-data/preprocessed/

# CSVファイルもアップロード（オプション）
gsutil cp data/unified_es_data_en.csv gs://${PROJECT_ID}-es-data/raw/
```

### Cloud Storage からデータを読み込む（オプション）

`src/app.py` の `startup_event` を修正してCloud Storageからデータを読み込むようにします：

```python
from google.cloud import storage
import os
import tempfile

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時にCloud Storageからデータを読み込む"""
    print("\n" + "="*60)
    print("🚀 ES診断ツール（FastAPI版）起動中...")
    print("="*60)

    # Cloud Storageから前処理済みデータをダウンロード
    try:
        bucket_name = os.getenv("GCS_BUCKET", f"{os.getenv('PROJECT_ID')}-es-data")
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # 一時ディレクトリにダウンロード
        temp_dir = tempfile.mkdtemp()

        # 前処理済みデータをダウンロード
        blobs = bucket.list_blobs(prefix='preprocessed/')
        for blob in blobs:
            file_path = os.path.join(temp_dir, blob.name.replace('preprocessed/', ''))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            blob.download_to_filename(file_path)

        # ダウンロードしたデータを読み込み
        preprocessed_loaded = load_preprocessed_data(temp_dir)

    except Exception as e:
        print(f"⚠️ Cloud Storageからの読み込みに失敗: {e}")
        # フォールバック処理
        preprocessed_loaded = load_preprocessed_data()

    # 以下、既存のコード...
```

## 環境変数の設定

Cloud Run で環境変数を設定する場合：

```bash
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --set-env-vars "PROJECT_ID=$PROJECT_ID,GCS_BUCKET=${PROJECT_ID}-es-data"
```

## カスタムドメインの設定

### Cloud Run カスタムドメインマッピング

```bash
# ドメインをマッピング
gcloud run domain-mappings create \
  --service es-diagnosis-tool \
  --domain your-domain.com \
  --region $REGION
```

表示されるDNSレコードを、ドメインのDNS設定に追加してください。

## Cloud CDN の設定（オプション）

静的アセットのキャッシュでパフォーマンスを向上：

```bash
# ロードバランサーを作成してCloud CDNを有効化
# （詳細はGCPドキュメントを参照）
```

## セキュリティ設定

### IAM認証の有効化

認証が必要な場合：

```bash
# 認証を必須にする
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --no-allow-unauthenticated

# 特定のユーザーにアクセス権を付与
gcloud run services add-iam-policy-binding es-diagnosis-tool \
  --region $REGION \
  --member="user:email@example.com" \
  --role="roles/run.invoker"
```

### VPC Connector の設定

プライベートネットワークにアクセスする場合：

```bash
# VPC Connector を作成
gcloud compute networks vpc-access connectors create es-connector \
  --region $REGION \
  --network default \
  --range 10.8.0.0/28

# Cloud Run サービスに接続
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --vpc-connector es-connector
```

## モニタリングとロギング

### Cloud Logging

ログは自動的にCloud Loggingに送信されます：

```bash
# ログを表示
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=es-diagnosis-tool" \
  --limit 50 \
  --format json
```

GCPコンソールから確認：
https://console.cloud.google.com/logs

### Cloud Monitoring

メトリクスとアラートの設定：

1. GCPコンソール → Monitoring → Dashboards
2. Cloud Run サービスのダッシュボードを表示
3. アラートポリシーを作成：
   - リクエスト数
   - レスポンスタイム
   - エラー率
   - メモリ使用率

## コスト最適化

### 自動スケーリングの調整

```bash
# 最小インスタンス数を0に設定（リクエストがない時は課金なし）
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --min-instances 0 \
  --max-instances 10

# リクエスト数に応じてスケール
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --concurrency 80
```

### メモリとCPUの最適化

```bash
# リソースを調整
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --memory 2Gi \
  --cpu 1
```

## CI/CD パイプライン

### Cloud Build トリガーの設定

`cloudbuild.yaml` を使用した自動デプロイ：

```bash
# GitHub リポジトリと連携してトリガーを作成
gcloud builds triggers create github \
  --name="deploy-es-tool" \
  --repo-name="es-opt" \
  --repo-owner="your-github-username" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml"
```

## トラブルシューティング

### デプロイが失敗する

```bash
# ビルドログを確認
gcloud builds list --limit 5
gcloud builds log [BUILD_ID]

# サービスログを確認
gcloud logging read "resource.type=cloud_run_revision" --limit 100
```

### メモリ不足エラー

```bash
# メモリを増やす
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --memory 8Gi
```

### タイムアウトエラー

```bash
# タイムアウトを延長
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --timeout 600
```

### コールドスタートが遅い

```bash
# 最小インスタンスを1に設定（常時起動）
gcloud run services update es-diagnosis-tool \
  --region $REGION \
  --min-instances 1
```

## バックアップとリストア

### データのバックアップ

```bash
# Cloud Storageにバックアップ
gsutil -m cp -r es_preprocessed_data/* \
  gs://${PROJECT_ID}-es-data/backups/$(date +%Y%m%d)/
```

### イメージのバックアップ

Artifact Registryに保存された全てのイメージがバックアップとして保持されます。

## ローカルテスト

Cloud Run エミュレータでローカルテスト：

```bash
# Cloud Run エミュレータで起動
gcloud beta code dev

# または Docker で直接起動
docker run -p 8000:8000 \
  $REGION-docker.pkg.dev/$PROJECT_ID/es-diagnosis-tool/app:latest
```

## その他のデプロイオプション

### Google Kubernetes Engine (GKE)

より高度な制御が必要な場合はGKEを使用できます。

### Compute Engine

VM上で直接実行する場合は、通常のDockerデプロイ手順に従ってください。

## サポート

問題が発生した場合：
1. Cloud Loggingでログを確認
2. Cloud Monitoringでメトリクスを確認
3. GCPサポートに問い合わせ

## 参考リンク

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud Build ドキュメント](https://cloud.google.com/build/docs)
- [Artifact Registry ドキュメント](https://cloud.google.com/artifact-registry/docs)
- [Cloud Storage ドキュメント](https://cloud.google.com/storage/docs)

# ES診断ツール - GCPクイックスタート

## 5分でCloud Runにデプロイ！

このガイドでは、最短手順でES診断ツールをGCP Cloud Runにデプロイする方法を説明します。

## 前提条件

- Google Cloud アカウント
- gcloud CLI がインストール済み
- GCPプロジェクトが作成済み

## ステップ1: gcloud CLIの確認

```bash
# gcloud CLIがインストールされているか確認
gcloud version

# ログインしていない場合はログイン
gcloud auth login

# プロジェクトIDを確認
gcloud projects list
```

## ステップ2: プロジェクトの設定

```bash
# プロジェクトIDを設定（your-project-idを実際のIDに置き換え）
export PROJECT_ID="gaxi-tool"
gcloud config set project $PROJECT_ID
```

## ステップ3: 自動デプロイスクリプトの実行

```bash
# リポジトリのルートディレクトリで実行
./deploy.sh
```

対話的に以下を聞かれます：
1. **プロジェクトID**: 確認してEnter
2. **リージョン**: デフォルト（東京: asia-northeast1）でEnter
3. **デプロイ確認**: `y` を入力してEnter
4. **Cloud Storageバケット作成**: `y` を入力（推奨）
5. **前処理済みデータアップロード**: `y` を入力（推奨）

スクリプトが自動的に以下を実行します：
- ✅ 必要なAPIの有効化
- ✅ Artifact Registryリポジトリの作成
- ✅ Dockerイメージのビルド（5-10分）
- ✅ Cloud Runへのデプロイ
- ✅ Cloud Storageバケットの作成

## ステップ4: デプロイ完了

デプロイが完了すると、以下のような情報が表示されます：

```
======================================
🎉 デプロイ成功！
======================================

📍 サービスURL:
   https://es-diagnosis-tool-xxxxxxxxxx-an.a.run.app

📚 APIドキュメント:
   https://es-diagnosis-tool-xxxxxxxxxx-an.a.run.app/docs
```

## ステップ5: 動作確認

ブラウザでサービスURLにアクセスして動作を確認：

```bash
# URLを開く（macOS）
open https://es-diagnosis-tool-xxxxxxxxxx-an.a.run.app

# または curl でテスト
curl https://es-diagnosis-tool-xxxxxxxxxx-an.a.run.app/docs
```

## 完了！

これでES診断ツールがCloud Runで稼働しています 🎉

## 次のステップ

### モニタリング

Cloud Runコンソールでメトリクスを確認：

```bash
# Cloud Runコンソールを開く
open "https://console.cloud.google.com/run?project=$PROJECT_ID"
```

### ログ確認

```bash
# ログを表示
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format json
```

### カスタムドメインの設定

```bash
# カスタムドメインをマッピング
gcloud run domain-mappings create \
  --service es-diagnosis-tool \
  --domain your-domain.com \
  --region asia-northeast1
```

## トラブルシューティング

### デプロイに失敗した場合

```bash
# ビルドログを確認
gcloud builds list --limit 5
gcloud builds log [BUILD_ID]
```

### サービスが起動しない場合

```bash
# サービスログを確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=es-diagnosis-tool" \
  --limit 100
```

### メモリ不足エラー

```bash
# メモリを増やす
gcloud run services update es-diagnosis-tool \
  --region asia-northeast1 \
  --memory 8Gi
```

## コスト管理

### 無料枠

Cloud Runの無料枠：
- 月間200万リクエスト
- 360,000 vCPU秒
- 180,000 GiB秒のメモリ

### コスト最適化

リクエストがない時は課金されないように設定：

```bash
# 最小インスタンス数を0に設定
gcloud run services update es-diagnosis-tool \
  --region asia-northeast1 \
  --min-instances 0
```

## 更新とデプロイ

コードを変更した後、再デプロイする方法：

```bash
# 再度デプロイスクリプトを実行
./deploy.sh

# または手動で
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/$PROJECT_ID/es-diagnosis-tool/app:latest
gcloud run deploy es-diagnosis-tool \
  --image asia-northeast1-docker.pkg.dev/$PROJECT_ID/es-diagnosis-tool/app:latest \
  --region asia-northeast1
```

## サービスの削除

不要になった場合、リソースを削除：

```bash
# Cloud Runサービスを削除
gcloud run services delete es-diagnosis-tool --region asia-northeast1

# Artifact Registryリポジトリを削除
gcloud artifacts repositories delete es-diagnosis-tool --location asia-northeast1

# Cloud Storageバケットを削除
gsutil rm -r gs://${PROJECT_ID}-es-data
```

## サポート

詳細なドキュメント：
- [DEPLOY.md](DEPLOY.md) - 詳細なデプロイガイド
- [README_FASTAPI.md](README_FASTAPI.md) - FastAPI版の説明
- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)

問題が発生した場合は、GitHubのIssuesで報告してください。

# GCP Secret Manager セットアップ手順

このドキュメントでは、GCP Secret ManagerにOpenAI APIキーを安全に保存し、Cloud Runから参照できるようにする手順を説明します。

## 前提条件

- GCPプロジェクトが作成されていること
- `gcloud` CLIがインストールされ、認証されていること
- OpenAI APIキーを取得済みであること

## 手順

### 1. Secret Manager APIを有効化

```bash
gcloud services enable secretmanager.googleapis.com --project=gaxi-tool
```

### 2. OpenAI APIキーをSecret Managerに保存

```bash
# シークレットを作成（初回のみ）
gcloud secrets create openai-api-key \
  --replication-policy="automatic" \
  --project=gaxi-tool

# APIキーの値を追加
echo -n "your_actual_openai_api_key_here" | \
  gcloud secrets versions add openai-api-key \
  --data-file=- \
  --project=gaxi-tool
```

**注意**: `your_actual_openai_api_key_here` を実際のOpenAI APIキーに置き換えてください。

### 3. Cloud Runサービスアカウントに権限を付与

```bash
# プロジェクト番号を取得
PROJECT_NUMBER=$(gcloud projects describe gaxi-tool --format="value(projectNumber)")

# Cloud Runのデフォルトサービスアカウントにシークレットアクセス権限を付与
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gaxi-tool
```

### 4. シークレットが正しく設定されているか確認

```bash
# シークレット一覧を表示
gcloud secrets list --project=gaxi-tool

# シークレットの詳細を確認
gcloud secrets describe openai-api-key --project=gaxi-tool

# シークレットの値を確認（テスト用）
gcloud secrets versions access latest --secret=openai-api-key --project=gaxi-tool
```

### 5. デプロイ

シークレットを設定した後、通常通りデプロイします：

```bash
./deploy.sh
```

または

```bash
gcloud builds submit --config cloudbuild.yaml
```

## トラブルシューティング

### エラー: "Secret Manager API has not been used"

Secret Manager APIが有効化されていません。手順1を実行してください。

### エラー: "Permission denied"

Cloud Runサービスアカウントにシークレットへのアクセス権限がありません。手順3を実行してください。

### エラー: "Secret not found"

シークレットが作成されていません。手順2を実行してください。

## ローカル開発環境のセットアップ

ローカル開発では、`.env`ファイルを使用します：

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集してAPIキーを設定
# OPENAI_API_KEY=your_actual_openai_api_key_here
```

`.env`ファイルは`.gitignore`に含まれているため、Gitにコミットされません。

## セキュリティのベストプラクティス

1. APIキーをソースコードに直接記述しない
2. `.env`ファイルをGitにコミットしない（`.gitignore`に追加済み）
3. 本番環境ではSecret Managerを使用する
4. 定期的にAPIキーをローテーションする
5. 不要になったシークレットバージョンは削除する

## 参考リンク

- [GCP Secret Manager ドキュメント](https://cloud.google.com/secret-manager/docs)
- [Cloud Run でシークレットを使用する](https://cloud.google.com/run/docs/configuring/secrets)
- [OpenAI API Keys](https://platform.openai.com/api-keys)

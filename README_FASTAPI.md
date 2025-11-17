# ES診断ツール - FastAPI版

## 概要

Google Colab上で実行していたFlask版のES診断ツールをFastAPIに移行しました。
ローカル環境で高速に動作し、前処理済みデータを活用することで起動時間を大幅に短縮できます。

**本番環境**: Google Cloud Platform (GCP) Cloud Run 推奨

## 主な変更点

### Flask版からの変更
- **Webフレームワーク**: Flask → FastAPI
- **非同期処理**: 非同期エンドポイントに対応
- **自動ドキュメント**: Swagger UI / ReDocが利用可能
- **型安全性**: Pydanticモデルによるリクエスト/レスポンスの型検証

### 新機能
- **前処理済みデータの活用**: 初回起動後、前処理済みデータを保存して次回以降の起動を高速化
- **環境変数対応**: 設定をコマンドライン引数で指定可能
- **自動リロード**: 開発時のコード変更を自動検知

### 最新機能（2025年11月更新）
- **結果画面での編集・再診断**: 診断結果を見ながら条件を変更して即座に再診断
- **「内定のみに絞る」フィルター**: チェックボックスで内定・内々定のES例のみを表示
- **AI による類似・改善点分析**: OpenAI API（GPT-4o-mini）を使用して、あなたのESと合格ESを比較分析し、具体的な改善提案を生成
- **最新データ対応**: `unified_es_data_20251109.csv`（2025年11月時点の最新ES実績データ）

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. データの準備

以下のいずれかの方法でデータを準備します：

#### 方法A: CSVファイルから読み込む（初回）
```
data/unified_es_data_20251109.csv
```
を配置してください。

#### 方法B: 前処理済みデータを使用する（高速起動）
```
es_preprocessed_data/
├── unified_es_data_es_data.pkl
├── unified_es_data_tfidf_matrix.npz
├── unified_es_data_vectorizer.pkl
└── unified_es_data_embeddings.npy
```

前処理済みデータがある場合、起動時間が **3-5分 → 数秒** に短縮されます。

## 実行方法

### 基本的な起動

```bash
python run.py
```

### オプション付き起動

```bash
# ポート番号を指定
python run.py --port 8080

# 自動リロード有効化（開発時）
python run.py --reload

# すべてのオプション
python run.py --host 0.0.0.0 --port 8080 --reload
```

### 直接実行

```bash
cd src
python app.py
```

または

```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```

## アクセス

起動後、以下のURLにアクセスできます：

- **メインページ**: http://localhost:8000
- **APIドキュメント（Swagger UI）**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## APIエンドポイント

### GET /
フロントエンドUIを返します。

### POST /analyze
ES診断を実行します。

**リクエストボディ**:
```json
{
  "esAnswers": ["回答1", "回答2", "回答3"],
  "targetIndustry": "IT・通信",
  "university": "早稲田大学",
  "targetCompanies": ["会社A", "会社B"],
  "major": "経済学部",
  "graduationYear": "2025"
}
```

**レスポンス**:
```json
{
  "matchCompanies": [...],
  "industryAnalysis": {...},
  "esAnalysis": {...},
  "industrySimilarESSamples": [...],
  "episodeTypeSimilarESSamples": [...],
  "targetCompaniesMatch": [...],
  "dataStatistics": {...},
  "userInfo": {...},
  "episodeTypeInfo": {...}
}
```

## 前処理済みデータの生成

初回起動時にCSVから読み込んだ場合、次回起動を高速化するために前処理済みデータを保存できます。

以下のコードを実行すると、`es_preprocessed_data/`ディレクトリに前処理済みデータが保存されます：

```python
import pickle
import numpy as np
from scipy import sparse
import os

# srcディレクトリから実行
from app import es_data, vectorizer, tfidf_matrix

# 保存先ディレクトリ
preprocessed_dir = '../es_preprocessed_data'
os.makedirs(preprocessed_dir, exist_ok=True)

# es_dataを保存
with open(f'{preprocessed_dir}/unified_es_data_es_data.pkl', 'wb') as f:
    pickle.dump(es_data, f)

# TF-IDF行列を保存
sparse.save_npz(f'{preprocessed_dir}/unified_es_data_tfidf_matrix.npz', tfidf_matrix)

# Vectorizerを保存
with open(f'{preprocessed_dir}/unified_es_data_vectorizer.pkl', 'wb') as f:
    pickle.dump(vectorizer, f)

# セマンティックエンベディングを保存
if 'semantic_embedding' in es_data.columns:
    embeddings_array = np.array(es_data['semantic_embedding'].tolist())
    np.save(f'{preprocessed_dir}/unified_es_data_embeddings.npy', embeddings_array)

print("✅ 前処理済みデータの保存が完了しました")
```

## パフォーマンス

### 起動時間の比較（35,000件のデータ）

| 方法 | 起動時間 |
|------|---------|
| CSVから読み込み（CPU） | 3-5分 |
| CSVから読み込み（GPU T4） | 30秒〜1分 |
| **前処理済みデータ** | **数秒** |

### 前処理済みデータのサイズ（35,000件の場合）

- es_data.pkl: 約50-100 MB
- tfidf_matrix.npz: 約20-50 MB
- vectorizer.pkl: 約5-10 MB
- embeddings.npy: 約50-150 MB
- **合計**: 約125-310 MB

## トラブルシューティング

### データが読み込まれない

```
❌ CSVファイルが見つかりません
```

**対処法**:
1. `data/unified_es_data_20251109.csv`が存在するか確認
2. ファイルパスが正しいか確認
3. 前処理済みデータがあれば、そちらを使用

### メモリエラー

```
MemoryError
```

**対処法**:
1. データ量を減らす
2. より大きなメモリを持つマシンで実行
3. バッチサイズを調整

### sentence-transformersのエラー

```
ImportError: No module named 'sentence_transformers'
```

**対処法**:
```bash
pip install sentence-transformers
```

## 開発

### 開発時の起動

```bash
python run.py --reload
```

コード変更が自動的に検知され、サーバーが再起動します。

### テスト

APIドキュメント（http://localhost:8000/docs）からインタラクティブにテストできます。

## ライセンス

（必要に応じて記載）

## 貢献

（必要に応じて記載）

## GCPへのデプロイ

### クイックデプロイ

最も簡単な方法：

```bash
# デプロイスクリプトを実行
./deploy.sh
```

スクリプトが以下を自動的に実行します：
1. 必要なAPIの有効化
2. Artifact Registryリポジトリの作成
3. Dockerイメージのビルド
4. Cloud Runへのデプロイ
5. Cloud Storageバケットの作成（オプション）

### 手動デプロイ

詳細な手順は [DEPLOY.md](DEPLOY.md) を参照してください。

```bash
# 環境変数を設定
export PROJECT_ID="your-project-id"
export REGION="asia-northeast1"

# 必要なAPIを有効化
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com

# イメージをビルド＆プッシュ
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/es-diagnosis-tool/app:latest

# Cloud Runにデプロイ
gcloud run deploy es-diagnosis-tool \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/es-diagnosis-tool/app:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2
```

### デプロイ後

デプロイが完了すると、以下のURLが発行されます：

```
https://es-diagnosis-tool-xxxxxxxxxx-an.a.run.app
```

- **アプリケーション**: `https://[YOUR-URL]`
- **APIドキュメント**: `https://[YOUR-URL]/docs`
- **ReDoc**: `https://[YOUR-URL]/redoc`

### モニタリング

- **Cloud Run コンソール**: https://console.cloud.google.com/run
- **Cloud Logging**: https://console.cloud.google.com/logs
- **Cloud Monitoring**: メトリクスとアラートの設定

### コスト最適化

```bash
# 最小インスタンス数を0に設定（リクエストがない時は無料）
gcloud run services update es-diagnosis-tool \
  --region asia-northeast1 \
  --min-instances 0
```

## CI/CD

GitHub Actionsまたは Cloud Build トリガーで自動デプロイを設定できます。

詳細は [DEPLOY.md](DEPLOY.md#cicd-パイプライン) を参照してください。

## プロジェクト構成

```
es-opt/
├── src/
│   └── app.py                    # FastAPIアプリケーション
├── templates/
│   └── index.html                # フロントエンドUI
├── data/
│   └── unified_es_data_20251109.csv    # 元データ（最新版）
├── es_preprocessed_data/          # 前処理済みデータ
│   ├── unified_es_data_es_data.pkl
│   ├── unified_es_data_tfidf_matrix.npz
│   ├── unified_es_data_vectorizer.pkl
│   └── unified_es_data_embeddings.npy
├── Dockerfile                     # Cloud Run用Dockerfile
├── docker-compose.yml             # ローカル開発用
├── cloudbuild.yaml                # Cloud Build設定
├── service.yaml                   # Cloud Runサービス定義
├── deploy.sh                      # 自動デプロイスクリプト
├── requirements.txt               # Python依存パッケージ
├── run.py                         # ローカル起動スクリプト
├── README.md                      # プロジェクト概要
├── README_FASTAPI.md              # 本ファイル
└── DEPLOY.md                      # GCPデプロイ詳細ガイド
```

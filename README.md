# ES診断ツール

3.5万件のデータからあなたに最適な企業を分析するES合格診断ツールです。

## 特徴

- ✅ インストール不要（Google Colab対応）
- ✅ HTMLとバックエンドが分離された保守性の高い設計
- ✅ 美しいUIが自動生成
- ✅ ngrokで即座に公開可能
- ✅ 機械学習ベースのマッチング分析

## ディレクトリ構造

```
es/
├── notebooks/
│   └── run_on_colab.ipynb      # Google Colab用起動ノートブック
├── src/
│   └── app.py                  # Flaskバックエンドアプリケーション
├── templates/
│   └── index.html              # フロントエンドHTML
├── data/
│   └── README.md               # データ管理ガイド
├── requirements.txt            # Python依存パッケージ
└── README.md                   # このファイル
```

## 🚀 クイックスタート（Google Colab）

### 方法1: 直接リンクから開く（最も簡単）

```
https://colab.research.google.com/github/ryosuke-fujii/es/blob/main/notebooks/run_on_colab.ipynb
```

### 方法2: 手動でセットアップ

1. **リポジトリをクローン**
```python
!git clone https://github.com/ryosuke-fujii/es.git
%cd es
```

2. **パッケージをインストール**
```python
!pip install -r requirements.txt
```

3. **CSVデータを準備**（3つの選択肢）

#### 選択肢A: Google Driveから読み込む（推奨）
```python
from google.colab import drive
drive.mount('/content/drive')
csv_path = "/content/drive/MyDrive/your-folder/es_data.csv"
```

#### 選択肢B: 直接アップロード
```python
from google.colab import files
uploaded = files.upload()
csv_path = list(uploaded.keys())[0]
```

#### 選択肢C: GitHubのdataディレクトリから
```python
csv_path = "data/sample.csv"
```

4. **アプリケーションを起動**
```python
import sys
sys.path.insert(0, 'src')

from app import app, load_csv_data
from pyngrok import ngrok

# ngrok認証
ngrok.set_auth_token("YOUR_NGROK_TOKEN")

# データ読み込み
load_csv_data(csv_path)

# アプリ起動
import threading
threading.Thread(target=lambda: app.run(port=5000), daemon=True).start()

# 公開URL取得
import time
time.sleep(2)
public_url = ngrok.connect(5000)
print(f"🌐 公開URL: {public_url}")
```

## 📁 プロジェクトの特徴

### 分離されたアーキテクチャ

このプロジェクトは、保守性とAI開発ツールとの親和性を考慮して設計されています：

- **フロントエンド** (`templates/index.html`)
  - 美しいUIデザイン
  - レスポンシブ対応
  - リアルタイム診断結果表示

- **バックエンド** (`src/app.py`)
  - Flask RESTful API
  - TF-IDFベースのテキスト類似度分析
  - 機械学習による企業マッチング

- **起動ノートブック** (`notebooks/run_on_colab.ipynb`)
  - Google Colabで簡単に起動
  - CSVデータ管理の柔軟性
  - ngrok統合

### なぜHTMLとバックエンドを分離？

1. **保守性**: コードの修正が容易
2. **AI開発支援**: Claude Code、Cursor、GitHub Copilotが効率的に動作
3. **再利用性**: 他のプロジェクトでもコンポーネントを再利用可能
4. **テスタビリティ**: フロントエンドとバックエンドを独立してテスト可能

## 💻 ローカル環境での開発

### 必要な環境
- Python 3.7以上
- pip

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/ryosuke-fujii/es.git
cd es

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 実行

```bash
# CSVファイルを data/ ディレクトリに配置

# アプリケーションを起動
python -c "
import sys
sys.path.insert(0, 'src')
from app import app, load_csv_data

# データ読み込み
load_csv_data('data/your_data.csv')

# アプリ起動
app.run(debug=True, port=5000)
"
```

ブラウザで `http://localhost:5000` にアクセス

## 📊 CSVデータの管理

CSVファイルは **Google Drive で管理することを推奨** します。

### 理由
- ✅ 個人情報の保護（GitHubに機密データを含めない）
- ✅ 大きなファイルも扱える
- ✅ Google Colabとの統合が簡単

詳細は [data/README.md](data/README.md) を参照してください。

## 🔧 開発ガイド

### HTMLの編集

`templates/index.html` を編集してUIをカスタマイズ：

```html
<!-- 例: タイトルを変更 -->
<h1>あなたのカスタムタイトル</h1>
```

### バックエンドの編集

`src/app.py` を編集して機能を追加：

```python
# 例: 新しいエンドポイントを追加
@app.route('/api/new-feature', methods=['POST'])
def new_feature():
    # あなたのロジック
    return jsonify({"status": "success"})
```

### AI開発ツールとの連携

このプロジェクトはGitHubで管理されているため、以下のツールと連携できます：

- **Claude Code**: ターミナルで `claude-code` を実行
- **GitHub Copilot**: VSCodeやJetBrainsで自動補完
- **Cursor**: AIペアプログラミング

```bash
# 変更をコミット
git add .
git commit -m "feat: 新機能を追加"
git push
```

## 📖 詳細ドキュメント

- [Google Colab詳細ガイド](COLAB_GUIDE.md)
- [データ管理ガイド](data/README.md)

## 🐛 トラブルシューティング

### ngrokの認証エラー
- https://dashboard.ngrok.com/ でトークンを取得
- Google Colabのシークレット機能を使用して安全に保存

### CSVファイルが見つからない
- ファイルパスを確認
- Google Colabのファイルブラウザで実際のパスを確認

### メモリエラー
- Google Colab Proの使用を検討
- CSVデータをフィルタリングしてサイズを削減

### テンプレートが見つからない
- `src/app.py` が `templates/index.html` を正しく読み込んでいるか確認
- ディレクトリ構造が正しいか確認

## 🤝 貢献

プルリクエストを歓迎します！

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'feat: Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

MIT License

## 🙏 サポート

問題が発生した場合は、GitHubのIssuesで報告してください。

---

**作成者**: Your Name
**リポジトリ**: https://github.com/ryosuke-fujii/es

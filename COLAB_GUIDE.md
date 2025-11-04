# Google Colab 使用ガイド（分離アーキテクチャ版）

このガイドでは、HTMLとバックエンドが分離されたES診断ツールをGoogle Colabで使用する方法を説明します。

## 🎯 分離アーキテクチャの利点

### なぜHTMLとバックエンドを分離？

1. **保守性**: コードが整理され、修正が容易
2. **AI開発支援**: Claude Code、Cursor、GitHub Copilotが効率的に動作
3. **再利用性**: コンポーネントを他のプロジェクトでも使用可能
4. **GitHub管理**: バージョン管理が容易

### ファイル構成

```
es-opt/
├── src/app.py              # Pythonバックエンド（Flask API）
├── templates/index.html    # フロントエンド（UI）
└── notebooks/
    └── run_on_colab.ipynb  # Google Colab起動用
```

## 🚀 クイックスタート

### 方法1: 専用ノートブックを使用（最も簡単）

直接リンクから起動ノートブックを開く：

```
https://colab.research.google.com/github/YOUR_USERNAME/es-opt/blob/main/notebooks/run_on_colab.ipynb
```

セルを順番に実行するだけ！

### 方法2: 手動セットアップ

新しいGoogle Colabノートブックで以下を実行：

#### ステップ1: リポジトリをクローン

```python
!git clone https://github.com/YOUR_USERNAME/es-opt.git
%cd es-opt

print("✅ リポジトリをクローンしました")
!ls -la
```

#### ステップ2: パッケージをインストール

```python
!pip install -r requirements.txt -q

print("✅ パッケージのインストールが完了しました")
```

#### ステップ3: CSVデータを準備

以下の3つの方法から選択：

##### 選択肢A: Google Driveから読み込む（推奨）

```python
from google.colab import drive
import os

# Google Driveをマウント
drive.mount('/content/drive')

# CSVファイルのパスを設定
csv_path = "/content/drive/MyDrive/your-folder/es_data.csv"

# ファイルが存在するか確認
if os.path.exists(csv_path):
    print(f"✅ ファイルを発見: {csv_path}")
else:
    print(f"❌ ファイルが見つかりません: {csv_path}")
```

##### 選択肢B: 直接アップロード

```python
from google.colab import files

# ファイルをアップロード
uploaded = files.upload()

# アップロードされたファイル名を取得
csv_path = list(uploaded.keys())[0]
print(f"✅ ファイルをアップロードしました: {csv_path}")
```

##### 選択肢C: GitHubのdataディレクトリから

```python
import os

csv_path = "data/sample.csv"

if os.path.exists(csv_path):
    print(f"✅ ファイルを発見: {csv_path}")
else:
    print(f"❌ ファイルが見つかりません: {csv_path}")
```

#### ステップ4: アプリケーションを起動

```python
import sys
import os
import threading
import time
from pyngrok import ngrok

# srcディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

# アプリケーションをインポート
from app import app, load_csv_data

# ngrok認証トークンを設定
NGROK_TOKEN = "YOUR_NGROK_TOKEN"  # https://dashboard.ngrok.com/
ngrok.set_auth_token(NGROK_TOKEN)

# CSVデータを読み込み
print("📂 CSVデータを読み込み中...")
load_csv_data(csv_path)
print("✅ データの読み込みが完了しました")

# Flaskアプリをバックグラウンドで起動
def run_flask():
    app.run(port=5000)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

print("🚀 Flaskアプリを起動しました")

# ngrokトンネルを作成
time.sleep(2)
public_url = ngrok.connect(5000)

print("\n" + "="*60)
print("🎉 アプリケーションが起動しました！")
print("="*60)
print(f"\n🌐 公開URL: {public_url}")
print("\n💡 上記のURLをクリックしてアプリにアクセスしてください")
print("="*60)
```

## 📁 プロジェクト構造の説明

### src/app.py（バックエンド）

Flaskアプリケーション本体：

```python
# 主要な関数
- load_csv_data(csv_path): CSVデータを読み込み
- analyze_match(university, gakuchika, industry): マッチング分析
- clean_text(text): テキストクリーニング

# エンドポイント
- GET  /         : フロントエンドUIを表示
- POST /analyze  : ES診断を実行
```

### templates/index.html（フロントエンド）

美しいUIを提供：
- レスポンシブデザイン
- リアルタイム文字数カウント
- アニメーション付き結果表示

### notebooks/run_on_colab.ipynb

Google Colab用の起動ノートブック：
- セットアップを自動化
- CSVデータ読み込みオプション
- ngrok統合

## 🔧 カスタマイズガイド

### フロントエンドのカスタマイズ

`templates/index.html` を編集：

```html
<!-- タイトルを変更 -->
<h1>あなたのカスタムタイトル</h1>

<!-- 色を変更 -->
<style>
    body {
        background: linear-gradient(135deg, #YOUR_COLOR_1 0%, #YOUR_COLOR_2 100%);
    }
</style>
```

Google Colabでの編集：

```python
# ファイルを読み込み
with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 編集
html = html.replace('ES合格診断ツール', 'あなたのタイトル')

# 保存
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ HTMLを更新しました")
```

### バックエンドのカスタマイズ

`src/app.py` を編集：

```python
# 新しいエンドポイントを追加
@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify({
        'total_records': len(es_data),
        'industries': es_data['industry'].unique().tolist()
    })
```

Google Colabでの編集：

```python
# ファイルを読み込み
with open('src/app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 編集（例: デバッグモードを有効化）
code = code.replace('app.run(port=5000)', 'app.run(port=5000, debug=True)')

# 保存
with open('src/app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ バックエンドを更新しました")
```

## 🔄 GitHubへの変更の反映

Google Colab上で編集した内容をGitHubに反映：

```python
# Git設定
!git config --global user.email "your-email@example.com"
!git config --global user.name "Your Name"

# 変更を確認
!git status

# 変更をステージング
!git add src/app.py templates/index.html

# コミット
!git commit -m "feat: Update from Google Colab"

# GitHub Personal Access Tokenを使用してプッシュ
# https://github.com/settings/tokens でトークンを生成
TOKEN = "YOUR_GITHUB_TOKEN"
!git remote set-url origin https://{TOKEN}@github.com/YOUR_USERNAME/es-opt.git
!git push
```

## 💡 ベストプラクティス

### 1. Google Driveでデータを管理

```python
# データパスをデフォルト設定
DEFAULT_CSV = "/content/drive/MyDrive/es-tool/data.csv"

import os
from google.colab import drive

if not os.path.exists('/content/drive'):
    drive.mount('/content/drive')

csv_path = DEFAULT_CSV if os.path.exists(DEFAULT_CSV) else "data/sample.csv"
print(f"📂 使用するCSVファイル: {csv_path}")
```

### 2. ngrokトークンをシークレットに保存

Google Colabのシークレット機能を使用：

1. 左側のメニュー → 🔑 シークレット
2. 新しいシークレットを追加：
   - 名前: `NGROK_AUTH_TOKEN`
   - 値: あなたのngrokトークン

```python
from google.colab import userdata

ngrok_token = userdata.get('NGROK_AUTH_TOKEN')
ngrok.set_auth_token(ngrok_token)
```

### 3. 自動再起動対応

セッションが切れた場合の自動再起動：

```python
import os

# 設定を保存
config = {
    'csv_path': csv_path,
    'ngrok_token': 'YOUR_TOKEN'
}

import json
with open('config.json', 'w') as f:
    json.dump(config, f)

# 次回起動時に読み込み
if os.path.exists('config.json'):
    with open('config.json', 'r') as f:
        config = json.load(f)
    csv_path = config['csv_path']
    print(f"✅ 設定を読み込みました: {csv_path}")
```

## 🐛 トラブルシューティング

### エラー: templates/index.html が見つからない

```python
# ディレクトリ構造を確認
!pwd
!ls -la templates/

# templatesディレクトリが存在するか確認
import os
print(f"templates exists: {os.path.exists('templates')}")
print(f"index.html exists: {os.path.exists('templates/index.html')}")
```

### エラー: src/app.py のインポートエラー

```python
# Pythonパスを確認
import sys
print("Python path:", sys.path)

# srcディレクトリを追加
sys.path.insert(0, '/content/es-opt/src')

# 再度インポート
from app import app, load_csv_data
```

### メモリエラー

```python
# データをフィルタリングして削減
import pandas as pd

df = pd.read_csv(csv_path)
print(f"元のサイズ: {len(df)} 件")

# 最近のデータのみ使用
df = df.tail(10000)
print(f"フィルタ後: {len(df)} 件")

# 一時ファイルとして保存
df.to_csv('temp_data.csv', index=False)
csv_path = 'temp_data.csv'
```

## 📊 データ分析例

Google Colabでデータ分析も可能：

```python
import pandas as pd
import matplotlib.pyplot as plt

# データを読み込み
df = pd.read_csv(csv_path)

# 業界別の集計
industry_counts = df['業界'].value_counts()

# グラフ表示
plt.figure(figsize=(10, 6))
industry_counts.head(10).plot(kind='bar')
plt.title('業界別ES数 TOP10')
plt.xlabel('業界')
plt.ylabel('件数')
plt.tight_layout()
plt.show()
```

## 🎓 次のステップ

1. **機能拡張**: 新しい診断ロジックを追加
2. **UI改善**: templates/index.htmlをカスタマイズ
3. **データ分析**: Pandas/Matplotlibで深掘り分析
4. **API連携**: 外部APIと連携して機能強化

## 📚 参考リンク

- [Flask ドキュメント](https://flask.palletsprojects.com/)
- [ngrok ドキュメント](https://ngrok.com/docs)
- [Google Colab ガイド](https://colab.research.google.com/)
- [pandas チートシート](https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf)

## 🙏 サポート

問題が発生した場合：
1. [GitHub Issues](https://github.com/YOUR_USERNAME/es-opt/issues)
2. [README.md](README.md) のトラブルシューティングセクション

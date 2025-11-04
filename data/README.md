# データディレクトリ

このディレクトリには、ES診断ツールで使用するCSVファイルを配置します。

## CSVファイルの配置方法

### 方法1: GitHub上に配置する場合

1. CSVファイルをこのディレクトリに配置
   ```
   data/
   └── es_data.csv
   ```

2. Google Colabで以下のようにファイルを読み込む
   ```python
   # GitHubリポジトリをクローン
   !git clone https://github.com/your-username/es-opt.git

   # CSVファイルのパス
   csv_path = "es-opt/data/es_data.csv"
   ```

### 方法2: Google Driveを使用する場合

1. Google DriveにCSVファイルをアップロード
2. Google Colabでドライブをマウント
   ```python
   from google.colab import drive
   drive.mount('/content/drive')

   # CSVファイルのパス
   csv_path = "/content/drive/MyDrive/your-folder/es_data.csv"
   ```

### 方法3: 直接アップロードする場合

Google Colabのファイルアップロード機能を使用
```python
from google.colab import files
uploaded = files.upload()
csv_path = list(uploaded.keys())[0]
```

## CSVファイルの形式

CSVファイルには以下のカラムが必要です：
- 大学名
- ガクチカ（学生時代に力を入れたこと）
- 志望業界
- 企業名
- その他の関連データ

## 注意事項

- 大きなCSVファイル（100MB以上）をGitHubに配置する場合は、Git LFSの使用を検討してください
- 個人情報を含むデータは`.gitignore`に追加して、GitHubにアップロードしないよう注意してください
- サンプルデータのみをGitHubに配置し、本番データはGoogle Driveで管理することを推奨します

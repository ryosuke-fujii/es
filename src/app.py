# ============================================
# セル3: ES診断アプリケーション（Flask統合版）
# ============================================
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, request, jsonify, render_template, Response
import json
import re
import threading
import time
import os

# グローバル変数
es_data = None
vectorizer = None
tfidf_matrix = None
sentence_model = None  # Sentence-BERTモデル

# 選択肢用データ
universities_list = []
industries_list = []
companies_list = []
common_questions = []
company_counts = {}
industry_counts = {}

# 業界の大分類リスト
INDUSTRY_MAJOR_CATEGORIES = [
    'IT・通信',
    'インフラ・物流・エネルギー',
    'コンサル・シンクタンク',
    'サービス',
    'メーカー・製造業',
    '不動産',
    '商社・卸',
    '小売り',
    '広告・マスコミ',
    '金融'
]

# ESテーマカテゴリ体系（実データ分析に基づく）
ES_THEME_CATEGORIES = {
    # 活動フィールド
    '研究・学術活動': [
        '研究', 'ゼミ', '論文', '学会', '実験', '調査', '分析', '考察'
    ],
    'ビジネス経験': [
        'インターン', 'アルバイト', '長期インターン', '実務経験', '職務経験', '営業', '接客'
    ],
    '課外活動': [
        'サークル', '部活', '学生団体', 'ボランティア', '課外', 'スポーツ'
    ],
    # アクション・スキル
    '課題解決・改善': [
        '課題', '問題', '解決', '改善', '克服', '対策', '施策', '打開'
    ],
    'リーダーシップ・組織運営': [
        'リーダー', '代表', 'マネジメント', '統率', '組織', '運営', '主導'
    ],
    'チームワーク・協働': [
        'チーム', 'メンバー', '協力', '連携', '協働', 'グループ', '共同'
    ],
    '企画・提案': [
        '企画', '提案', 'アイデア', '立案', '新規', '発案', 'プラン'
    ],
    '技術開発・創造': [
        '開発', 'プログラミング', 'システム', '設計', '実装', '制作', '構築'
    ],
    # マインド・姿勢
    '挑戦・目標達成': [
        '挑戦', '目標', '達成', 'チャレンジ', '新しい', '初めて', '未経験'
    ],
    '困難克服・逆境': [
        '困難', '失敗', '乗り越え', '苦労', '壁', '逆境', 'トラブル', '危機'
    ],
    '成長・学習': [
        '成長', '学び', '習得', '経験', '気づき', '獲得', '身につけた'
    ],
    # 成果・インパクト
    '定量的成果': [
        '売上', '増加', '削減', '向上', '%', '倍', '人', '件', '円', '達成率'
    ],
    '社会貢献・影響力': [
        '社会', '貢献', '支援', '地域', '影響', '価値', 'インパクト'
    ],
    # 志望動機・キャリア
    '企業理解・共感': [
        '理念', 'ビジョン', '事業', '強み', '魅力', '特徴', '姿勢', '取り組み'
    ],
    'キャリアビジョン': [
        '将来', 'キャリア', '実現したい', '成し遂げたい', '目指す', '夢'
    ]
}

# エピソードタイプ分類（拡張版）
EPISODE_TYPES = {
    # ビジネス・実務経験
    'アルバイト・接客': {
        'keywords': [
            'アルバイト', 'バイト', 'バイト先', 'アルバイト先',
            '接客', '販売', '店舗', 'レストラン', 'カフェ', '飲食店',
            'コンビニ', 'スーパー', '小売', 'ホール', 'レジ'
        ],
        'weight': 1.0
    },
    'インターン・実務': {
        'keywords': [
            'インターン', 'インターンシップ', '長期インターン',
            '実務', '実務経験', '職務経験', 'ビジネス経験',
            'インターン先', 'インターン生'
        ],
        'weight': 1.0
    },
    '起業・事業立ち上げ': {
        'keywords': [
            '起業', '創業', '事業', 'ビジネス',
            '会社設立', '法人', '代表', '経営',
            'スタートアップ', 'ベンチャー', '自営',
            'サービス立ち上げ', '事業化', '商品開発'
        ],
        'weight': 1.0
    },

    # 学術・研究活動
    '研究・ゼミ活動': {
        'keywords': [
            '研究', 'ゼミ', 'ゼミナール', '実験',
            '論文', '学会', '卒論', '修論',
            '研究室', 'ラボ', '調査', '分析',
            '考察', '仮説', 'データ', '検証'
        ],
        'weight': 1.0
    },
    '資格取得・受験': {
        'keywords': [
            '資格', '検定', '試験', '合格',
            '勉強', '受験', '学習', 'TOEIC',
            'TOEFL', '簿記', '宅建', '公認会計士',
            'FP', 'ソムリエ', '国家試験'
        ],
        'weight': 0.8
    },

    # 課外活動
    '部活動・体育会': {
        'keywords': [
            '部活', '部活動', '体育会', '運動部',
            '練習', 'トレーニング', '大会', '試合',
            '選手', 'キャプテン', '主将', 'レギュラー',
            '全国大会', '地区大会', '県大会'
        ],
        'weight': 1.0
    },
    'サークル活動': {
        'keywords': [
            'サークル', 'サークル活動', '同好会',
            '文化系', '趣味', '愛好会',
            'サークル代表', 'サークル長'
        ],
        'weight': 1.0
    },
    '学生団体・NPO': {
        'keywords': [
            '学生団体', '団体', 'NPO', 'NGO',
            'ボランティア', '社会貢献', '支援活動',
            '地域活動', 'コミュニティ', '市民活動',
            '学生組織', '代表', '運営'
        ],
        'weight': 1.0
    },

    # 国際・語学経験
    '留学・海外経験': {
        'keywords': [
            '留学', '海外', '海外経験', '海外留学',
            '交換留学', '語学留学', '短期留学', '長期留学',
            '海外インターン', 'ホームステイ', '海外ボランティア',
            '現地', '異文化', '外国', '渡航'
        ],
        'weight': 1.0
    },

    # イベント・コンテスト
    'コンテスト・大会': {
        'keywords': [
            'コンテスト', 'コンペ', 'コンペティション',
            '大会', '競技会', 'ハッカソン',
            'ビジネスコンテスト', 'プレゼン大会',
            '入賞', '優勝', '受賞', '表彰'
        ],
        'weight': 1.0
    },

    # 個人プロジェクト
    '個人プロジェクト・趣味': {
        'keywords': [
            '個人', '趣味', 'プロジェクト', '制作',
            'ポートフォリオ', 'アプリ開発', 'Web制作',
            'ブログ', 'SNS', 'YouTube', '動画',
            '作品', 'ハンドメイド', 'DIY'
        ],
        'weight': 0.8
    },

    # 教育関連
    '家庭教師・塾講師': {
        'keywords': [
            '家庭教師', '塾', '塾講師', '講師',
            '指導', '教育', '生徒', '教える',
            '授業', '添削', '進路指導'
        ],
        'weight': 1.0
    },

    # その他
    'その他の経験': {
        'keywords': [],
        'weight': 0.5
    }
}

# Flaskアプリケーションの初期化
# templatesフォルダを親ディレクトリから読み込む
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(os.path.dirname(base_dir), 'templates')
app = Flask(__name__, template_folder=template_dir)

# ============================================
# データ処理関数
# ============================================

def clean_text(text):
    """テキストのクリーニング"""
    if pd.isna(text):
        return ""
    text = re.sub(r'\n+', ' ', str(text))
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'続きを読む.*', '', text)
    text = re.sub(r'問題を報告する.*', '', text)
    return text.strip()

def remove_prefix(text):
    """プレフィックスを削除"""
    if pd.isna(text):
        return ""
    return re.sub(r'^[^：]+：\s*', '', str(text))

def extract_university(user_info):
    """ユーザー情報から大学名を抽出"""
    if pd.isna(user_info):
        return "不明"
    match = re.search(r'\d{2}卒\s*\|\s*([^|]+)\s*\|', str(user_info))
    if match:
        return match.group(1).strip()
    return "不明"

def extract_major_industry_category(industry):
    """業界名から大分類を抽出"""
    if pd.isna(industry) or not industry:
        return None

    industry_str = str(industry).strip()

    # 大分類リストから一致するものを探す
    for major_category in INDUSTRY_MAJOR_CATEGORIES:
        if industry_str.startswith(major_category):
            return major_category

    return None

def categorize_es_themes(text):
    """ESのテーマをマルチラベルで判定"""
    if pd.isna(text) or not text:
        return []

    text_str = str(text)
    matched_themes = []

    for theme_name, keywords in ES_THEME_CATEGORIES.items():
        # キーワードマッチング
        keyword_count = sum(1 for kw in keywords if kw in text_str)

        # 閾値を超えたらテーマとして認定（2個以上）
        if keyword_count >= 2:
            matched_themes.append({
                'theme': theme_name,
                'score': keyword_count
            })

    # スコアでソート
    matched_themes.sort(key=lambda x: x['score'], reverse=True)

    return matched_themes if matched_themes else [{'theme': 'その他', 'score': 0}]

def extract_theme_keywords_for_weighting(text):
    """重要キーワードに重み付けしたテキストを生成"""
    if pd.isna(text) or not text:
        return str(text)

    text_str = str(text)
    weighted_text = text_str

    # テーマ別に重要キーワードを抽出して重み付け
    for theme_name, keywords in ES_THEME_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_str:
                # キーワードを3回繰り返して重要度を上げる
                weighted_text += f" {keyword} {keyword} {keyword}"

    return weighted_text

def analyze_es_structure(text):
    """ESの構造を分析してスコアリング（STARフレームワーク）"""
    if pd.isna(text) or not text:
        return {
            'situation': 0,
            'task': 0,
            'action': 0,
            'result': 0,
            'learning': 0
        }

    text_str = str(text)

    structure_features = {
        'situation': 0,  # 状況説明
        'task': 0,       # 課題・目標
        'action': 0,     # 具体的行動
        'result': 0,     # 成果・結果
        'learning': 0    # 学び
    }

    # 状況説明の検出
    situation_keywords = ['において', 'で', 'に所属', 'に参加', '当時', 'では', 'として']
    structure_features['situation'] = sum(1 for kw in situation_keywords if kw in text_str)

    # 課題・目標の検出
    task_keywords = ['目標', '課題', 'したい', 'を目指', '改善', '向上', '問題', '必要']
    structure_features['task'] = sum(1 for kw in task_keywords if kw in text_str)

    # 具体的行動の検出
    action_keywords = ['私は', '取り組んだ', '実施', '工夫', '提案', '導入', '行った', '考えた']
    structure_features['action'] = sum(1 for kw in action_keywords if kw in text_str)

    # 成果の検出
    result_keywords = ['結果', '達成', '向上', '%', '増加', '成功', '実現', '完成']
    structure_features['result'] = sum(1 for kw in result_keywords if kw in text_str)

    # 学びの検出
    learning_keywords = ['学んだ', '得た', '身につけた', '気づいた', '経験から', '理解した', '成長']
    structure_features['learning'] = sum(1 for kw in learning_keywords if kw in text_str)

    return structure_features

def classify_episode_type(text):
    """
    ESテキストからエピソードタイプを判定

    Args:
        text (str): ES本文

    Returns:
        dict: {
            'type': エピソードタイプ名,
            'confidence': 信頼度（マッチしたキーワード数）,
            'matched_keywords': マッチしたキーワードリスト
        }
    """
    if pd.isna(text) or not text:
        return {
            'type': 'その他の経験',
            'confidence': 0,
            'matched_keywords': []
        }

    text_str = str(text)

    # 各エピソードタイプでマッチング
    episode_scores = []

    for episode_type, config in EPISODE_TYPES.items():
        keywords = config['keywords']
        weight = config['weight']

        # マッチしたキーワードをカウント
        matched_keywords = [kw for kw in keywords if kw in text_str]
        match_count = len(matched_keywords)

        if match_count > 0:
            # スコア = マッチ数 × 重み
            score = match_count * weight
            episode_scores.append({
                'type': episode_type,
                'score': score,
                'confidence': match_count,
                'matched_keywords': matched_keywords[:5]  # 最大5個まで
            })

    # スコアが最も高いものを返す
    if episode_scores:
        best_match = max(episode_scores, key=lambda x: x['score'])
        return {
            'type': best_match['type'],
            'confidence': best_match['confidence'],
            'matched_keywords': best_match['matched_keywords']
        }

    # マッチしない場合
    return {
        'type': 'その他の経験',
        'confidence': 0,
        'matched_keywords': []
    }

def classify_multiple_episode_types(text, top_n=2):
    """
    複数のエピソードタイプを返す（マルチラベル対応）

    Args:
        text (str): ES本文
        top_n (int): 返すエピソードタイプの最大数

    Returns:
        list: エピソードタイプのリスト
    """
    if pd.isna(text) or not text:
        return [{'type': 'その他の経験', 'confidence': 0}]

    text_str = str(text)

    episode_scores = []

    for episode_type, config in EPISODE_TYPES.items():
        keywords = config['keywords']
        weight = config['weight']

        matched_keywords = [kw for kw in keywords if kw in text_str]
        match_count = len(matched_keywords)

        if match_count > 0:
            score = match_count * weight
            episode_scores.append({
                'type': episode_type,
                'score': score,
                'confidence': match_count
            })

    # スコア順にソート
    episode_scores.sort(key=lambda x: x['score'], reverse=True)

    # 上位top_nを返す
    if episode_scores:
        return episode_scores[:top_n]

    return [{'type': 'その他の経験', 'confidence': 0}]

def load_csv_data(csv_path):
    """CSVデータを読み込んで整形"""
    global es_data, vectorizer, tfidf_matrix, sentence_model

    print(f"\n📂 CSVデータを読み込み中: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ {len(df)}件のデータを読み込みました")

    print("🔧 データ整形中...")

    es_data = pd.DataFrame({
        'company_name': df['p-company-summary__name'].apply(clean_text),
        'industry': df['p-company-summary__stage-sub'].apply(remove_prefix),
        'title': df['p-company-heading-contents__title'].apply(clean_text),
        'user_info': df.get('c-panel-variant2__header-user', pd.Series()).apply(clean_text),
        'question_1': df['u-font-light'].apply(clean_text),
        'answer_1': df['c-show-more__content'].apply(clean_text),
        'question_2': df.get('u-font-light (2)', pd.Series()).apply(clean_text),
        'answer_2': df.get('c-show-more__content (2)', pd.Series()).apply(clean_text),
        'question_3': df.get('u-font-light (3)', pd.Series()).apply(clean_text),
        'answer_3': df.get('c-show-more__content (3)', pd.Series()).apply(clean_text),
        'avg_salary': df.get('p-company-table (11)', pd.Series()).apply(clean_text),
        'employee_count': df.get('p-company-summary__stage-sub (3)', pd.Series()).apply(remove_prefix),
    })

    es_data['university'] = es_data['user_info'].apply(extract_university)

    es_data['result_status'] = es_data['title'].apply(
        lambda x: '内定' if '内定' in str(x) else ('通過' if '通過' in str(x) else '不明')
    )

    es_data = es_data[es_data['result_status'].isin(['通過', '内定'])]

    es_data['combined_answer'] = (
        es_data['answer_1'].fillna('') + ' ' +
        es_data['answer_2'].fillna('') + ' ' +
        es_data['answer_3'].fillna('')
    ).str.strip()

    es_data = es_data[es_data['combined_answer'].str.len() > 50]

    print(f"✅ 有効なESデータ: {len(es_data)}件")

    # テーマカテゴリ分析を追加
    print("🔧 ESのテーマ分析中...")
    es_data['themes'] = es_data['combined_answer'].apply(categorize_es_themes)

    # エピソードタイプ分析を追加
    print("🔧 エピソードタイプ分析中...")
    es_data['episode_type'] = es_data['combined_answer'].apply(classify_episode_type)
    es_data['episode_types_multi'] = es_data['combined_answer'].apply(
        lambda x: classify_multiple_episode_types(x, top_n=2)
    )

    # エピソードタイプの統計を出力
    episode_type_counts = {}
    for episode_info in es_data['episode_type']:
        episode_type = episode_info['type']
        episode_type_counts[episode_type] = episode_type_counts.get(episode_type, 0) + 1

    print("\n📊 エピソードタイプ別の分布:")
    for episode_type, count in sorted(episode_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {episode_type}: {count}件")

    # 重要キーワードの重み付けテキストを生成
    print("\n🔧 キーワード重み付け中...")
    es_data['weighted_answer'] = es_data['combined_answer'].apply(extract_theme_keywords_for_weighting)

    print("🔧 TF-IDFベクトル化中（最適化済みパラメータ）...")
    vectorizer = TfidfVectorizer(
        max_features=3000,  # 1000 → 3000に増加
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 3)  # (1,2) → (1,3)に拡張
    )

    # 重み付けされたテキストを使用してベクトル化
    tfidf_matrix = vectorizer.fit_transform(es_data['weighted_answer'])
    print(f"✅ ベクトル化完了: {tfidf_matrix.shape}")

    # ============================================
    # セマンティックエンベディング生成（Sentence-BERT）
    # ============================================
    print("🔧 セマンティックエンベディング生成中...")
    try:
        from sentence_transformers import SentenceTransformer
        import time

        # tqdmのインポート（進捗表示用）
        try:
            from tqdm import tqdm
            has_tqdm = True
        except ImportError:
            print("  ⚠️ tqdmがインストールされていません。進捗表示なしで実行します。")
            has_tqdm = False

        # 1. モデルのロード
        if sentence_model is None:
            print("  📥 セマンティックモデルをダウンロード中...")
            # 軽量モデルを使用（384次元、約2倍速い）
            sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

            # GPU対応（利用可能な場合）
            try:
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
                print(f"  🖥️  使用デバイス: {device}")
                sentence_model = sentence_model.to(device)
            except ImportError:
                print("  🖥️  使用デバイス: cpu")

            print("  ✅ モデルロード完了")

        # 2. まず100件でテスト（所要時間の予測）
        print("\n  🧪 テスト: 最初の100件を処理して所要時間を予測...")
        test_start = time.time()
        test_count = min(100, len(es_data))
        test_texts = es_data['weighted_answer'].head(test_count).apply(lambda x: str(x)[:512]).tolist()
        test_embeddings = sentence_model.encode(
            test_texts,
            convert_to_tensor=False,
            show_progress_bar=False,
            batch_size=32
        )
        test_time = time.time() - test_start

        estimated_total_time = (test_time / test_count) * len(es_data)
        print(f"  ⏱️  {test_count}件の処理時間: {test_time:.2f}秒")
        print(f"  📊 予想所要時間: {estimated_total_time / 60:.1f}分")

        # 3. 全データをバッチ処理
        print(f"\n  🚀 全データのエンベディング生成中（{len(es_data)}件）...")

        # テキストを一括で準備（長さ制限を512文字に）
        all_texts = es_data['weighted_answer'].apply(lambda x: str(x)[:512]).tolist()

        # バッチサイズの設定
        batch_size = 32  # CPUの場合は16-32が最適
        all_embeddings = []

        # バッチ処理ループ
        batch_range = range(0, len(all_texts), batch_size)
        if has_tqdm:
            batch_range = tqdm(batch_range, desc="  エンベディング生成")

        for i in batch_range:
            batch_texts = all_texts[i:i+batch_size]

            # バッチで一気にエンコード
            batch_embeddings = sentence_model.encode(
                batch_texts,
                convert_to_tensor=False,
                show_progress_bar=False,
                batch_size=batch_size
            )

            # リストに追加
            if isinstance(batch_embeddings, list):
                all_embeddings.extend(batch_embeddings)
            else:
                # numpyアレイの場合
                all_embeddings.extend(batch_embeddings.tolist() if hasattr(batch_embeddings, 'tolist') else list(batch_embeddings))

        # 4. DataFrameに格納
        es_data['semantic_embedding'] = all_embeddings

        # 5. 結果確認
        print(f"\n  ✅ セマンティックエンベディング完了（{len(all_embeddings)}件）")
        if len(all_embeddings) > 0:
            first_embedding = all_embeddings[0]
            if hasattr(first_embedding, '__len__'):
                print(f"  📏 エンベディング次元: {len(first_embedding)}")

    except ImportError:
        print("⚠️ sentence-transformersがインストールされていません。")
        print("   pip install sentence-transformers でインストールしてください。")
        print("   TF-IDFのみを使用します。")
        es_data['semantic_embedding'] = None

    except Exception as e:
        print(f"⚠️ セマンティックエンベディング生成エラー: {e}")
        import traceback
        traceback.print_exc()
        es_data['semantic_embedding'] = None

    print("\n📊 データ統計:")
    print(f"  - ユニーク企業数: {es_data['company_name'].nunique()}")
    print(f"  - 業界数: {es_data['industry'].nunique()}")
    print(f"  - 通過ES: {(es_data['result_status'] == '通過').sum()}件")
    print(f"  - 内定ES: {(es_data['result_status'] == '内定').sum()}件")

    # 選択肢を抽出
    global universities_list, industries_list, companies_list, common_questions
    global company_counts, industry_counts

    print("\n📋 選択肢を抽出中...")

    universities_list = sorted(es_data['university'].dropna().unique().tolist())
    universities_list = [u for u in universities_list if u != "不明" and str(u).strip() != ""]

    industries_list = sorted(es_data['industry'].dropna().unique().tolist())
    industries_list = [i for i in industries_list if i and str(i).strip() != ""]

    # 企業リストの処理を改善（前株企業も含める）
    companies_list = es_data['company_name'].dropna().unique().tolist()
    # 空文字や空白のみの企業名を除外（ただし、前株企業は保持）
    companies_list = [c for c in companies_list if c and str(c).strip() != "" and len(str(c).strip()) > 1]
    # ソート（日本語対応）
    companies_list = sorted(companies_list, key=lambda x: str(x))

    # 企業ごとのデータ件数をカウント
    company_counts = es_data['company_name'].value_counts().to_dict()

    # 業界ごとのデータ件数をカウント
    industry_counts = es_data['industry'].value_counts().to_dict()

    common_questions = [
        "学生時代に力を入れたこと（ガクチカ）",
        "志望動機",
        "自己PR",
        "あなたの強みとエピソード",
        "挑戦したこと・チャレンジ",
        "困難を乗り越えた経験",
        "チームで成果を出した経験",
        "リーダーシップを発揮した経験",
        "インターンで学びたいこと",
        "将来のキャリアビジョン"
    ]

    print(f"✅ 選択肢の抽出が完了しました")
    print(f"  - 大学: {len(universities_list)}校")
    print(f"  - 業界: {len(industries_list)}種類")
    print(f"  - 企業: {len(companies_list)}社")

def calculate_similarity(input_text, top_n=100):
    """類似度計算（ハイブリッド：TF-IDF + セマンティック + 構造分析）"""
    # 入力テキストにも同じ重み付けを適用
    weighted_input = extract_theme_keywords_for_weighting(input_text)

    # TF-IDF類似度
    input_vector = vectorizer.transform([weighted_input])
    tfidf_similarities = cosine_similarity(input_vector, tfidf_matrix)[0]

    # セマンティック類似度（BERT）
    semantic_similarities = np.zeros(len(es_data))
    has_semantic = False

    try:
        from sentence_transformers import SentenceTransformer

        if sentence_model is not None and es_data['semantic_embedding'].iloc[0] is not None:
            # 入力テキストのエンベディング生成
            input_embedding = sentence_model.encode(str(input_text)[:512], convert_to_tensor=False)

            # 全ESとの類似度計算
            embeddings_matrix = np.vstack(es_data['semantic_embedding'].values)
            semantic_similarities = cosine_similarity([input_embedding], embeddings_matrix)[0]
            has_semantic = True
    except Exception as e:
        print(f"⚠️ セマンティック類似度計算をスキップ: {e}")

    # ハイブリッドスコア（セマンティックが使える場合は重視）
    if has_semantic:
        combined_similarities = (
            tfidf_similarities * 0.3 +      # キーワードマッチ
            semantic_similarities * 0.7     # 意味マッチ
        )
    else:
        combined_similarities = tfidf_similarities

    # 構造分析による追加スコアリング
    input_structure = analyze_es_structure(input_text)

    result = es_data.copy()
    result['similarity_score'] = combined_similarities

    # 上位候補に対して構造類似度を計算
    result = result.sort_values('similarity_score', ascending=False).head(top_n * 2)

    # 構造類似度を追加
    structure_scores = []
    for idx, row in result.iterrows():
        es_structure = analyze_es_structure(row['combined_answer'])

        # 構造の一致度を計算
        structure_similarity = sum(
            min(input_structure[key], es_structure[key])
            for key in input_structure.keys()
        ) / max(sum(input_structure.values()), 1)

        structure_scores.append(structure_similarity)

    result['structure_score'] = structure_scores

    # 最終スコア = 内容類似度 * 0.8 + 構造類似度 * 0.2
    result['similarity_score'] = (
        result['similarity_score'] * 0.8 +
        result['structure_score'] * 0.2
    )

    # テーマフィルタリング強化
    # 入力ESのテーマを抽出
    input_themes = categorize_es_themes(input_text)
    input_theme_names = set([t['theme'] for t in input_themes[:3]])  # 上位3テーマ

    # テーマボーナスを追加
    for idx, row in result.iterrows():
        es_themes = row['themes']
        es_theme_names = set([t['theme'] for t in es_themes[:3]])

        # テーマの一致数を計算
        theme_overlap = len(input_theme_names & es_theme_names)

        # ボーナススコア（0〜0.15）
        # 3つ一致 → +15%、2つ一致 → +10%、1つ一致 → +5%
        theme_bonus = theme_overlap * 0.05

        # スコアを更新（乗算）
        result.at[idx, 'similarity_score'] = (
            row['similarity_score'] * (1 + theme_bonus)
        )

    # 最終的にtop_nに絞る
    result = result.sort_values('similarity_score', ascending=False).head(top_n)

    return result

def extract_salary_numeric(salary_str):
    """給与から数値を抽出"""
    if pd.isna(salary_str):
        return None
    match = re.search(r'(\d+)万', str(salary_str))
    if match:
        return int(match.group(1)) * 10000
    return None

def estimate_company_difficulty(row):
    """企業難易度を推定"""
    difficulty = 0.5

    avg_salary = extract_salary_numeric(row.get('avg_salary'))
    if avg_salary:
        if avg_salary >= 8000000:
            difficulty += 0.3
        elif avg_salary >= 6000000:
            difficulty += 0.2
        elif avg_salary >= 5000000:
            difficulty += 0.1

    employee_str = str(row.get('employee_count', ''))
    if '1万人以上' in employee_str:
        difficulty += 0.2

    return min(difficulty, 1.0)

def calculate_match_score(similarity_score, company_difficulty, industry_match, university_match=0.5):
    """マッチスコア計算"""
    score = (
        similarity_score * 0.5 +
        (1 - company_difficulty) * 0.2 +
        industry_match * 0.2 +
        university_match * 0.1
    )
    return min(int(score * 100), 100)

def get_top_companies(similar_es, user_industry, user_university="", top_n=5):
    """TOP企業を選出"""
    companies = []
    seen_companies = set()

    # まず十分な数の企業を処理（top_nの3倍または最低20社）
    process_count = max(top_n * 3, 20)

    for _, row in similar_es.iterrows():
        company_name = row['company_name']

        if company_name in seen_companies:
            continue
        seen_companies.add(company_name)

        difficulty = estimate_company_difficulty(row)
        industry_match = 1.0 if user_industry in row['industry'] else 0.5
        university_match = 1.0 if user_university and user_university == row.get('university') else 0.5

        match_score = calculate_match_score(
            row['similarity_score'],
            difficulty,
            industry_match,
            university_match
        )

        reasons = []
        if row['similarity_score'] > 0.3:
            reasons.append('ESの内容が類似')
        if industry_match == 1.0:
            reasons.append('志望業界と一致')
        if university_match == 1.0:
            reasons.append('同じ大学からの採用実績')
        if difficulty < 0.6:
            reasons.append('比較的通過しやすい')

        reason = '、'.join(reasons) if reasons else 'データマッチング'

        salary = extract_salary_numeric(row['avg_salary'])
        if salary and salary >= 7000000:
            avg_gpa = "3.2-3.8"
        elif salary and salary >= 6000000:
            avg_gpa = "3.0-3.6"
        else:
            avg_gpa = "2.8-3.4"

        companies.append({
            'name': company_name,
            'industry': row['industry'],
            'matchScore': match_score,
            'reason': reason,
            'avgGpa': avg_gpa,
            'avgSalary': row.get('avg_salary', '不明'),
            'employeeCount': row.get('employee_count', '不明'),
        })

        # 十分な数の企業を処理したら終了
        if len(companies) >= process_count:
            break

    # matchScoreで降順ソートしてtop_nを返す
    companies.sort(key=lambda x: x['matchScore'], reverse=True)
    return companies[:top_n]

def calculate_target_company_match(company_name, similar_es, user_industry, user_university="", rank=1):
    """特定の志望企業とのマッチ率を計算（志望順位に応じて調整）"""
    # 企業データを検索
    company_data = es_data[es_data['company_name'] == company_name]

    if len(company_data) == 0:
        # データがない場合は、類似ESの平均スコアを使用
        if len(similar_es) > 0:
            avg_score = similar_es['similarity_score'].mean()
            base_score = min(int(avg_score * 70), 100)  # 控えめなスコア

            # 志望順位による調整
            rank_adjustment = 1.0 if rank == 1 else (0.95 if rank == 2 else 0.9)
            adjusted_score = int(base_score * rank_adjustment)

            return {
                'name': company_name,
                'industry': '不明',
                'matchScore': adjusted_score,
                'reason': 'データ不足のため推定値です',
                'dataCount': 0
            }
        return None

    # 企業の代表的なデータを取得
    representative = company_data.iloc[0]

    # 類似度を計算（その企業のESとの平均類似度）
    company_similarities = similar_es[similar_es['company_name'] == company_name]

    if len(company_similarities) > 0:
        avg_similarity = company_similarities['similarity_score'].mean()
    else:
        avg_similarity = similar_es['similarity_score'].mean() * 0.7  # 控えめに推定

    difficulty = estimate_company_difficulty(representative)
    industry_match = 1.0 if user_industry in str(representative['industry']) else 0.5
    university_match = 1.0 if user_university and user_university == representative.get('university') else 0.5

    base_match_score = calculate_match_score(
        avg_similarity,
        difficulty,
        industry_match,
        university_match
    )

    # 志望順位による調整（第一志望=100%、第二志望=95%、第三志望=90%）
    rank_adjustment = 1.0 if rank == 1 else (0.95 if rank == 2 else 0.9)
    match_score = int(base_match_score * rank_adjustment)

    reasons = []
    if avg_similarity > 0.3:
        reasons.append('ESの内容が類似')
    if industry_match == 1.0:
        reasons.append('志望業界と一致')
    if university_match == 1.0:
        reasons.append('同じ大学からの採用実績')
    if len(company_data) >= 10:
        reasons.append(f'{len(company_data)}件の合格ES実績あり')
    elif len(company_data) >= 5:
        reasons.append(f'{len(company_data)}件のES実績あり')

    reason = '、'.join(reasons) if reasons else 'データマッチング'

    return {
        'name': company_name,
        'industry': str(representative['industry']) if not pd.isna(representative['industry']) else '不明',
        'matchScore': match_score,
        'reason': reason,
        'dataCount': len(company_data)
    }

def analyze_industry(industry):
    """業界分析"""
    industry_data = es_data[es_data['industry'].str.contains(industry, na=False)]

    if len(industry_data) == 0:
        return {
            'passRate': 70,
            'avgApplicants': 150,
            'competition': '中',
            'recommendations': ['業界研究を深める', '企業の特徴を理解する']
        }

    pass_rate = 75
    avg_applicants = len(industry_data) * 3

    if avg_applicants > 200:
        competition = '非常に高'
    elif avg_applicants > 150:
        competition = '高'
    elif avg_applicants > 100:
        competition = '中'
    else:
        competition = '低'

    recommendations_map = {
        'IT': ['技術スキルの証明', 'ポートフォリオの作成', '最新技術のキャッチアップ'],
        'コンサルティング': ['ケース面接対策', '論理的思考力の強化', 'フェルミ推定の練習'],
        '金融': ['金融知識の習得', '数字に強いエピソード', '誠実さのアピール'],
        'メーカー': ['技術力の証明', '長期的なキャリアビジョン', 'ものづくりへの情熱']
    }

    recommendations = recommendations_map.get(
        industry,
        ['業界研究を深める', '企業の特徴を理解する', '自己分析を徹底する']
    )

    return {
        'passRate': pass_rate,
        'avgApplicants': avg_applicants,
        'competition': competition,
        'recommendations': recommendations
    }

def analyze_gakuchika(gakuchika_text):
    """ガクチカ分析"""
    strengths = []
    improvements = []

    if any(word in gakuchika_text for word in ['数値', '結果', '成果', '%', '人']):
        strengths.append('具体的な数値・成果の記載')

    if any(word in gakuchika_text for word in ['課題', '問題', '解決', '改善']):
        strengths.append('課題解決のプロセスが明確')

    if len(gakuchika_text) >= 300:
        strengths.append('十分な分量で説明されている')

    if not any(word in gakuchika_text for word in ['チーム', '協力', '連携', 'メンバー']):
        improvements.append('チームワークの要素を追加')

    if not any(word in gakuchika_text for word in ['学んだ', '得た', '成長']):
        improvements.append('学びや成長の要素を強調')

    if len(gakuchika_text) < 200:
        improvements.append('もう少し詳しく記述する')

    return {
        'strengths': strengths if strengths else ['基本的な構成は良好'],
        'improvements': improvements if improvements else ['現状で良い内容です']
    }

def analyze_es_answers(answers):
    """ES分析（複数回答対応）"""
    all_text = ' '.join([a for a in answers if a])

    strengths = []
    improvements = []

    if any(word in all_text for word in ['数値', '結果', '成果', '%', '人', '件', '倍']):
        strengths.append('具体的な数値・成果の記載')
    if any(word in all_text for word in ['課題', '問題', '解決', '改善', '克服']):
        strengths.append('課題解決のプロセスが明確')
    if any(word in all_text for word in ['チーム', '協力', '連携', 'メンバー', '組織']):
        strengths.append('チームワークの要素がある')
    if len(all_text) >= 500:
        strengths.append('十分な分量で説明されている')

    if not any(word in all_text for word in ['学んだ', '得た', '成長', '経験']):
        improvements.append('学びや成長の要素を強調')
    if not any(word in all_text for word in ['具体的', '例えば', '実際に']):
        improvements.append('より具体的なエピソードを追加')
    if len(all_text) < 300:
        improvements.append('もう少し詳しく記述する')

    return {
        'strengths': strengths if strengths else ['基本的な構成は良好'],
        'improvements': improvements if improvements else ['現状で良い内容です']
    }

def get_industry_similar_es_samples(similar_es, target_industry, top_n=3):
    """志望業界内の類似度の高いESのサンプルを取得

    まず小分類（完全一致）で検索し、見つからない場合は大分類で検索する
    """
    # 1. まず小分類（完全一致）で検索
    industry_es = similar_es[similar_es['industry'].str.contains(target_industry, na=False)]
    exact_match = True
    matched_category = target_industry

    # 2. 小分類で見つからない場合、大分類で検索
    if len(industry_es) == 0:
        major_category = extract_major_industry_category(target_industry)
        if major_category:
            # 大分類で始まる業界をすべて検索
            industry_es = similar_es[similar_es['industry'].str.startswith(major_category, na=False)]
            exact_match = False
            matched_category = major_category

        # それでも見つからない場合は空のリストを返す
        if len(industry_es) == 0:
            return {'samples': [], 'exactMatch': False, 'matchedCategory': None}

    samples = []

    for idx, row in industry_es.head(top_n).iterrows():
        user_info = str(row.get('user_info', ''))

        # 卒業年度を抽出
        grad_year_match = re.search(r'(\d{2})卒', user_info)
        grad_year = grad_year_match.group(1) + '卒' if grad_year_match else '不明'

        university = row.get('university', '不明')

        # 学部・学科を抽出
        major_match = re.search(r'\|\s*([^|]+)\s*\|', user_info)
        major = major_match.group(1).strip() if major_match else '不明'

        es_content = []
        for i in range(1, 4):
            question = row.get(f'question_{i}', '')
            answer = row.get(f'answer_{i}', '')

            if question and answer and str(question).strip() and str(answer).strip():
                es_content.append({
                    'question': str(question).strip(),
                    'answer': str(answer).strip()[:500] + ('...' if len(str(answer)) > 500 else '')
                })

        if len(es_content) > 0:
            sample = {
                'company': str(row['company_name']),
                'industry': str(row['industry']) if not pd.isna(row['industry']) else '不明',
                'result': str(row['result_status']),
                'similarity': round(float(row['similarity_score']) * 100, 1),
                'profile': {
                    'university': university,
                    'major': major,
                    'gradYear': grad_year
                },
                'esContent': es_content
            }
            samples.append(sample)

    return {
        'samples': samples,
        'exactMatch': exact_match,
        'matchedCategory': matched_category
    }

def get_similar_es_samples(similar_es, top_n=3):
    """類似ESのサンプルを取得"""
    samples = []

    for idx, row in similar_es.head(top_n).iterrows():
        user_info = str(row.get('user_info', ''))

        # 卒業年度を抽出
        grad_year_match = re.search(r'(\d{2})卒', user_info)
        grad_year = grad_year_match.group(1) + '卒' if grad_year_match else '不明'

        university = row.get('university', '不明')

        # 学部・学科を抽出
        major_match = re.search(r'\|\s*([^|]+)\s*\|', user_info)
        major = major_match.group(1).strip() if major_match else '不明'

        es_content = []
        for i in range(1, 4):
            question = row.get(f'question_{i}', '')
            answer = row.get(f'answer_{i}', '')

            if question and answer and str(question).strip() and str(answer).strip():
                es_content.append({
                    'question': str(question).strip(),
                    'answer': str(answer).strip()[:500] + ('...' if len(str(answer)) > 500 else '')
                })

        if len(es_content) > 0:
            sample = {
                'company': str(row['company_name']),
                'industry': str(row['industry']) if not pd.isna(row['industry']) else '不明',
                'result': str(row['result_status']),
                'similarity': round(float(row['similarity_score']) * 100, 1),
                'profile': {
                    'university': university,
                    'major': major,
                    'gradYear': grad_year
                },
                'esContent': es_content
            }
            samples.append(sample)

    return samples

def get_es_samples_by_company(similar_es, company_name, top_n=3):
    """
    指定した企業の類似ESサンプルを取得

    Args:
        similar_es: 類似度計算済みのES DataFrame
        company_name: 企業名
        top_n: 返すサンプル数

    Returns:
        list: ESサンプルのリスト
    """
    # この企業のESを類似度順で取得
    company_es = similar_es[similar_es['company_name'] == company_name]

    if len(company_es) == 0:
        return []

    samples = []

    for idx, row in company_es.head(top_n).iterrows():
        user_info = str(row.get('user_info', ''))

        # 卒業年度を抽出
        grad_year_match = re.search(r'(\d{2})卒', user_info)
        grad_year = grad_year_match.group(1) + '卒' if grad_year_match else '不明'

        university = row.get('university', '不明')

        # 学部・学科を抽出
        major_match = re.search(r'\|\s*([^|]+)\s*\|', user_info)
        major = major_match.group(1).strip() if major_match else '不明'

        es_content = []
        for i in range(1, 4):
            question = row.get(f'question_{i}', '')
            answer = row.get(f'answer_{i}', '')

            if question and answer and str(question).strip() and str(answer).strip():
                es_content.append({
                    'question': str(question).strip(),
                    'answer': str(answer).strip()[:500] + ('...' if len(str(answer)) > 500 else '')
                })

        if len(es_content) > 0:
            sample = {
                'company': str(row['company_name']),
                'industry': str(row['industry']) if not pd.isna(row['industry']) else '不明',
                'result': str(row['result_status']),
                'similarity': round(float(row['similarity_score']) * 100, 1),
                'profile': {
                    'university': university,
                    'major': major,
                    'gradYear': grad_year
                },
                'esContent': es_content
            }
            samples.append(sample)

    return samples

def get_similar_es_samples_from_top_companies(similar_es, top_companies):
    """
    TOP企業リストに基づいて類似ESのサンプルを取得（順序を維持）
    ※この関数は後方互換性のために残していますが、非推奨です

    Args:
        similar_es: 類似度計算済みのES DataFrame
        top_companies: get_top_companies()から返された企業リスト

    Returns:
        list: TOP企業と同じ順序・同じ企業のESサンプル
    """
    samples = []

    for company_info in top_companies:
        company_name = company_info['name']
        company_samples = get_es_samples_by_company(similar_es, company_name, top_n=1)

        if len(company_samples) > 0:
            # matchScoreを追加
            company_samples[0]['matchScore'] = company_info['matchScore']
            samples.append(company_samples[0])

    return samples


def get_episode_type_similar_es_samples(similar_es, input_text, top_n=3):
    """
    同じエピソードタイプの類似ESのサンプルを取得

    Args:
        similar_es: 類似度計算済みのES DataFrame
        input_text: ユーザー入力のES本文
        top_n: 返すサンプル数

    Returns:
        dict: {
            'episodeType': エピソードタイプ名,
            'episodeTypeJa': エピソードタイプの日本語名,
            'confidence': 信頼度,
            'samples': [類似ESのリスト],
            'totalCount': 同じエピソードタイプのES総数
        }
    """
    # 入力ESのエピソードタイプを判定
    input_episode_info = classify_episode_type(input_text)
    input_episode_type = input_episode_info['type']
    input_confidence = input_episode_info['confidence']

    print(f"  🎯 入力ESのエピソードタイプ: {input_episode_type} (信頼度: {input_confidence})")

    # 同じエピソードタイプのESをフィルタリング
    same_episode_es = similar_es[
        similar_es['episode_type'].apply(lambda x: x['type'] == input_episode_type)
    ]

    # 件数が少ない場合は、マルチラベルでも検索
    if len(same_episode_es) < top_n:
        print(f"  ⚠️ 同一エピソードタイプのESが{len(same_episode_es)}件のみ。マルチラベルで追加検索...")

        # マルチラベルで同じエピソードタイプを含むESを追加
        multi_episode_es = similar_es[
            similar_es['episode_types_multi'].apply(
                lambda types: any(t['type'] == input_episode_type for t in types)
            )
        ]

        # 重複を除外して結合
        same_episode_es = pd.concat([same_episode_es, multi_episode_es]).drop_duplicates()

    total_count = len(same_episode_es)

    if total_count == 0:
        return {
            'episodeType': input_episode_type,
            'episodeTypeJa': input_episode_type,
            'confidence': input_confidence,
            'samples': [],
            'totalCount': 0,
            'message': f'「{input_episode_type}」カテゴリのESが見つかりませんでした'
        }

    # 上位top_nのサンプルを取得
    samples = []

    for idx, row in same_episode_es.head(top_n).iterrows():
        user_info = str(row.get('user_info', ''))

        # 卒業年度を抽出
        grad_year_match = re.search(r'(\d{2})卒', user_info)
        grad_year = grad_year_match.group(1) + '卒' if grad_year_match else '不明'

        university = row.get('university', '不明')

        # 学部・学科を抽出
        major_match = re.search(r'\|\s*([^|]+)\s*\|', user_info)
        major = major_match.group(1).strip() if major_match else '不明'

        es_content = []
        for i in range(1, 4):
            question = row.get(f'question_{i}', '')
            answer = row.get(f'answer_{i}', '')

            if question and answer and str(question).strip() and str(answer).strip():
                es_content.append({
                    'question': str(question).strip(),
                    'answer': str(answer).strip()[:500] + ('...' if len(str(answer)) > 500 else '')
                })

        if len(es_content) > 0:
            # エピソード情報を取得
            episode_info = row['episode_type']

            sample = {
                'company': str(row['company_name']),
                'industry': str(row['industry']) if not pd.isna(row['industry']) else '不明',
                'result': str(row['result_status']),
                'similarity': round(float(row['similarity_score']) * 100, 1),
                'episodeType': episode_info['type'],
                'episodeConfidence': episode_info['confidence'],
                'profile': {
                    'university': university,
                    'major': major,
                    'gradYear': grad_year
                },
                'esContent': es_content
            }
            samples.append(sample)

    return {
        'episodeType': input_episode_type,
        'episodeTypeJa': input_episode_type,  # 日本語名（既に日本語）
        'confidence': input_confidence,
        'samples': samples,
        'totalCount': total_count,
        'message': f'同じ「{input_episode_type}」カテゴリから{len(samples)}件のESを抽出しました'
    }

# ============================================
# HTMLテンプレート（美しいUI）
# ============================================

# HTMLテンプレートは templates/index.html から読み込み

# ============================================
# Flaskルート
# ============================================

@app.route('/')
def home():
    """フロントエンドUI - データを埋め込んだHTMLを返す"""
    print("\n🌐 ページ生成中...")

    # 企業と業界のマッピングを作成
    company_industries = {}
    for company in companies_list[:300]:
        company_data = es_data[es_data['company_name'] == company]
        if len(company_data) > 0:
            # 最も多い業界を取得
            industry = company_data['industry'].mode()[0] if len(company_data['industry'].mode()) > 0 else '不明'
            company_industries[company] = industry

    # 選択肢データを準備
    embedded_data = {
        'universities': universities_list[:200],  # 最初の200校
        'industries': industries_list,
        'companies': companies_list[:300],  # 最初の300社
        'commonQuestions': common_questions,
        'companyCounts': {k: v for k, v in company_counts.items() if k in companies_list[:300]},
        'industryCounts': industry_counts,
        'companyIndustries': company_industries  # 企業と業界のマッピング
    }

    # JSONシリアライズ（ensure_ascii=Trueで安全に）
    embedded_data_json = json.dumps(embedded_data, ensure_ascii=True)

    # HTMLテンプレートを読み込み
    template_path = os.path.join(template_dir, 'index.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # <script type="application/json">で埋め込み
    embedded_script = f"""
    <script id="embedded-data" type="application/json">
{embedded_data_json}
    </script>
    """

    # HTMLの</head>直前に挿入
    html_content = html_content.replace('</head>', embedded_script + '\n</head>')

    print(f"  ✅ データ埋め込み完了: 大学{len(embedded_data['universities'])}校, 業界{len(embedded_data['industries'])}種類")

    return Response(html_content, mimetype='text/html')

@app.route('/analyze', methods=['POST'])
def analyze_es():
    """ES診断API - 複数ES質問対応"""
    try:
        data = request.get_json()

        # 複数のES回答に対応
        if not data.get('esAnswers') or len(data.get('esAnswers', [])) == 0:
            return jsonify({'error': 'ES回答を入力してください'}), 400

        has_long_answer = any(len(ans) >= 100 for ans in data['esAnswers'])
        if not has_long_answer:
            return jsonify({'error': '少なくとも1つの回答は100文字以上入力してください'}), 400

        if not data.get('targetIndustry'):
            return jsonify({'error': '志望業界を選択してください'}), 400

        # 全ての回答を結合して類似度計算
        combined_answers = ' '.join(data['esAnswers'])
        similar_es = calculate_similarity(combined_answers, top_n=100)

        top_companies = get_top_companies(
            similar_es,
            data['targetIndustry'],
            data.get('university', ''),
            top_n=5
        )

        # 各TOP企業にESサンプルを追加（アコーディオン用）
        for company in top_companies:
            company['esSamples'] = get_es_samples_by_company(
                similar_es,
                company['name'],
                top_n=3  # 各企業から3件のESを取得
            )

        industry_analysis = analyze_industry(data['targetIndustry'])
        es_analysis = analyze_es_answers(data['esAnswers'])
        industry_similar_es_samples = get_industry_similar_es_samples(similar_es, data['targetIndustry'], top_n=3)

        # 入力ESのエピソードタイプを判定
        input_episode_info = classify_episode_type(combined_answers)
        input_episode_types_multi = classify_multiple_episode_types(combined_answers, top_n=2)

        # エピソードタイプ別の類似ES
        episode_type_similar_es_samples = get_episode_type_similar_es_samples(
            similar_es,
            combined_answers,
            top_n=3
        )

        # 志望企業のマッチ率を計算（第三志望まで）
        target_companies_match = []
        if data.get('targetCompanies') and len(data['targetCompanies']) > 0:
            for i, target_company in enumerate(data['targetCompanies'], 1):
                if target_company and target_company.strip():
                    match_result = calculate_target_company_match(
                        target_company,
                        similar_es,
                        data['targetIndustry'],
                        data.get('university', ''),
                        rank=i  # 志望順位を渡す
                    )
                    if match_result:
                        # 志望順位を追加
                        match_result['rank'] = i
                        # ESサンプルを追加（アコーディオン用）
                        match_result['esSamples'] = get_es_samples_by_company(
                            similar_es,
                            target_company,
                            top_n=3  # 各企業から3件のESを取得
                        )
                        target_companies_match.append(match_result)

        # 統計情報を計算
        total_es_count = len(es_data)
        matched_es_count = len(similar_es)
        industry_es_count = len(es_data[es_data['industry'].str.contains(data['targetIndustry'], na=False)])

        # 志望企業のデータ数をカウント
        target_companies_data_count = {}
        if data.get('targetCompanies') and len(data['targetCompanies']) > 0:
            for target_company in data['targetCompanies']:
                if target_company and target_company.strip():
                    count = len(es_data[es_data['company_name'] == target_company])
                    target_companies_data_count[target_company] = count

        # 第三志望までのマッチ率の平均を計算
        avg_match_rate = 0
        if len(target_companies_match) > 0:
            avg_match_rate = sum(item['matchScore'] for item in target_companies_match) / len(target_companies_match)

        response = {
            'matchCompanies': top_companies,  # 各企業にesSamplesフィールド追加済み（アコーディオン用）
            'industryAnalysis': industry_analysis,
            'esAnalysis': es_analysis,
            'industrySimilarESSamples': industry_similar_es_samples,  # 業界内の類似ES
            'episodeTypeSimilarESSamples': episode_type_similar_es_samples,  # エピソードタイプ別の類似ES
            'targetCompaniesMatch': target_companies_match,  # 各企業にesSamplesフィールド追加済み（アコーディオン用）
            'dataStatistics': {
                'totalEsCount': total_es_count,
                'matchedEsCount': matched_es_count,
                'industryEsCount': industry_es_count,
                'targetCompaniesDataCount': target_companies_data_count,
                'avgMatchRate': round(avg_match_rate, 1)
            },
            'userInfo': {
                'university': data.get('university'),
                'major': data.get('major'),
                'graduationYear': data.get('graduationYear')
            },
            'episodeTypeInfo': {  # エピソードタイプ情報
                'primary': input_episode_info,
                'all': input_episode_types_multi
            }
        }

        return jsonify(response)

    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

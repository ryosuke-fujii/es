# ============================================
# セル3: ES診断アプリケーション（Flask統合版）
# ============================================
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, request, jsonify, render_template
import re
import threading
import time
import os

# グローバル変数
es_data = None
vectorizer = None
tfidf_matrix = None

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

def load_csv_data(csv_path):
    """CSVデータを読み込んで整形"""
    global es_data, vectorizer, tfidf_matrix

    print(f"\n📂 CSVデータを読み込み中: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ {len(df)}件のデータを読み込みました")

    print("🔧 データ整形中...")

    es_data = pd.DataFrame({
        'company_name': df['p-company-summary__name'].apply(clean_text),
        'industry': df['p-company-summary__stage-sub'].apply(remove_prefix),
        'title': df['p-company-heading-contents__title'].apply(clean_text),
        'question_1': df['u-font-light'].apply(clean_text),
        'answer_1': df['c-show-more__content'].apply(clean_text),
        'question_2': df.get('u-font-light (2)', pd.Series()).apply(clean_text),
        'answer_2': df.get('c-show-more__content (2)', pd.Series()).apply(clean_text),
        'question_3': df.get('u-font-light (3)', pd.Series()).apply(clean_text),
        'answer_3': df.get('c-show-more__content (3)', pd.Series()).apply(clean_text),
        'avg_salary': df.get('p-company-table (11)', pd.Series()).apply(clean_text),
        'employee_count': df.get('p-company-summary__stage-sub (3)', pd.Series()).apply(remove_prefix),
    })

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

    print("🔧 TF-IDFベクトル化中...")
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 2)
    )

    tfidf_matrix = vectorizer.fit_transform(es_data['combined_answer'])
    print(f"✅ ベクトル化完了: {tfidf_matrix.shape}")

    print("\n📊 データ統計:")
    print(f"  - ユニーク企業数: {es_data['company_name'].nunique()}")
    print(f"  - 業界数: {es_data['industry'].nunique()}")
    print(f"  - 通過ES: {(es_data['result_status'] == '通過').sum()}件")
    print(f"  - 内定ES: {(es_data['result_status'] == '内定').sum()}件")

def calculate_similarity(input_text, top_n=100):
    """類似度計算"""
    input_vector = vectorizer.transform([input_text])
    similarities = cosine_similarity(input_vector, tfidf_matrix)[0]

    result = es_data.copy()
    result['similarity_score'] = similarities
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

def calculate_match_score(similarity_score, company_difficulty, industry_match):
    """マッチスコア計算"""
    score = (
        similarity_score * 0.6 +
        (1 - company_difficulty) * 0.2 +
        industry_match * 0.2
    )
    return min(int(score * 100), 100)

def get_top_companies(similar_es, user_industry, top_n=5):
    """TOP企業を選出"""
    companies = []
    seen_companies = set()

    for _, row in similar_es.iterrows():
        company_name = row['company_name']

        if company_name in seen_companies:
            continue
        seen_companies.add(company_name)

        difficulty = estimate_company_difficulty(row)
        industry_match = 1.0 if user_industry in row['industry'] else 0.5

        match_score = calculate_match_score(
            row['similarity_score'],
            difficulty,
            industry_match
        )

        reasons = []
        if row['similarity_score'] > 0.3:
            reasons.append('ESの内容が類似')
        if industry_match == 1.0:
            reasons.append('志望業界と一致')
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

        if len(companies) >= top_n:
            break

    return companies

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

# ============================================
# HTMLテンプレート（美しいUI）
# ============================================

# HTMLテンプレートは templates/index.html から読み込み

# ============================================
# Flaskルート
# ============================================

@app.route('/')
def home():
    """フロントエンドUI"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_es():
    """ES診断API"""
    try:
        data = request.get_json()

        if not data.get('gakuchika') or len(data.get('gakuchika', '')) < 100:
            return jsonify({'error': 'ガクチカは100文字以上入力してください'}), 400

        if not data.get('targetIndustry'):
            return jsonify({'error': '志望業界を選択してください'}), 400

        similar_es = calculate_similarity(data['gakuchika'], top_n=100)
        top_companies = get_top_companies(similar_es, data['targetIndustry'], top_n=5)
        industry_analysis = analyze_industry(data['targetIndustry'])
        gakuchika_analysis = analyze_gakuchika(data['gakuchika'])

        response = {
            'matchCompanies': top_companies,
            'industryAnalysis': industry_analysis,
            'gakuchikaAnalysis': gakuchika_analysis,
            'targetCompany': data.get('targetCompany'),
            'userInfo': {
                'university': data.get('university'),
                'major': data.get('major'),
                'gpa': data.get('gpa')
            }
        }

        return jsonify(response)

    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

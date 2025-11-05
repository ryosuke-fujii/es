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

# 選択肢用データ
universities_list = []
industries_list = []
companies_list = []
common_questions = []
company_counts = {}
industry_counts = {}

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

    # 選択肢を抽出
    global universities_list, industries_list, companies_list, common_questions
    global company_counts, industry_counts

    print("\n📋 選択肢を抽出中...")

    universities_list = sorted(es_data['university'].dropna().unique().tolist())
    universities_list = [u for u in universities_list if u != "不明" and str(u).strip() != ""]

    industries_list = sorted(es_data['industry'].dropna().unique().tolist())
    industries_list = [i for i in industries_list if i and str(i).strip() != ""]

    companies_list = sorted(es_data['company_name'].dropna().unique().tolist())
    companies_list = [c for c in companies_list if c and str(c).strip() != ""]

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

        if len(companies) >= top_n:
            break

    return companies

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

    # 選択肢データを準備
    embedded_data = {
        'universities': universities_list[:200],  # 最初の200校
        'industries': industries_list,
        'companies': companies_list[:300],  # 最初の300社
        'commonQuestions': common_questions,
        'companyCounts': {k: v for k, v in company_counts.items() if k in companies_list[:300]},
        'industryCounts': industry_counts
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

        industry_analysis = analyze_industry(data['targetIndustry'])
        es_analysis = analyze_es_answers(data['esAnswers'])
        similar_es_samples = get_similar_es_samples(similar_es, top_n=3)

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
            'matchCompanies': top_companies,
            'industryAnalysis': industry_analysis,
            'esAnalysis': es_analysis,
            'similarESSamples': similar_es_samples,
            'targetCompaniesMatch': target_companies_match,  # 第三志望までのマッチ率
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
            }
        }

        return jsonify(response)

    except Exception as e:
        print(f"❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

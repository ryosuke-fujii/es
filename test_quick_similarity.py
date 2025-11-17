#!/usr/bin/env python3
"""
軽量版類似度テスト（エンベディングなし、TF-IDFのみ）
"""
import sys
import os
sys.path.insert(0, 'src')

os.environ.setdefault('OPENAI_API_KEY', 'dummy-key-for-testing')

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 必要な関数だけインポート
from app import (
    extract_strengths_and_weaknesses,
    categorize_es_themes,
    classify_episode_type,
    extract_quantitative_achievement_score,
    calculate_detail_score,
    EPISODE_TYPES
)

print("=" * 80)
print("軽量版類似度テスト")
print("=" * 80)

# テストデータを作成（実際のESデータの代わり）
test_es_samples = [
    {
        'id': 1,
        'company': 'テスト企業A',
        'question': '長所',
        'combined_answer': '''
私の強みは、有言実行する行動力です。私は、口にしたことは絶対に成し遂げることを心掛けて達成します。
大学時代に「留学する」と言って、アメリカに留学した経験があります。現地での生活を通じて、
異文化理解を深め、英語力も向上させました。
        '''.strip()
    },
    {
        'id': 2,
        'company': 'テスト企業B',
        'question': '長所',
        'combined_answer': '''
私の強みは人にわかりやすく説明できることです。私は大学入学後、塾講師として活動しています。
生徒や保護者との経験を活かして、成績向上を目標に活動を行っています。
授業を行う中で、理解してもらいやすい言葉選びや正確に伝わっていることを確かめながら話を進めることを工夫しました。
        '''.strip()
    },
    {
        'id': 3,
        'company': 'テスト企業C',
        'question': '長所',
        'combined_answer': '''
私の強みは行動力です。思い立ったらすぐに行動に移すことができます。
大学時代に「起業する」と決めて、実際に学生ベンチャーを立ち上げました。
周りの協力を得ながら、半年で売上100万円を達成することができました。
        '''.strip()
    },
    {
        'id': 4,
        'company': 'テスト企業D',
        'question': '長所',
        'combined_answer': '''
私の強みはコミュニケーション力です。相手の立場に立って考え、適切な言葉で伝えることができます。
インターンシップでの営業活動を通じて、顧客との信頼関係を構築しました。
結果として、3ヶ月で新規顧客を10社獲得することができました。
        '''.strip()
    }
]

# DataFrame化
es_data = pd.DataFrame(test_es_samples)

# 各ESに対して分析を実行
print("\n📊 各ESの分析結果:")
print("=" * 80)

# 新しいカラムを追加
sw_list = []
episode_list = []
themes_list = []

for idx, row in es_data.iterrows():
    sw = extract_strengths_and_weaknesses(row['combined_answer'])
    episode = classify_episode_type(row['combined_answer'])
    themes = categorize_es_themes(row['combined_answer'])

    sw_list.append(sw)
    episode_list.append(episode)
    themes_list.append(themes)

    print(f"\nES#{row['id']} ({row['company']})")
    print(f"  強み: {sw['strengths']}")
    print(f"  弱み: {sw['weaknesses']}")
    print(f"  エピソード: {episode['type']}")
    print(f"  テーマ: {[t['theme'] for t in themes[:2]]}")

# DataFrameに追加
es_data['strengths_weaknesses'] = sw_list
es_data['episode_type'] = episode_list
es_data['themes'] = themes_list

# 入力テスト
input_text = """
私の強みは、有言実行する行動力です。私は、口にしたことは絶対に成し遂げることを心掛けて達成します。
大学時代に「アメリカに行く」と言って一人でアメリカに行った経験があります。
一方の弱みは、行動力がありすぎるあまり一人で突っ走ってしまうことがあるところです。
自分が決めたことを成し遂げようとして周りを気にせず一人で次々と進んでしまい周りの仲間を置いていくという失敗をしたことがあります。
"""

print("\n" + "=" * 80)
print("入力ESの分析")
print("=" * 80)
print(input_text.strip())

input_sw = extract_strengths_and_weaknesses(input_text)
input_episode = classify_episode_type(input_text)
input_themes = categorize_es_themes(input_text)

print(f"\n入力ESの特徴:")
print(f"  強み: {input_sw['strengths']}")
print(f"  弱み: {input_sw['weaknesses']}")
print(f"  エピソード: {input_episode['type']}")
print(f"  テーマ: {[t['theme'] for t in input_themes[:2]]}")

# 簡易類似度計算（TF-IDFのみ）
print("\n" + "=" * 80)
print("簡易類似度計算（TF-IDFベース）")
print("=" * 80)

vectorizer = TfidfVectorizer(max_features=100)
all_texts = es_data['combined_answer'].tolist() + [input_text]
tfidf_matrix = vectorizer.fit_transform(all_texts)

# 入力テキストとの類似度
input_vector = tfidf_matrix[-1]
es_vectors = tfidf_matrix[:-1]
tfidf_similarities = cosine_similarity(input_vector, es_vectors)[0]

# 強み・弱みボーナス/ペナルティを計算
input_strengths = set(input_sw['strengths'])
input_weaknesses = set(input_sw['weaknesses'])

final_scores = []
for idx, (tfidf_sim, (_, row)) in enumerate(zip(tfidf_similarities, es_data.iterrows())):
    es_sw = row['strengths_weaknesses']
    es_strengths = set(es_sw.get('strengths', []))
    es_weaknesses = set(es_sw.get('weaknesses', []))

    # ボーナス/ペナルティ計算
    bonus = 0.0

    # 強みの一致
    strength_overlap = len(input_strengths & es_strengths)
    if strength_overlap >= 2:
        bonus += 0.10
    elif strength_overlap == 1:
        bonus += 0.05

    # 強みが完全に異なる場合のペナルティ
    if len(input_strengths) > 0 and len(es_strengths) > 0 and strength_overlap == 0:
        bonus -= 0.03  # -0.06 → -0.03に変更

    # 弱みの一致
    weakness_overlap = len(input_weaknesses & es_weaknesses)
    if weakness_overlap >= 1:
        bonus += 0.05

    final_score = tfidf_sim + bonus
    final_score = max(0.0, min(1.0, final_score))

    final_scores.append({
        'id': row['id'],
        'company': row['company'],
        'tfidf_score': tfidf_sim,
        'bonus': bonus,
        'final_score': final_score,
        'strengths': es_sw.get('strengths', []),
        'strength_overlap': strength_overlap
    })

# スコア順にソート
final_scores.sort(key=lambda x: x['final_score'], reverse=True)

print("\n【結果】類似度ランキング:")
print("-" * 80)
for rank, result in enumerate(final_scores, 1):
    print(f"\n{rank}位: ES#{result['id']} ({result['company']})")
    print(f"    TF-IDFスコア: {result['tfidf_score']:.4f}")
    print(f"    ボーナス/ペナルティ: {result['bonus']:+.4f}")
    print(f"    最終スコア: {result['final_score']:.4f}")
    print(f"    強み: {result['strengths']}")
    print(f"    強みの重複: {result['strength_overlap']}個")

print("\n" + "=" * 80)
print("検証ポイント")
print("=" * 80)
print("✓ ES#1（行動力・留学）とES#3（行動力・起業）が上位に来ているか？")
print("✓ ES#2（説明力）とES#4（コミュニケーション力）はペナルティで下位か？")
print("=" * 80)

#!/usr/bin/env python3
"""
フルデータで類似度計算をテストするスクリプト
"""
import sys
import os
sys.path.insert(0, 'src')

# 環境変数を設定（必要に応じて）
os.environ.setdefault('OPENAI_API_KEY', 'dummy-key-for-testing')

import pandas as pd
from app import (
    load_csv_data,
    calculate_similarity,
    extract_strengths_and_weaknesses
)

print("=" * 80)
print("データローディングテスト")
print("=" * 80)

# データをロード
print("\n📂 データをロード中（CSVから）...")
print("⚠️  これには数分かかる場合があります...")
try:
    # CSVから直接ロード
    load_csv_data('data/unified_es_data_20251109.csv')
    print("✅ データロードが完了しました")

    # グローバル変数からes_dataを取得
    from app import es_data

    print(f"\n📊 データ統計:")
    print(f"  - 総ES数: {len(es_data)}")
    print(f"  - カラム: {list(es_data.columns)}")

    # 強み・弱み列が存在するか確認
    if 'strengths_weaknesses' in es_data.columns:
        print("\n✅ 'strengths_weaknesses' カラムが存在します")

        # サンプルを表示
        sample = es_data.iloc[0]
        sw = sample['strengths_weaknesses']
        print(f"\n【サンプルES（1件目）】")
        print(f"  企業: {sample.get('company', 'N/A')}")
        print(f"  質問: {sample.get('question', 'N/A')[:50]}...")
        print(f"  強み: {sw.get('strengths', [])}")
        print(f"  弱み: {sw.get('weaknesses', [])}")
    else:
        print("\n❌ 'strengths_weaknesses' カラムが見つかりません")

except Exception as e:
    print(f"\n❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("類似度計算テスト")
print("=" * 80)

# テスト用の入力
test_input = """
私の強みは、有言実行する行動力です。私は、口にしたことは絶対に成し遂げることを心掛けて達成します。
大学時代に「アメリカに行く」と言って一人でアメリカに行った経験があります。
一方の弱みは、行動力がありすぎるあまり一人で突っ走ってしまうことがあるところです。
"""

print("\n【入力ES】")
print(test_input.strip())

print("\n🔍 類似度を計算中...")
try:
    # 類似度計算（上位5件のみ）
    similar_es = calculate_similarity(test_input, top_n=5)

    print(f"\n✅ 類似度計算が完了しました（上位5件）")
    print("\n【結果】")
    print("-" * 80)

    for idx, (_, row) in enumerate(similar_es.iterrows(), 1):
        print(f"\n{idx}. 企業: {row.get('company', 'N/A')}")
        print(f"   類似度スコア: {row['similarity_score']:.4f}")
        print(f"   質問: {row.get('question', 'N/A')[:60]}...")

        # 強み・弱みを表示
        sw = row.get('strengths_weaknesses', {})
        if isinstance(sw, dict):
            print(f"   強み: {sw.get('strengths', [])}")
            print(f"   弱み: {sw.get('weaknesses', [])}")

        # 回答の一部を表示
        answer = row.get('combined_answer', '')
        print(f"   回答（抜粋）: {answer[:100]}...")
        print("-" * 80)

    # 入力ESの強み・弱みと比較
    input_sw = extract_strengths_and_weaknesses(test_input)
    print("\n【入力ESの特徴】")
    print(f"  強み: {input_sw['strengths']}")
    print(f"  弱み: {input_sw['weaknesses']}")

    print("\n【検証ポイント】")
    print("  ✓ 「行動力」を持つESが上位に来ているか？")
    print("  ✓ 「コミュニケーション力」だけのESはペナルティで下位に来ているか？")

except Exception as e:
    print(f"\n❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("テスト完了")
print("=" * 80)

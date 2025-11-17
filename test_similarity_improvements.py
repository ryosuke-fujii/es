#!/usr/bin/env python3
"""
類似度計算の改善をテストするスクリプト
"""
import sys
sys.path.insert(0, 'src')

from app import extract_strengths_and_weaknesses

# テストケース1: ユーザーが提供した例
test_input = """
私の強みは、有言実行する行動力です。私は、口にしたことは絶対に成し遂げることを心掛けて達成します。
大学時代に「アメリカに行く」と言って一人でアメリカに行った経験があります。
一方の弱みは、行動力がありすぎるあまり一人で突っ走ってしまうことがあるところです。
自分が決めたことを成し遂げようとして周りを気にせず一人で次々と進んでしまい周りの仲間を置いていくという失敗をしたことがあります。
"""

# 比較対象のES（全く異なる強み）
comparison_es = """
私の強みは人にわかりやすく説明できることです。私は大学入学後、○○の○○として活動しています。
○○や○○の経験を活かして、○○を目標に活動を行っています。
○○の活動を行う中で、理解してもらいやすい言葉選びや正確に伝わっていることを確かめながら話を進めることや話す順序、
タイミングを工夫しました。
"""

print("=" * 80)
print("テストケース: 強み・弱みの抽出")
print("=" * 80)

print("\n【入力ES】")
print(test_input.strip())

print("\n【入力ESの強み・弱み抽出結果】")
input_sw = extract_strengths_and_weaknesses(test_input)
print(f"  強み: {input_sw['strengths']}")
print(f"  強みキーワード: {input_sw['strength_keywords']}")
print(f"  弱み: {input_sw['weaknesses']}")
print(f"  弱みキーワード: {input_sw['weakness_keywords']}")

print("\n" + "=" * 80)
print("\n【比較対象ES】")
print(comparison_es.strip())

print("\n【比較対象ESの強み・弱み抽出結果】")
comparison_sw = extract_strengths_and_weaknesses(comparison_es)
print(f"  強み: {comparison_sw['strengths']}")
print(f"  強みキーワード: {comparison_sw['strength_keywords']}")
print(f"  弱み: {comparison_sw['weaknesses']}")
print(f"  弱みキーワード: {comparison_sw['weakness_keywords']}")

print("\n" + "=" * 80)
print("【期待される動作】")
print("=" * 80)
print("✅ 入力ESの強み: ['行動力・実行力'] が検出されるべき")
print("✅ 入力ESの弱み: ['突っ走る・周りが見えない'] が検出されるべき")
print("✅ 比較ESの強み: ['コミュニケーション力'] が検出されるべき")
print("❌ 強みが完全に異なるため、類似度計算でペナルティ（-0.12）が適用されるべき")
print("=" * 80)

# 一致度を確認
input_strengths = set(input_sw['strengths'])
comparison_strengths = set(comparison_sw['strengths'])
overlap = len(input_strengths & comparison_strengths)

print(f"\n強みの重複数: {overlap}")
if overlap == 0 and len(input_strengths) > 0 and len(comparison_strengths) > 0:
    print("✅ 強みが完全に異なるため、ペナルティが適用される条件を満たしています")
else:
    print("❌ ペナルティ条件を満たしていません")

print("\n" + "=" * 80)
print("テスト完了")
print("=" * 80)

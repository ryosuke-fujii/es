#!/usr/bin/env python3
"""
APIリクエストで3パターンのテストを実行
"""
import requests
import json

API_URL = "http://localhost:8000/analyze"

# ===================================================================
# テストパターン1: 行動力を強みとするES（ユーザー提供の例）
# ===================================================================
test_case_1 = {
    "esAnswers": [
        """私の強みは、有言実行する行動力です。私は、口にしたことは絶対に成し遂げることを心掛けて達成します。
大学時代に「アメリカに行く」と言って一人でアメリカに行った経験があります。
一方の弱みは、行動力がありすぎるあまり一人で突っ走ってしまうことがあるところです。
自分が決めたことを成し遂げようとして周りを気にせず一人で次々と進んでしまい周りの仲間を置いていくという失敗をしたことがあります。"""
    ],
    "targetIndustry": "IT・通信",
    "university": "早稲田大学",
    "targetCompanies": [],
    "major": "",
    "graduationYear": "",
    "onlyAccepted": False
}

# ===================================================================
# テストパターン2: コミュニケーション力を強みとするES
# ===================================================================
test_case_2 = {
    "esAnswers": [
        """私の強みは、人に分かりやすく説明できるコミュニケーション力です。
大学入学後、塾講師として活動する中で、生徒一人ひとりの理解度に合わせて説明の仕方を変えることを心掛けてきました。
理解してもらいやすい言葉選びや、正確に伝わっていることを確かめながら話を進めることで、
担当生徒の成績を平均20点向上させることができました。この経験から、相手の立場に立って考え、
適切な言葉で伝えることの重要性を学びました。"""
    ],
    "targetIndustry": "IT・通信",
    "university": "早稲田大学",
    "targetCompanies": [],
    "major": "",
    "graduationYear": "",
    "onlyAccepted": False
}

# ===================================================================
# テストパターン3: リーダーシップを強みとするES
# ===================================================================
test_case_3 = {
    "esAnswers": [
        """私の強みはリーダーシップです。大学時代、サークル代表として50名のメンバーをまとめ、
年間10回のイベントを成功させました。メンバーの意見を聞きながらも、最終的な決断は私が責任を持って行い、
チーム全体を一つの方向に導くことを心掛けました。特に、文化祭での出店では、
準備期間が短い中でもメンバーの役割分担を明確にし、全員が目標に向かって動ける環境を作りました。
結果として、過去最高の売上を達成することができ、リーダーとしての達成感を得ることができました。"""
    ],
    "targetIndustry": "IT・通信",
    "university": "早稲田大学",
    "targetCompanies": [],
    "major": "",
    "graduationYear": "",
    "onlyAccepted": False
}

def test_api(test_name, test_data, expected_strength):
    """APIをテストする"""
    print("\n" + "=" * 80)
    print(f"テストパターン: {test_name}")
    print("=" * 80)
    print(f"\n【入力ES】")
    print(test_data['esAnswers'][0][:200] + "...")
    print(f"\n【期待される強み】{expected_strength}")

    try:
        response = requests.post(API_URL, json=test_data, timeout=60)

        if response.status_code == 200:
            result = response.json()

            print(f"\n✅ APIリクエスト成功")

            # デバッグ: レスポンス全体を表示
            print(f"\n【レスポンスキー】{list(result.keys())}")

            # 業界類似ESを表示
            industry_similar_es = result.get('industrySimilarESSamples', [])
            print(f"【業界類似ES型】{type(industry_similar_es)}")
            print(f"【業界類似ES】{industry_similar_es if not isinstance(industry_similar_es, list) or len(industry_similar_es) < 10 else 'リスト (長すぎて省略)'}")

            # エピソードタイプ類似ESを表示
            episode_similar_es = result.get('episodeTypeSimilarESSamples', [])
            print(f"【エピソードタイプ類似ES型】{type(episode_similar_es)}")

            # マッチ企業を表示
            match_companies = result.get('matchCompanies', [])
            print(f"【マッチ企業数】{len(match_companies)}")

            # 業界類似ESがリストの場合のみ処理
            if isinstance(industry_similar_es, list) and len(industry_similar_es) > 0:
                print(f"\n【上位3件の業界類似ES】")
                print("-" * 80)

                for i, es in enumerate(industry_similar_es[:3], 1):
                    print(f"\n{i}位:")
                    print(f"  企業: {es.get('company', 'N/A')}")
                    print(f"  類似度: {es.get('similarity', 0):.1f}%")
                    print(f"  回答（抜粋）: {es.get('answer', '')[:150]}...")

                    # 回答から強みを推測
                    answer = es.get('answer', '')
                    if '行動力' in answer or '実行力' in answer or '有言実行' in answer:
                        print(f"  💡 この回答には「行動力」が含まれています")
                    elif 'コミュニケーション' in answer or '説明' in answer or '伝える' in answer:
                        print(f"  💡 この回答には「コミュニケーション力」が含まれています")
                    elif 'リーダー' in answer or '代表' in answer or 'まとめ' in answer:
                        print(f"  💡 この回答には「リーダーシップ」が含まれています")

            print("\n" + "-" * 80)
            print(f"検証ポイント: 上位ESに「{expected_strength}」関連の内容が多いか？")

        else:
            print(f"\n❌ APIエラー: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"\n❌ リクエストエラー: {e}")
        import traceback
        traceback.print_exc()

# ===================================================================
# テスト実行
# ===================================================================
print("=" * 80)
print("APIリクエストテスト開始")
print("=" * 80)

test_api("パターン1: 行動力", test_case_1, "行動力・実行力")
test_api("パターン2: コミュニケーション力", test_case_2, "コミュニケーション力")
test_api("パターン3: リーダーシップ", test_case_3, "リーダーシップ")

print("\n" + "=" * 80)
print("全テスト完了")
print("=" * 80)

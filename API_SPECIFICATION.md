# ES診断ツール API仕様書

## 基本情報

**本番環境URL**: `https://es-diagnosis-tool-224578818083.asia-northeast1.run.app`

**APIドキュメント（Swagger UI）**: `https://es-diagnosis-tool-224578818083.asia-northeast1.run.app/docs`

---

## エンドポイント一覧

### 1. ホームページ取得

```
GET /
```

フロントエンドのHTMLページを返します。

**レスポンス**: HTML

---

### 2. ES診断実行（メインAPI）

```
POST /analyze
```

エントリーシート（ES）を分析し、マッチする企業や類似ESサンプルを返します。

#### リクエスト仕様

**Content-Type**: `application/json`

**リクエストボディ（JSON）**:

```json
{
  "esAnswers": [
    "回答1（100文字以上推奨）",
    "回答2",
    "回答3"
  ],
  "targetIndustry": "IT・通信",
  "university": "早稲田大学",
  "targetCompanies": [
    "株式会社サイバーエージェント",
    "楽天グループ株式会社"
  ],
  "major": "商学部",
  "graduationYear": "2025"
}
```

#### フィールド詳細

| フィールド名 | 型 | 必須 | 説明 | 制約・備考 |
|------------|-------|------|------|-----------|
| `esAnswers` | `string[]` | ✅ **必須** | ES質問に対する回答の配列 | ・最低1つの回答が必要<br>・**少なくとも1つの回答は100文字以上必須**<br>・複数の回答を配列で送信 |
| `targetIndustry` | `string` | ✅ **必須** | 志望業界 | ・空文字列不可<br>・例: "IT・通信", "金融", "コンサル" |
| `university` | `string` | ⭕ オプション | 大学名 | ・空文字列可<br>・デフォルト: `""`<br>・例: "早稲田大学", "慶應義塾大学" |
| `targetCompanies` | `string[]` | ⭕ オプション | 志望企業のリスト | ・空配列可<br>・デフォルト: `[]`<br>・最大3社程度を推奨 |
| `major` | `string` | ⭕ オプション | 専攻・学部 | ・空文字列可<br>・デフォルト: `""`<br>・例: "商学部", "工学部" |
| `graduationYear` | `string` | ⭕ オプション | 卒業年度 | ・空文字列可<br>・デフォルト: `""`<br>・例: "2025", "2026" |

#### バリデーションルール

1. ✅ `esAnswers`は**空配列不可**
2. ✅ **最低1つの回答が100文字以上**である必要がある
3. ✅ `targetIndustry`は**必須**かつ空文字列不可

#### エラーレスポンス

**400 Bad Request**:

```json
// ES回答が空の場合
{
  "detail": "ES回答を入力してください"
}

// 100文字以上の回答がない場合
{
  "detail": "少なくとも1つの回答は100文字以上入力してください"
}

// 志望業界が未選択の場合
{
  "detail": "志望業界を選択してください"
}
```

**500 Internal Server Error**:

```json
{
  "detail": "エラーメッセージ"
}
```

#### 成功レスポンス（200 OK）

**レスポンスボディ構造**:

```json
{
  "matchCompanies": [
    {
      "name": "企業名",
      "industry": "業界分類",
      "matchScore": 76,
      "reason": "マッチング理由",
      "avgGpa": "2.8-3.4",
      "avgSalary": "給与情報URL",
      "employeeCount": "従業員数",
      "esSamples": [
        {
          "company": "企業名",
          "industry": "業界",
          "result": "通過",
          "similarity": 83.7,
          "dataSource": "syukatsu-kaigi-job",
          "profile": {
            "university": "大学名",
            "major": "専攻",
            "gradYear": "卒業年度"
          },
          "esContent": [
            {
              "question": "質問内容",
              "answer": "回答内容"
            }
          ]
        }
      ]
    }
  ],
  "industryAnalysis": {
    "industry": "業界名",
    "description": "業界説明",
    "trends": "トレンド情報"
  },
  "esAnalysis": [
    {
      "answer": "回答内容",
      "episodeType": "エピソードタイプ",
      "strength": "強み",
      "improvement": "改善点"
    }
  ],
  "industrySimilarESSamples": [
    {
      "company": "企業名",
      "similarity": 85.2,
      "esContent": [...]
    }
  ],
  "episodeTypeSimilarESSamples": [
    {
      "company": "企業名",
      "episodeType": "エピソードタイプ",
      "similarity": 78.3,
      "esContent": [...]
    }
  ],
  "targetCompaniesMatch": [
    {
      "name": "志望企業名",
      "industry": "業界",
      "matchScore": 72,
      "reason": "マッチング理由",
      "dataCount": 62,
      "rank": 1,
      "esSamples": [...]
    }
  ],
  "dataStatistics": {
    "totalEsCount": 68346,
    "matchedEsCount": 100,
    "industryEsCount": 13100,
    "targetCompaniesDataCount": {
      "企業名": データ件数
    },
    "avgMatchRate": 63.0
  },
  "userInfo": {
    "university": "大学名",
    "major": "専攻",
    "graduationYear": "卒業年度",
    "targetIndustry": "志望業界",
    "targetCompanies": ["企業名1", "企業名2"]
  },
  "episodeTypeInfo": {
    "primary": "主要エピソードタイプ",
    "secondary": "副次エピソードタイプ",
    "confidence": 0.85
  }
}
```

---

## リクエスト例

### cURLでのリクエスト例

```bash
curl -X POST "https://es-diagnosis-tool-224578818083.asia-northeast1.run.app/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "esAnswers": [
      "大学時代、ゼミ活動でチームリーダーとして20人のメンバーをまとめ、地域活性化プロジェクトを成功させました。具体的には、地元商店街との連携イベントを企画し、3ヶ月間で来場者数を前年比200%増加させることができました。この経験を通じて、多様なステークホルダーとの調整力とプロジェクトマネジメント能力を身につけました。",
      "インターンシップで営業部門に配属され、新規顧客開拓に取り組み、月間目標を120%達成しました。データ分析を活用してターゲット顧客を絞り込み、効率的な営業活動を実現しました。",
      "学生団体の代表として、予算管理や企画立案を行い、イベント参加者を前年比150%増加させました。限られた予算の中で最大の効果を出すため、クラウドファンディングも活用し、目標金額の180%を達成しました。"
    ],
    "targetIndustry": "IT・通信",
    "university": "早稲田大学",
    "targetCompanies": [
      "株式会社サイバーエージェント",
      "楽天グループ株式会社"
    ],
    "major": "商学部",
    "graduationYear": "2025"
  }'
```

### JavaScriptでのリクエスト例（fetch API）

```javascript
const response = await fetch('https://es-diagnosis-tool-224578818083.asia-northeast1.run.app/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    esAnswers: [
      "大学時代、ゼミ活動でチームリーダーとして20人のメンバーをまとめ、地域活性化プロジェクトを成功させました。具体的には、地元商店街との連携イベントを企画し、3ヶ月間で来場者数を前年比200%増加させることができました。この経験を通じて、多様なステークホルダーとの調整力とプロジェクトマネジメント能力を身につけました。",
      "インターンシップで営業部門に配属され、新規顧客開拓に取り組み、月間目標を120%達成しました。データ分析を活用してターゲット顧客を絞り込み、効率的な営業活動を実現しました。"
    ],
    targetIndustry: "IT・通信",
    university: "早稲田大学",
    targetCompanies: ["株式会社サイバーエージェント", "楽天グループ株式会社"],
    major: "商学部",
    graduationYear: "2025"
  })
});

const data = await response.json();
console.log(data);
```

### Pythonでのリクエスト例（requests）

```python
import requests
import json

url = "https://es-diagnosis-tool-224578818083.asia-northeast1.run.app/analyze"

payload = {
    "esAnswers": [
        "大学時代、ゼミ活動でチームリーダーとして20人のメンバーをまとめ、地域活性化プロジェクトを成功させました。具体的には、地元商店街との連携イベントを企画し、3ヶ月間で来場者数を前年比200%増加させることができました。この経験を通じて、多様なステークホルダーとの調整力とプロジェクトマネジメント能力を身につけました。",
        "インターンシップで営業部門に配属され、新規顧客開拓に取り組み、月間目標を120%達成しました。データ分析を活用してターゲット顧客を絞り込み、効率的な営業活動を実現しました。"
    ],
    "targetIndustry": "IT・通信",
    "university": "早稲田大学",
    "targetCompanies": ["株式会社サイバーエージェント", "楽天グループ株式会社"],
    "major": "商学部",
    "graduationYear": "2025"
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
data = response.json()

print(json.dumps(data, indent=2, ensure_ascii=False))
```

---

## 最小限のリクエスト例

必須フィールドのみを使用した最小構成：

```json
{
  "esAnswers": [
    "大学時代、サークル活動でリーダーとして30人のメンバーをまとめ、新入生獲得数を前年比150%に増やしました。具体的には、SNS戦略を見直し、活動内容の動画発信を強化することで、認知度を大幅に向上させることができました。"
  ],
  "targetIndustry": "IT・通信"
}
```

---

## レスポンスデータの活用例

### マッチング企業トップ5を表示

```javascript
const topCompanies = data.matchCompanies.slice(0, 5);
topCompanies.forEach((company, index) => {
  console.log(`${index + 1}. ${company.name} - マッチ度: ${company.matchScore}`);
});
```

### 志望企業のマッチ結果を取得

```javascript
const cyberAgentMatch = data.targetCompaniesMatch.find(
  c => c.name === "株式会社サイバーエージェント"
);
console.log(`サイバーエージェント マッチスコア: ${cyberAgentMatch.matchScore}`);
console.log(`データ件数: ${cyberAgentMatch.dataCount}件`);
```

### データ統計情報の表示

```javascript
console.log(`総ES数: ${data.dataStatistics.totalEsCount}`);
console.log(`マッチES数: ${data.dataStatistics.matchedEsCount}`);
console.log(`業界内ES数: ${data.dataStatistics.industryEsCount}`);
```

---

## 注意事項

1. **文字数制限**: 少なくとも1つのES回答は**100文字以上**必要です
2. **タイムアウト**: 処理に時間がかかる場合があるため、タイムアウトは120秒以上を推奨
3. **レート制限**: 現在は設定されていませんが、大量リクエストは避けてください
4. **認証**: 現在は`allow-unauthenticated`で公開中（将来的に認証が追加される可能性あり）
5. **データソース**: 68,346件のES実績データに基づいて分析されます

---

## 対応業界一覧（例）

- IT・通信
- 金融
- コンサルティング
- メーカー
- 商社
- 広告・マスコミ
- 不動産
- その他212業界

詳細な業界リストは`GET /`のレスポンスHTMLに埋め込まれています。

---

## サポート

- **APIドキュメント**: https://es-diagnosis-tool-224578818083.asia-northeast1.run.app/docs
- **GitHub**: （リポジトリURL）
- **問題報告**: GitHub Issues

---

**最終更新**: 2025-11-09

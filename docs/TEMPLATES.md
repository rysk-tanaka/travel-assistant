# TravelAssistant 初期テンプレート集

## テンプレート構成

### 1. 国内出張基本テンプレート

**ファイル名**: `templates/domestic_business.md`
**用途**: 国内出張の基本パターン

---

```markdown
---
template_type: "domestic_business"
template_version: "1.0"
last_updated: "2025-06-27"
customizable_fields:
  - destination
  - duration
  - season
  - transport_method
---

# 国内出張準備チェックリスト

## 基本情報
- **出張先**: {{destination}}
- **期間**: {{start_date}} ～ {{end_date}} （{{duration}}泊{{duration+1}}日）
- **目的**: {{purpose}}
- **交通手段**: {{transport_method}}

## 📋 チェックリスト

### 🎫 移動関連
- [ ] 交通チケット（{{transport_method}}）
- [ ] 身分証明書（運転免許証・マイナンバーカード）
- [ ] 時刻表・乗換案内の確認
- [ ] 出発時刻の再確認

### 💼 仕事関連
- [ ] ノートPC + 充電器
- [ ] 名刺（{{business_cards_count}}枚程度）
- [ ] 会議資料（印刷版 + デジタル）
- [ ] ボールペン・メモ帳
- [ ] 会社携帯・社用スマホ

### 👔 服装・身だしなみ
- [ ] {{duration}}泊分の着替え
- [ ] 下着・靴下（{{duration+1}}日分）
- [ ] 予備シャツ（1枚）
- [ ] ビジネスシューズ
- [ ] ベルト・ネクタイ

### 🧳 生活用品
- [ ] 歯ブラシ・歯磨き粉
- [ ] シャンプー・ボディソープ（宿泊先にない場合）
- [ ] タオル（必要に応じて）
- [ ] 常備薬
- [ ] モバイルバッテリー
- [ ] 充電ケーブル（スマホ・PC）

### 💰 金銭関連
- [ ] 現金（{{recommended_cash}}円程度）
- [ ] クレジットカード
- [ ] 交通系ICカード
- [ ] 会社経費用レシート保管袋

### 🌦️ 天気対応（{{weather_condition}}）
{{weather_items}}

### 📍 {{destination}}特有項目
{{regional_items}}

## 📝 重要な連絡先
- **宿泊先**: {{hotel_name}} / {{hotel_phone}}
- **訪問先**: {{client_name}} / {{client_phone}}
- **緊急連絡先**: {{emergency_contact}}

## 🎁 お土産メモ
{{souvenir_notes}}

## ✅ 出発前最終確認
- [ ] 天気予報の最終チェック
- [ ] 交通状況・遅延情報確認
- [ ] 宿泊先・会議場所の最終確認
- [ ] 家の戸締り・ガス・電気確認
- [ ] 冷蔵庫の整理
```

---

### 2. 札幌出張専用テンプレート

**ファイル名**: `templates/sapporo_business.md`
**用途**: 札幌出張の最適化版

---

```markdown
---
template_type: "sapporo_business"
template_version: "1.0"
based_on: "domestic_business"
last_updated: "2025-06-27"
---

# 札幌出張準備チェックリスト

## 基本情報
- **出張先**: 札幌市
- **期間**: {{start_date}} ～ {{end_date}} （{{duration}}泊{{duration+1}}日）
- **空港**: 羽田 → 新千歳
- **移動時間**: 約1時間35分

## 📋 チェックリスト

### ✈️ 航空関連
- [ ] 航空券（eチケット・QRコード保存）
- [ ] 身分証明書（写真付き必須）
- [ ] 搭乗手続き（オンラインチェックイン推奨）
- [ ] 手荷物規定確認（液体制限等）
- [ ] 搭乗2時間前到着予定

### 💼 仕事関連（札幌特化）
- [ ] ノートPC + 充電器
- [ ] 名刺（多めに100枚 - 北海道は名刺交換文化）
- [ ] 会議資料（印刷版推奨 - WiFi不安定対策）
- [ ] 北海道企業向け提案資料
- [ ] 防水PCケース（雪・雨対策）

### 🧥 服装（札幌気候対応）
#### 6月〜8月（夏）
- [ ] 薄手の長袖（朝夕冷える）
- [ ] ライトジャケット
- [ ] 長ズボン（虫除け・冷房対策）
- [ ] 歩きやすい靴（観光地移動多い）

#### 9月〜11月（秋）
- [ ] 厚手のジャケット・コート
- [ ] セーター・カーディガン
- [ ] 手袋・マフラー（11月は必須）
- [ ] 防水性のある靴

#### 12月〜3月（冬）
- [ ] 防寒コート（ダウン推奨）
- [ ] 厚手のセーター・インナー
- [ ] 手袋・マフラー・帽子
- [ ] 雪対応靴（滑り止めソール）
- [ ] ホッカイロ

#### 4月〜5月（春）
- [ ] 中厚手のジャケット
- [ ] 重ね着用インナー
- [ ] 雨具（春雨多い）

### 🌦️ 札幌天気対策
- [ ] 折り畳み傘（年中必須）
- [ ] ウインドブレーカー（風強い）
- [ ] 日焼け止め（雪反射注意・冬でも必要）

### 🍜 札幌グルメ・お土産
#### 必食グルメ
- [ ] 海鮮丼（朝市・二条市場）
- [ ] ジンギスカン
- [ ] 札幌ラーメン（味噌・塩・醤油）
- [ ] スープカレー

#### 定番お土産
- [ ] 六花亭（マルセイバターサンド）
- [ ] ロイズ（生チョコレート）
- [ ] 白い恋人
- [ ] じゃがポックル
- [ ] 昆布茶・海産物

### 📍 札幌特有注意事項
- [ ] すすきの周辺は夜遅くまで営業
- [ ] 地下街が発達（冬は地下移動推奨）
- [ ] 交通系ICカード：Kitaca対応確認
- [ ] タクシー料金は本州より高め
- [ ] 観光地（時計台・赤レンガ）は徒歩圏内

### 🚇 交通手段
- [ ] 新千歳空港 ↔ 札幌駅：JR快速エアポート（37分）
- [ ] 市内移動：地下鉄1日券購入検討
- [ ] レンタカー手配（必要に応じて）

## 📞 緊急連絡先（札幌）
- **新千歳空港**: 0123-23-0111
- **札幌駅**: 011-222-7111
- **札幌市観光案内**: 011-213-5088

## 💡 札幌出張のコツ
- 余裕のあるスケジュール設定（天候による遅延考慮）
- 現地の方との懇親会文化を理解
- 海産物アレルギーの確認
- 夏でも長袖必須（冷房・朝夕対策）
```

---

### 3. レジャー旅行基本テンプレート

**ファイル名**: `templates/leisure_domestic.md`

---

```markdown
---
template_type: "leisure_domestic"
template_version: "1.0"
last_updated: "2025-06-27"
---

# 国内レジャー旅行チェックリスト

## 基本情報
- **旅行先**: {{destination}}
- **期間**: {{start_date}} ～ {{end_date}}
- **旅行タイプ**: {{trip_type}} (観光/温泉/アウトドア/都市部)
- **同行者**: {{companions}}

## 📋 チェックリスト

### 🎫 移動・宿泊
- [ ] 交通チケット
- [ ] 宿泊予約確認書
- [ ] 身分証明書
- [ ] 保険証

### 📱 旅行便利グッズ
- [ ] スマホ + 充電器
- [ ] モバイルバッテリー
- [ ] カメラ + SDカード
- [ ] 旅行ガイドブック・地図アプリ

### 👕 服装（{{trip_type}}向け）
{{activity_specific_clothes}}

### 🧴 衛生・ケア用品
- [ ] 歯ブラシセット
- [ ] 洗顔・スキンケア用品
- [ ] 日焼け止め
- [ ] 虫除けスプレー（必要に応じて）

### 💊 健康管理
- [ ] 常備薬
- [ ] 絆創膏・消毒液
- [ ] 酔い止め薬
- [ ] 持病の薬

### 🎁 お土産・記念品
- [ ] お土産リスト作成
- [ ] 予算設定
- [ ] 配送用の箱・梱包材（大量購入時）

### 💰 予算管理
- [ ] 現金（予備分含む）
- [ ] クレジットカード
- [ ] 旅行予算の上限設定

## 🌦️ 天気対応
{{weather_specific_items}}

## 📍 {{destination}}特有項目
{{regional_leisure_items}}
```

## テンプレート使用方法

### 1. 変数置換ルール

```python
# 基本変数
{{destination}} → 実際の目的地名
{{start_date}} → 出発日
{{end_date}} → 帰着日
{{duration}} → 宿泊日数

# 条件別変数
{{weather_condition}} → 天気予報に基づく条件
{{weather_items}} → 天気対応アイテムリスト
{{regional_items}} → 地域特有アイテム
```

### 2. 自動調整ポイント

- **期間調整**: 1泊/2泊/長期で持ち物数調整
- **季節調整**: 月別の気候対応
- **目的調整**: 出張/レジャーでの優先度変更
- **交通手段調整**: 飛行機/新幹線/車での固有アイテム

### 3. 学習ポイント

- チェック済み率の記録
- 忘れ物の記録（次回自動追加）
- 不要だったアイテムの記録（次回除外候補）
- 追加したアイテムの記録（テンプレート改善）

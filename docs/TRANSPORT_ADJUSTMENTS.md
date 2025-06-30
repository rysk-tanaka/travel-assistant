# 交通手段別調整機能の詳細化

## 概要
交通手段別調整機能を詳細化し、より精密な条件判定と適切な持ち物提案を実現しました。

## 実装内容

### 1. 詳細な交通手段ルール（transport_rules.yaml）
- **飛行機**: 国内/国際線の区別、液体制限、手荷物制限
- **新幹線**: 指定席券確認、大型荷物予約、駅弁情報
- **車**: 自家用車/レンタカーの区別、季節別装備、ETCカード
- **バス**: 高速バス/夜行バスの区別、快適グッズ
- **その他**: 自転車、バイクなどの特殊な移動手段

### 2. 条件判定の改善（smart_engine.py）
```python
# 新幹線駅の詳細リスト
shinkansen_cities = [
    "東京", "品川", "新横浜", "小田原", "熱海",
    "三島", "新富士", "静岡", "掛川", "浜松",
    # ... 全新幹線駅
]

# 観光地判定（レンタカー推定）
tourist_areas = ["沖縄", "北海道", "石垣", "宮古", "屋久島", "小豆島"]

# 夜行バス判定（0泊で長距離移動）
if request.duration == 0 and any(city in request.destination for city in major_cities):
    additional_conditions["night_bus"] = True
```

### 3. 季節別調整
- **冬季（12-3月）**: スタッドレスタイヤ、解氷スプレー、雪かきブラシ
- **夏季（6-9月）**: 車内用日よけ、クーラーボックス

## 実行例

### 飛行機で札幌へ（2泊3日・6月）
```
📋 追加される持ち物 (8個):
  【移動関連】
    ✓ 機内持ち込み用透明袋（1L以下）
    ✓ モバイルバッテリー（手荷物用）
    ✓ 耳栓・アイマスク
    ✓ ネックピロー
    ✓ 機内用スリッパ
```

### 車で長野へ（冬・2泊3日・1月）
```
📋 追加される持ち物 (10個):
  【移動関連】
    ✓ 運転免許証
    ✓ ETCカード
    ✓ スタッドレスタイヤ/チェーン
    ✓ 解氷スプレー
    ✓ 雪かきブラシ
```

## 今後の改善案

### 1. ユーザー入力の拡張
```python
# Discord コマンドでの詳細指定
!trip smart 大阪 2025-07-15 2025-07-16 business --transport=train --shinkansen=true
!trip smart 沖縄 2025-08-10 2025-08-13 leisure --transport=car --rental=true
```

### 2. 交通手段の自動推定
- 距離と時間から最適な交通手段を提案
- 複数の交通手段を組み合わせた場合の対応

### 3. 地域連携の強化
- 空港/駅から目的地までの二次交通考慮
- 地域特有の交通事情（例：沖縄はレンタカー必須）

### 4. 学習機能との統合
- 個人の交通手段の好み学習
- よく忘れる交通関連アイテムの強調

## テスト方法

### 単体テスト
```bash
# TransportRulesLoaderのテスト
python -m pytest tests/unit/test_transport_rules.py

# 統合テスト（SmartEngineとの連携）
python -m pytest tests/unit/test_smart_engine.py -k transport
```

### デモンストレーション
```bash
# 各交通手段の動作確認
python demo_transport.py
```

## API仕様

### TransportRulesLoader.get_transport_items()
```python
def get_transport_items(
    transport_method: TransportMethod,  # "airplane", "train", "car", "bus", "other"
    trip_duration: int,                 # 旅行日数
    is_domestic: bool = True,           # 国内/国際
    month: int | None = None,           # 旅行月（季節調整用）
    additional_conditions: dict[str, Any] | None = None,  # 追加条件
) -> list[ChecklistItem]:
```

### 追加条件の例
```python
additional_conditions = {
    "is_shinkansen": True,      # 新幹線利用
    "is_rental": True,          # レンタカー利用
    "is_highway": True,         # 高速バス利用
    "night_bus": True,          # 夜行バス
    "long_distance": True,      # 長距離移動
    "distance": 200,            # 移動距離（km）
    "large_luggage": True,      # 大型荷物あり
    "sub_method": "bicycle",    # その他の詳細（自転車、バイク等）
}
```

## パフォーマンス
- YAMLファイルのキャッシュにより高速動作
- 条件判定は単純な文字列比較で効率的
- 平均処理時間: < 10ms

## セキュリティ
- 条件評価にevalを使用せず、安全な実装
- ユーザー入力は型チェックで検証

---
*最終更新: 2025-06-30*

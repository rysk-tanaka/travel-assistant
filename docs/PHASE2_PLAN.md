# Phase 2 実装計画

## 概要
Phase 2では、基本的なスマート調整機能を外部APIと連携させ、より高度な自動調整を実現します。

## 実装優先順位

### 1. 🌤️ 天気予報連携（Week 1）
**理由**: 最も実用的で即効性が高い機能

#### 実装タスク
1. **OpenWeatherMap APIセットアップ**
   - [ ] APIキー取得（無料プラン）
   - [ ] 環境変数設定（OPENWEATHERMAP_API_KEY）
   - [ ] API仕様調査・実装設計

2. **天気データ取得モジュール**
   - [ ] `src/core/weather_service.py` 作成
   - [ ] 都市名→座標変換（Geocoding API）
   - [ ] 天気予報取得（5日間予報）
   - [ ] エラーハンドリング

3. **天気に基づく調整ロジック**
   - [ ] 降水確率による雨具追加
   - [ ] 気温による服装調整
   - [ ] 天候警報による特別対応
   - [ ] UV指数による日焼け対策

4. **キャッシュ実装**
   - [ ] メモリキャッシュ（1時間有効）
   - [ ] 同一地域・期間の重複API呼び出し防止

### 2. 🗾 地域特性の高度化（Week 2）
**理由**: 日本の地域性を活かした実用的な機能

#### 実装タスク
1. **地域データベース構築**
   - [ ] `src/data/regions.yaml` 作成
   - [ ] 都道府県別の特性データ
   - [ ] 季節別の調整ルール
   - [ ] 地域名の正規化・マッチング

2. **地域別調整の詳細化**
   ```yaml
   regions:
     hokkaido:
       seasons:
         summer:
           items: ["虫除けスプレー", "薄手の長袖"]
           reason: "夏でも朝夕は冷える、蚊が多い"
         winter:
           items: ["滑り止め付き靴", "ホッカイロ", "厚手の手袋"]
           reason: "雪道対策必須、極寒対策"
     kyoto:
       general:
         items: ["歩きやすい靴", "日傘"]
         reason: "観光地が多く歩く、夏は特に暑い"
       seasons:
         autumn:
           items: ["カメラ", "予備バッテリー"]
           reason: "紅葉シーズン"
   ```

3. **地域イベント考慮**
   - [ ] 主要イベント情報（祭り、花火大会など）
   - [ ] 混雑予測による追加アイテム

### 3. 🚄 交通手段別調整の詳細化（Week 3）
**理由**: 移動手段による準備の違いは大きい

#### 実装タスク
1. **交通手段別ルール拡充**
   - [ ] `src/data/transport_rules.yaml` 作成
   - [ ] 各交通手段の詳細ルール

2. **実装例**
   ```yaml
   transport:
     airplane:
       domestic:
         restrictions:
           liquids: "100ml以下の容器"
           battery: "モバイルバッテリーは手荷物"
         recommendations:
           - "オンラインチェックイン"
           - "空港には2時間前到着"
           - "耳栓・アイマスク"
       international:
         additional:
           - "パスポート"
           - "現地通貨"
           - "変換プラグ"

     shinkansen:
       recommendations:
         - "指定席予約確認"
         - "駅弁の事前調査"
         - "大きな荷物は特大荷物スペース予約"
   ```

### 4. 📅 期間別最適化の高度化（Week 3-4）
**理由**: 滞在期間による最適化は重要

#### 実装タスク
1. **期間別ルールの詳細化**
   - [ ] 1泊/2-3泊/4-7泊/長期のカテゴリ分け
   - [ ] 洗濯タイミングの計算
   - [ ] 着回し提案

2. **スマート圧縮提案**
   - [ ] 持ち物の優先順位付け
   - [ ] 現地調達可能品の提案

## 技術実装詳細

### Weather Service実装例
```python
# src/core/weather_service.py
import aiohttp
from typing import Optional
from pydantic import BaseModel
from src.config.settings import settings

class WeatherData(BaseModel):
    temperature: float
    feels_like: float
    humidity: int
    rain_probability: float
    weather_condition: str
    uv_index: Optional[float] = None

class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHERMAP_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self._cache: dict[str, tuple[WeatherData, datetime]] = {}

    async def get_weather_forecast(
        self,
        city: str,
        start_date: date,
        end_date: date
    ) -> list[WeatherData]:
        # キャッシュチェック
        cache_key = f"{city}_{start_date}_{end_date}"
        if cached := self._get_from_cache(cache_key):
            return cached

        # API呼び出し
        coords = await self._get_coordinates(city)
        forecast = await self._fetch_forecast(coords.lat, coords.lon)

        # 期間内のデータをフィルタリング
        weather_data = self._filter_forecast_by_dates(
            forecast, start_date, end_date
        )

        # キャッシュ保存
        self._save_to_cache(cache_key, weather_data)

        return weather_data
```

### 統合方法
```python
# src/core/smart_engine.py の拡張
class SmartTemplateEngine:
    def __init__(self):
        self.weather_service = WeatherService()
        self.region_matcher = RegionMatcher()
        # ... 既存のコード

    async def generate_checklist(self, request: TripRequest) -> TripChecklist:
        # 並行してデータ取得
        weather_task = self.weather_service.get_weather_forecast(
            request.destination,
            request.start_date,
            request.end_date
        )

        region_data = self.region_matcher.get_region_data(
            request.destination
        )

        weather_data = await weather_task

        # 調整適用
        items = self._apply_all_adjustments(
            base_template=template,
            weather_data=weather_data,
            region_data=region_data,
            request=request
        )
```

## 成功指標

### Phase 2完了基準
- [ ] OpenWeatherMap APIと連携して天気予報取得
- [ ] 天気に応じた持ち物の自動調整
- [ ] 47都道府県の地域特性データ整備
- [ ] 詳細な交通手段別ルール実装
- [ ] 期間別の最適化ロジック実装
- [ ] 全機能のテストカバレッジ90%以上

### 期待される効果
- 天気による忘れ物防止（傘、日焼け止めなど）
- 地域特有の準備漏れ防止
- 交通手段に応じた最適な準備
- 無駄な荷物の削減

## リスクと対策

### 技術的リスク
| リスク | 対策 |
|--------|------|
| API制限 | キャッシュ実装、フォールバック |
| 地域名の曖昧性 | 正規化処理、候補提示 |
| データ量増大 | 段階的実装、最適化 |

## 次のステップ

1. **今すぐ実行**
   - OpenWeatherMap APIキー取得
   - .env.exampleに追加
   - weather_service.pyの基本実装

2. **今週の目標**
   - 天気予報連携の完成
   - 基本的な天気調整ロジック

3. **Phase 2終了時**
   - Phase 3（AI連携）の準備
   - ユーザーフィードバックの収集

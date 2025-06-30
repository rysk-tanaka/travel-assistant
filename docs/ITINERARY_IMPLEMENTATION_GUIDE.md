# 移動スケジュール連携機能 実装ガイド

## 🎯 概要

既存のTravelAssistantプロジェクトに、航空券・宿泊先予約情報と連携した移動スケジュール管理機能を追加する実装ガイドです。

## 📍 現在のプロジェクト状況

- **Phase 1**: ✅ 完了（基本機能実装済み）
- **Phase 2**: 🚧 実装中（天気予報連携、交通手段調整済み）
- **Phase 3**: 📋 計画中（AI機能・高度な連携）

→ 移動スケジュール連携機能はPhase 3の一部として実装

## 🔧 段階的実装アプローチ

### Step 1: データモデル拡張（1週間）

#### 1.1 既存モデルへの追加

```python
# src/models.py に以下を追加

# 新しい型定義
type FlightStatus = Literal["scheduled", "delayed", "cancelled", "arrived"]
type AccommodationType = Literal["hotel", "ryokan", "airbnb", "friends", "other"]

# 新しいモデルクラス（FlightInfo, AccommodationInfo, TripItinerary）
# ※ 詳細はITINERARY_INTEGRATION.mdを参照

# 既存のTripChecklistに追加
class TripChecklist(BaseModel):
    # 既存のフィールド...
    itinerary: TripItinerary | None = Field(default=None, description="旅行行程")
```

#### 1.2 テスト作成

```bash
# 新しいテストファイル作成
touch tests/unit/test_itinerary_models.py
```

### Step 2: 最小限の機能実装（1週間）

#### 2.1 手動入力によるスケジュール管理

```python
# src/bot/schedule_commands.py（新規作成）
# 基本的なスケジュール入力・表示機能のみ実装

# コマンド例：
# /schedule add_flight JAL515 2025-07-01 08:00 HND CTS
# /schedule view
```

#### 2.2 既存コマンドとの統合

```python
# main.py に追加
from src.bot.schedule_commands import ScheduleCommands

# Cog登録
bot.add_cog(ScheduleCommands(bot))
```

### Step 3: スマートチェックリストとの連携（1週間）

#### 3.1 スケジュール考慮の調整

```python
# src/core/smart_engine.py に追加
def _get_schedule_adjustments(self, itinerary: TripItinerary | None) -> list[ChecklistItem]:
    """スケジュールに基づく調整項目を生成"""
    if not itinerary:
        return []

    items = []
    # 早朝便チェック、長時間フライト対応など
    return items
```

### Step 4: メールパーサー実装（2週間）

#### 4.1 基本パーサー実装

```python
# src/core/booking_parser.py（新規作成）
# JAL, ANAの予約確認メールパーサーから開始
```

### Step 5: リマインダー機能（1週間）

#### 5.1 APScheduler導入

```bash
# pyproject.tomlに追加
apscheduler = "^3.10.0"
```

## 📋 実装チェックリスト

### Phase 3-A: 基礎実装

- [ ] データモデル定義（FlightInfo, AccommodationInfo, TripItinerary）
- [ ] モデルのテスト作成
- [ ] 基本的なDiscordコマンド実装（/schedule）
- [ ] 手動でのフライト・ホテル情報入力機能
- [ ] タイムライン表示機能

### Phase 3-B: 連携強化

- [ ] スマートチェックリストとの統合
- [ ] スケジュールベースの持ち物調整
- [ ] 早朝便・長時間フライト対応

### Phase 3-C: 自動化

- [ ] JAL予約確認メールパーサー
- [ ] ANA予約確認メールパーサー
- [ ] 主要ホテルサイトのメールパーサー
- [ ] エラーハンドリング・フォールバック

### Phase 3-D: 高度な機能

- [ ] リマインダーサービス実装
- [ ] オンラインチェックイン通知
- [ ] 移動時間の自動計算
- [ ] 交通情報API連携（将来）

## 🔌 既存機能との統合ポイント

### 1. 天気予報連携の活用

```python
# 既存のWeatherServiceを活用
# フライト日時に基づいた天気予報取得
weather_data = await self.weather_service.get_weather_summary(
    destination=flight.arrival_airport,
    start_date=flight.scheduled_arrival.date(),
    end_date=flight.scheduled_arrival.date()
)
```

### 2. GitHub連携の拡張

```python
# 既存のGitHubSyncを活用
# スケジュール情報もMarkdownで保存
await self.github_sync.save_itinerary(
    trip_id=checklist.id,
    itinerary=itinerary
)
```

### 3. 交通手段調整との連携

```python
# 既存のTransportRulesLoaderを活用
# フライト情報から自動的に「airplane」モードで調整
```

## 🚀 今すぐ実行可能なタスク

### 1. データモデルの追加（30分）

```bash
# src/models.pyに新しいモデルを追加
# ITINERARY_INTEGRATION.mdからコピー＆ペースト
```

### 2. テストの作成（1時間）

```python
# tests/unit/test_itinerary_models.py
import pytest
from datetime import datetime
from src.models import FlightInfo, AccommodationInfo, TripItinerary

def test_flight_info_creation():
    flight = FlightInfo(
        flight_number="JAL515",
        airline="JAL",
        departure_airport="HND",
        arrival_airport="CTS",
        scheduled_departure=datetime(2025, 7, 1, 8, 0),
        scheduled_arrival=datetime(2025, 7, 1, 9, 35)
    )
    assert flight.flight_duration.total_seconds() == 5700  # 1時間35分
    assert flight.is_early_morning is True

def test_trip_itinerary_timeline():
    # タイムラインのテスト
    pass
```

### 3. 基本コマンドのスケルトン作成（1時間）

```python
# src/bot/schedule_commands.py
import discord
from discord.ext import commands

class ScheduleCommands(commands.Cog):
    """スケジュール管理コマンド"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    schedule_group = discord.SlashCommandGroup(
        "schedule",
        "移動スケジュールを管理"
    )

    @schedule_group.command(description="スケジュール表示")
    async def view(self, ctx: discord.ApplicationContext):
        await ctx.respond("スケジュール機能は開発中です！")
```

## 📈 期待される成果

### ユーザー価値

- **統合管理**: チェックリストとスケジュールの一元管理
- **自動最適化**: フライト時間に応じた持ち物調整
- **忘れ防止**: タイムリーなリマインダー

### 技術的価値

- **拡張性**: 外部サービス連携の基盤構築
- **学習データ**: より高度な個人最適化への道筋
- **差別化**: 競合にない統合機能

## ⚠️ 注意事項

### 1. 段階的実装の重要性

- 最初は手動入力から始める
- 動作確認しながら機能追加
- ユーザーフィードバックを反映

### 2. 既存機能への影響

- 既存のチェックリスト機能は維持
- オプショナルな機能として追加
- 後方互換性を保つ

### 3. プライバシー配慮

- 予約情報は暗号化保存
- 個人情報の最小限保持
- ユーザー同意の取得

## 📝 次のアクション

1. **この設計書のレビュー**
   - チーム内で実装方針を確認
   - 優先順位の調整

2. **Phase 2の完了**
   - 地域特性調整の実装
   - 期間別最適化の実装

3. **Phase 3-Aの開始**
   - データモデルの実装
   - 基本機能の構築

---

*作成日: 2025-07-01*
*Phase 3実装開始予定: Phase 2完了後*

# 移動スケジュール連携機能 - クイックスタートサンプル

このファイルは、移動スケジュール連携機能をすぐに実装開始するためのサンプルコードです。

## 1. モデル定義のサンプル（src/models.py に追加）

```python
# 追加する型定義
from datetime import timedelta

type FlightStatus = Literal["scheduled", "delayed", "cancelled", "arrived"]
type AccommodationType = Literal["hotel", "ryokan", "airbnb", "friends", "other"]

class FlightInfo(BaseModel):
    """フライト情報（簡易版）."""

    flight_number: str = Field(..., description="便名")
    airline: str = Field(..., description="航空会社")
    departure_airport: str = Field(..., description="出発空港コード")
    arrival_airport: str = Field(..., description="到着空港コード")
    scheduled_departure: datetime = Field(..., description="予定出発時刻")
    scheduled_arrival: datetime = Field(..., description="予定到着時刻")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_early_morning(self) -> bool:
        """早朝便かどうか."""
        return self.scheduled_departure.hour < 8

class AccommodationInfo(BaseModel):
    """宿泊情報（簡易版）."""

    name: str = Field(..., description="宿泊施設名")
    check_in: datetime = Field(..., description="チェックイン時刻")
    check_out: datetime = Field(..., description="チェックアウト時刻")
    address: str = Field(..., description="住所")

# TripChecklistクラスに追加するフィールド
# flights: list[FlightInfo] = Field(default_factory=list, description="フライト情報")
# accommodations: list[AccommodationInfo] = Field(default_factory=list, description="宿泊情報")
```

## 2. 基本的なDiscordコマンド（src/bot/schedule_commands.py）

```python
import discord
from discord.ext import commands
from datetime import datetime

from src.models import FlightInfo, AccommodationInfo
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ScheduleCommands(commands.Cog):
    """スケジュール管理コマンド（簡易版）."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # メモリ内でスケジュール情報を保持（仮実装）
        self.user_schedules = {}

    schedule_group = discord.SlashCommandGroup(
        "schedule",
        "移動スケジュールを管理（開発中）"
    )

    @schedule_group.command(description="フライト情報を手動で追加")
    async def add_flight(
        self,
        ctx: discord.ApplicationContext,
        flight_number: discord.Option(str, "便名（例: JAL515）"),
        departure_date: discord.Option(str, "出発日（YYYY-MM-DD）"),
        departure_time: discord.Option(str, "出発時刻（HH:MM）"),
        departure_airport: discord.Option(str, "出発空港（例: HND）"),
        arrival_airport: discord.Option(str, "到着空港（例: CTS）")
    ):
        """フライト情報を手動で追加（簡易版）."""
        await ctx.defer()

        try:
            # 簡易的な日時パース
            departure_datetime = datetime.strptime(
                f"{departure_date} {departure_time}",
                "%Y-%m-%d %H:%M"
            )

            # フライト情報作成（到着時刻は仮で+1.5時間）
            flight = FlightInfo(
                flight_number=flight_number,
                airline=flight_number[:3],  # 簡易的に便名から推定
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                scheduled_departure=departure_datetime,
                scheduled_arrival=departure_datetime + timedelta(hours=1.5)
            )

            # ユーザーごとに保存
            user_id = str(ctx.user.id)
            if user_id not in self.user_schedules:
                self.user_schedules[user_id] = {"flights": [], "hotels": []}

            self.user_schedules[user_id]["flights"].append(flight)

            # 確認メッセージ
            embed = discord.Embed(
                title="✅ フライト情報を追加しました",
                color=discord.Color.green()
            )
            embed.add_field(
                name="フライト",
                value=flight_number,
                inline=True
            )
            embed.add_field(
                name="出発",
                value=f"{departure_airport} {departure_time}",
                inline=True
            )

            if flight.is_early_morning:
                embed.add_field(
                    name="⚠️ 注意",
                    value="早朝便です。前泊を検討してください。",
                    inline=False
                )

            await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to add flight: {e}")
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}")

    @schedule_group.command(description="現在のスケジュールを表示")
    async def view(self, ctx: discord.ApplicationContext):
        """スケジュールを表示（簡易版）."""
        await ctx.defer()

        user_id = str(ctx.user.id)
        if user_id not in self.user_schedules or not self.user_schedules[user_id]["flights"]:
            await ctx.followup.send("スケジュールが登録されていません。")
            return

        embed = discord.Embed(
            title="📅 あなたの移動スケジュール",
            color=discord.Color.blue()
        )

        # フライト情報表示
        flights = self.user_schedules[user_id]["flights"]
        for i, flight in enumerate(flights, 1):
            embed.add_field(
                name=f"✈️ フライト {i}: {flight.flight_number}",
                value=(
                    f"出発: {flight.departure_airport} "
                    f"{flight.scheduled_departure.strftime('%m/%d %H:%M')}\n"
                    f"到着: {flight.arrival_airport} "
                    f"{flight.scheduled_arrival.strftime('%H:%M')}"
                ),
                inline=False
            )

        await ctx.followup.send(embed=embed)


def setup(bot):
    bot.add_cog(ScheduleCommands(bot))
```

## 3. スマートエンジンへの統合（src/core/smart_engine.py に追加）

```python
# SmartTemplateEngineクラスに追加するメソッド

def _get_flight_adjustments(self, flights: list[FlightInfo]) -> list[ChecklistItem]:
    """フライト情報に基づく調整項目を生成（簡易版）."""
    items = []

    for flight in flights:
        # 早朝便対応
        if flight.is_early_morning:
            items.append(
                ChecklistItem(
                    name="前泊の検討または早朝移動の準備",
                    category="移動関連",
                    auto_added=True,
                    reason=f"{flight.flight_number}が{flight.scheduled_departure.strftime('%H:%M')}出発のため"
                )
            )
            items.append(
                ChecklistItem(
                    name="目覚まし時計（スマホ＋予備）",
                    category="生活用品",
                    auto_added=True,
                    reason="早朝出発対策"
                )
            )

        # 基本的なフライト準備
        items.append(
            ChecklistItem(
                name=f"航空券（{flight.flight_number}）の確認",
                category="移動関連",
                auto_added=True,
                reason="フライト予約確認"
            )
        )

    return items
```

## 4. テストコード（tests/unit/test_itinerary_models.py）

```python
import pytest
from datetime import datetime, timedelta

from src.models import FlightInfo, AccommodationInfo


def test_flight_info_creation():
    """フライト情報の作成テスト."""
    flight = FlightInfo(
        flight_number="JAL515",
        airline="JAL",
        departure_airport="HND",
        arrival_airport="CTS",
        scheduled_departure=datetime(2025, 7, 1, 8, 0),
        scheduled_arrival=datetime(2025, 7, 1, 9, 35)
    )

    assert flight.flight_number == "JAL515"
    assert flight.airline == "JAL"
    assert not flight.is_early_morning  # 8:00は早朝便ではない


def test_early_morning_flight():
    """早朝便の判定テスト."""
    flight = FlightInfo(
        flight_number="ANA123",
        airline="ANA",
        departure_airport="HND",
        arrival_airport="FUK",
        scheduled_departure=datetime(2025, 7, 1, 6, 30),
        scheduled_arrival=datetime(2025, 7, 1, 8, 30)
    )

    assert flight.is_early_morning  # 6:30は早朝便


def test_accommodation_info_creation():
    """宿泊情報の作成テスト."""
    hotel = AccommodationInfo(
        name="札幌グランドホテル",
        check_in=datetime(2025, 7, 1, 15, 0),
        check_out=datetime(2025, 7, 3, 11, 0),
        address="北海道札幌市中央区北1条西4丁目"
    )

    assert hotel.name == "札幌グランドホテル"
    assert hotel.check_in.hour == 15
```

## 5. 実装開始手順

1. **モデルの追加**

   ```bash
   # src/models.py を開いて、FlightInfoとAccommodationInfoクラスを追加
   ```

2. **コマンドファイルの作成**

   ```bash
   touch src/bot/schedule_commands.py
   # 上記のコードをコピー＆ペースト
   ```

3. **main.pyへの統合**

   ```python
   # main.py に追加
   from src.bot.schedule_commands import ScheduleCommands

   # bot setup部分に追加
   bot.add_cog(ScheduleCommands(bot))
   ```

4. **テストの実行**

   ```bash
   pytest tests/unit/test_itinerary_models.py -v
   ```

5. **動作確認**

   ```bash
   python main.py
   # Discordで /schedule add_flight コマンドを試す
   ```

## 注意事項

- このサンプルは最小限の実装です
- データはメモリ内にのみ保存されます（再起動で消失）
- エラーハンドリングは最小限です
- 実際の実装では、GitHub連携やデータベース保存を追加してください

---

これらのサンプルコードを使って、すぐに実装を開始できます。
段階的に機能を追加していくことで、完全な移動スケジュール連携機能を構築できます。

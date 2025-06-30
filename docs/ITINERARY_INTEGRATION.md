# 移動スケジュール連携機能 設計書

## 概要

航空券や宿泊先の予約情報と連携し、統合的な移動スケジュール管理機能を提供する。これはPhase 3の高度な機能として実装する。

## 🎯 機能要件

### 1. 予約情報の自動取得

- 航空会社の予約確認番号から自動取得
- ホテル予約確認メールの解析
- 主要予約サイトとの連携

### 2. 統合スケジュール管理

- タイムライン形式での旅程表示
- 移動時間の自動計算
- アラート・リマインダー機能

### 3. スマートチェックリスト連携

- スケジュールに基づく持ち物の自動調整
- 早朝便対応（前泊提案など）
- 乗り継ぎ時間による注意喚起

## 📋 実装計画

### Phase 3-A: データモデル拡張（1週間）

#### 1. 新しいモデル定義

```python
# src/models.py に追加

from datetime import time

type FlightStatus = Literal["scheduled", "delayed", "cancelled", "arrived"]
type AccommodationType = Literal["hotel", "ryokan", "airbnb", "friends", "other"]

class FlightInfo(BaseModel):
    """フライト情報."""

    flight_number: str = Field(..., description="便名")
    airline: str = Field(..., description="航空会社")
    departure_airport: str = Field(..., description="出発空港コード")
    arrival_airport: str = Field(..., description="到着空港コード")
    scheduled_departure: datetime = Field(..., description="予定出発時刻")
    scheduled_arrival: datetime = Field(..., description="予定到着時刻")
    actual_departure: datetime | None = Field(default=None, description="実際の出発時刻")
    actual_arrival: datetime | None = Field(default=None, description="実際の到着時刻")
    terminal: str | None = Field(default=None, description="ターミナル")
    gate: str | None = Field(default=None, description="搭乗ゲート")
    seat: str | None = Field(default=None, description="座席番号")
    confirmation_code: str | None = Field(default=None, description="予約確認番号")
    status: FlightStatus = Field(default="scheduled", description="フライト状態")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def flight_duration(self) -> timedelta:
        """フライト時間を計算."""
        return self.scheduled_arrival - self.scheduled_departure

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_early_morning(self) -> bool:
        """早朝便かどうか."""
        return self.scheduled_departure.hour < 8

class AccommodationInfo(BaseModel):
    """宿泊情報."""

    name: str = Field(..., description="宿泊施設名")
    type: AccommodationType = Field(..., description="宿泊タイプ")
    check_in: datetime = Field(..., description="チェックイン時刻")
    check_out: datetime = Field(..., description="チェックアウト時刻")
    address: str = Field(..., description="住所")
    phone: str | None = Field(default=None, description="電話番号")
    confirmation_code: str | None = Field(default=None, description="予約確認番号")
    notes: str | None = Field(default=None, description="備考")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nights(self) -> int:
        """宿泊日数."""
        return (self.check_out.date() - self.check_in.date()).days

class TransportSegment(BaseModel):
    """移動区間情報."""

    type: TransportMethod = Field(..., description="交通手段")
    provider: str | None = Field(default=None, description="運行会社")
    from_location: str = Field(..., description="出発地")
    to_location: str = Field(..., description="到着地")
    departure_time: datetime = Field(..., description="出発時刻")
    arrival_time: datetime = Field(..., description="到着時刻")
    reservation_required: bool = Field(default=False, description="予約必須かどうか")
    confirmation_code: str | None = Field(default=None, description="予約確認番号")

class Meeting(BaseModel):
    """会議・イベント情報."""

    title: str = Field(..., description="タイトル")
    location: str = Field(..., description="場所")
    start_time: datetime = Field(..., description="開始時刻")
    end_time: datetime = Field(..., description="終了時刻")
    attendees: list[str] = Field(default_factory=list, description="参加者")
    notes: str | None = Field(default=None, description="備考")

class TripItinerary(BaseModel):
    """旅行行程."""

    trip_id: str = Field(..., description="旅行ID")
    flights: list[FlightInfo] = Field(default_factory=list, description="フライト情報")
    accommodations: list[AccommodationInfo] = Field(default_factory=list, description="宿泊情報")
    transport_segments: list[TransportSegment] = Field(default_factory=list, description="その他の移動")
    meetings: list[Meeting] = Field(default_factory=list, description="会議・イベント")
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def timeline_events(self) -> list[tuple[datetime, str, str]]:
        """時系列でイベントを整理."""
        events = []

        # フライト
        for flight in self.flights:
            events.append((
                flight.scheduled_departure,
                "flight_departure",
                f"✈️ {flight.flight_number} 出発"
            ))
            events.append((
                flight.scheduled_arrival,
                "flight_arrival",
                f"🛬 {flight.arrival_airport} 到着"
            ))

        # 宿泊
        for hotel in self.accommodations:
            events.append((
                hotel.check_in,
                "hotel_checkin",
                f"🏨 {hotel.name} チェックイン"
            ))
            events.append((
                hotel.check_out,
                "hotel_checkout",
                f"🏨 {hotel.name} チェックアウト"
            ))

        # その他の移動
        for transport in self.transport_segments:
            events.append((
                transport.departure_time,
                "transport",
                f"🚃 {transport.from_location} → {transport.to_location}"
            ))

        # 会議
        for meeting in self.meetings:
            events.append((
                meeting.start_time,
                "meeting",
                f"📅 {meeting.title}"
            ))

        # 時刻順にソート
        return sorted(events, key=lambda x: x[0])

# TripChecklistクラスに追加
class TripChecklist(BaseModel):
    # 既存のフィールド...

    itinerary: TripItinerary | None = Field(default=None, description="旅行行程")
```

### Phase 3-B: 予約情報パーサー実装（2週間）

#### 1. 予約情報パーサー

```python
# src/core/booking_parser.py

import re
from abc import ABC, abstractmethod
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

from src.models import AccommodationInfo, FlightInfo
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class BookingParser(ABC):
    """予約情報パーサーの基底クラス."""

    @abstractmethod
    async def parse(self, content: str) -> Any:
        """予約情報を解析."""
        pass


class JALBookingParser(BookingParser):
    """JAL予約確認メールパーサー."""

    async def parse(self, content: str) -> list[FlightInfo]:
        """JALの予約確認メールを解析."""
        flights = []

        # 便名パターン
        flight_pattern = r"JAL(\d+)"
        # 日時パターン
        datetime_pattern = r"(\d{4}年\d{1,2}月\d{1,2}日).*?(\d{2}:\d{2})"
        # 空港パターン
        airport_pattern = r"(羽田|成田|関西|中部|新千歳|福岡|那覇)"

        # 解析ロジック（簡略版）
        # 実際の実装では、より詳細なパターンマッチングが必要

        return flights


class ANABookingParser(BookingParser):
    """ANA予約確認メールパーサー."""

    async def parse(self, content: str) -> list[FlightInfo]:
        """ANAの予約確認メールを解析."""
        # 実装
        pass


class HotelBookingParser(BookingParser):
    """ホテル予約確認メールパーサー."""

    PARSERS = {
        "booking.com": "parse_booking_com",
        "楽天トラベル": "parse_rakuten",
        "じゃらん": "parse_jalan",
        "一休.com": "parse_ikyu"
    }

    async def parse(self, content: str) -> AccommodationInfo:
        """ホテル予約確認メールを解析."""
        # 予約サイトを判定
        for site, method_name in self.PARSERS.items():
            if site in content:
                method = getattr(self, method_name, None)
                if method:
                    return await method(content)

        raise ValueError("対応していない予約サイトです")

    async def parse_booking_com(self, content: str) -> AccommodationInfo:
        """Booking.comの予約確認を解析."""
        # 実装
        pass


class BookingService:
    """予約情報を統合的に管理するサービス."""

    def __init__(self):
        self.flight_parsers = {
            "JAL": JALBookingParser(),
            "ANA": ANABookingParser(),
            # 他の航空会社
        }
        self.hotel_parser = HotelBookingParser()

    async def parse_confirmation_email(
        self,
        email_content: str,
        email_type: Literal["flight", "hotel"]
    ) -> FlightInfo | AccommodationInfo:
        """確認メールを解析."""
        if email_type == "flight":
            # 航空会社を判定
            for airline, parser in self.flight_parsers.items():
                if airline in email_content:
                    return await parser.parse(email_content)
        else:
            return await self.hotel_parser.parse(email_content)

    async def fetch_by_confirmation_code(
        self,
        confirmation_code: str,
        provider: str
    ) -> FlightInfo | AccommodationInfo | None:
        """確認番号から予約情報を取得（将来実装）."""
        # 各社のAPIを使用（利用可能な場合）
        logger.info(f"Fetching booking info: {confirmation_code} from {provider}")
        # 実装予定
        return None
```

### Phase 3-C: スケジュール連携機能（2週間）

#### 1. Discord コマンド拡張

```python
# src/bot/schedule_commands.py

import discord
from discord.ext import commands

from src.core.booking_parser import BookingService
from src.core.smart_engine import SmartTemplateEngine
from src.models import TripItinerary
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ScheduleCommands(commands.Cog):
    """スケジュール管理コマンド."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.booking_service = BookingService()
        self.smart_engine = SmartTemplateEngine()

    schedule_group = discord.SlashCommandGroup(
        "schedule",
        "移動スケジュールを管理"
    )

    @schedule_group.command(description="フライト情報を追加")
    async def add_flight(
        self,
        ctx: discord.ApplicationContext,
        confirmation_code: discord.Option(str, "予約確認番号"),
        airline: discord.Option(
            str,
            "航空会社",
            choices=["JAL", "ANA", "その他"]
        )
    ):
        """フライト情報を追加."""
        await ctx.defer()

        try:
            # メールの転送を促す
            embed = discord.Embed(
                title="📧 予約確認メールを転送してください",
                description=(
                    f"確認番号: **{confirmation_code}**\n"
                    f"航空会社: **{airline}**\n\n"
                    "予約確認メールの内容をコピーして、"
                    "次のメッセージで送信してください。"
                ),
                color=discord.Color.blue()
            )

            await ctx.followup.send(embed=embed)

            # ユーザーの次のメッセージを待つ
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            message = await self.bot.wait_for("message", check=check, timeout=300.0)

            # メールを解析
            flight_info = await self.booking_service.parse_confirmation_email(
                message.content,
                email_type="flight"
            )

            # 成功メッセージ
            success_embed = discord.Embed(
                title="✅ フライト情報を追加しました",
                color=discord.Color.green()
            )
            success_embed.add_field(
                name="フライト",
                value=f"{flight_info.flight_number}",
                inline=True
            )
            success_embed.add_field(
                name="出発",
                value=f"{flight_info.scheduled_departure.strftime('%m/%d %H:%M')}",
                inline=True
            )

            await ctx.followup.send(embed=success_embed)

        except asyncio.TimeoutError:
            await ctx.followup.send("⏱️ タイムアウトしました。もう一度お試しください。")
        except Exception as e:
            logger.error(f"Failed to add flight: {e}")
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}")

    @schedule_group.command(description="スケジュール表示")
    async def view(
        self,
        ctx: discord.ApplicationContext,
        trip_id: discord.Option(str, "旅行ID", required=False)
    ):
        """統合スケジュールを表示."""
        await ctx.defer()

        # TODO: trip_idから行程を取得
        itinerary = await self._get_itinerary(trip_id or "current")

        if not itinerary:
            await ctx.followup.send("スケジュールが見つかりません。")
            return

        # タイムライン表示
        embed = self._create_timeline_embed(itinerary)
        await ctx.followup.send(embed=embed)

    def _create_timeline_embed(self, itinerary: TripItinerary) -> discord.Embed:
        """タイムライン形式のEmbed作成."""
        embed = discord.Embed(
            title="📅 移動スケジュール",
            color=discord.Color.green()
        )

        # 日付ごとにグループ化
        events_by_date = {}
        for timestamp, event_type, description in itinerary.timeline_events:
            date_key = timestamp.date()
            if date_key not in events_by_date:
                events_by_date[date_key] = []
            events_by_date[date_key].append((timestamp, event_type, description))

        # 各日付のイベントを表示
        for date, events in events_by_date.items():
            timeline_text = "```\n"
            for timestamp, event_type, description in events:
                time_str = timestamp.strftime("%H:%M")
                timeline_text += f"{time_str} {description}\n"
            timeline_text += "```"

            embed.add_field(
                name=f"📆 {date.strftime('%m月%d日（%a）')}",
                value=timeline_text,
                inline=False
            )

        # 注意事項
        warnings = self._check_schedule_warnings(itinerary)
        if warnings:
            embed.add_field(
                name="⚠️ 注意事項",
                value="\n".join(warnings),
                inline=False
            )

        return embed

    def _check_schedule_warnings(self, itinerary: TripItinerary) -> list[str]:
        """スケジュールの注意事項をチェック."""
        warnings = []

        for flight in itinerary.flights:
            if flight.is_early_morning:
                warnings.append(
                    f"早朝便です（{flight.flight_number} "
                    f"{flight.scheduled_departure.strftime('%H:%M')}出発）"
                )

        # 乗り継ぎ時間チェック
        # タイトなスケジュールチェック
        # etc...

        return warnings
```

#### 2. スマートチェックリストとの統合

```python
# src/core/smart_engine.py に追加

class ScheduleAwareSmartEngine(SmartTemplateEngine):
    """スケジュール情報を考慮したスマートエンジン."""

    async def generate_checklist_with_schedule(
        self,
        request: TripRequest,
        itinerary: TripItinerary | None
    ) -> TripChecklist:
        """スケジュールを考慮したチェックリスト生成."""
        # 基本のチェックリスト生成
        checklist = await self.generate_checklist(request)

        if itinerary:
            # スケジュールベースの調整
            schedule_items = self._get_schedule_adjustments(itinerary)
            checklist.items.extend(schedule_items)
            checklist.itinerary = itinerary

        return checklist

    def _get_schedule_adjustments(
        self,
        itinerary: TripItinerary
    ) -> list[ChecklistItem]:
        """スケジュールに基づく調整項目."""
        items = []

        # 早朝便チェック
        for flight in itinerary.flights:
            if flight.is_early_morning:
                items.extend([
                    ChecklistItem(
                        name="前泊の検討（または空港近くのホテル）",
                        category="移動関連",
                        auto_added=True,
                        reason=f"{flight.scheduled_departure.strftime('%H:%M')}出発のため"
                    ),
                    ChecklistItem(
                        name="目覚まし時計（複数セット）",
                        category="生活用品",
                        auto_added=True,
                        reason="早朝出発対策"
                    ),
                    ChecklistItem(
                        name="前日の早めの就寝",
                        category="移動関連",
                        auto_added=True,
                        reason="早朝フライトのため"
                    )
                ])

            # 長時間フライト
            if flight.flight_duration.total_seconds() > 3 * 3600:  # 3時間以上
                items.extend([
                    ChecklistItem(
                        name="フライト用快適グッズ（ネックピロー等）",
                        category="移動関連",
                        auto_added=True,
                        reason=f"{flight.flight_duration.total_seconds() / 3600:.1f}時間のフライト"
                    ),
                    ChecklistItem(
                        name="機内エンターテイメント（本・タブレット等）",
                        category="生活用品",
                        auto_added=True,
                        reason="長時間フライト対策"
                    )
                ])

        # ホテル関連
        for hotel in itinerary.accommodations:
            # レイトチェックアウト
            if hotel.check_out.hour >= 12:
                items.append(
                    ChecklistItem(
                        name="レイトチェックアウトの確認",
                        category="移動関連",
                        auto_added=True,
                        reason=f"{hotel.check_out.strftime('%H:%M')}チェックアウト"
                    )
                )

        # 移動時間の計算
        events = itinerary.timeline_events
        for i in range(len(events) - 1):
            current_event = events[i]
            next_event = events[i + 1]

            # イベント間の時間が短い場合
            time_diff = (next_event[0] - current_event[0]).total_seconds() / 60
            if time_diff < 60:  # 60分未満
                items.append(
                    ChecklistItem(
                        name=f"{current_event[2]}から{next_event[2]}への移動時間確認",
                        category="移動関連",
                        auto_added=True,
                        reason=f"移動時間が{int(time_diff)}分しかありません"
                    )
                )

        return items
```

### Phase 3-D: リマインダー機能（1週間）

#### 1. リマインダーサービス

```python
# src/core/reminder_service.py

import asyncio
from datetime import datetime, timedelta
from typing import Any

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.models import TripChecklist, TripItinerary
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ReminderService:
    """リマインダーサービス."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.reminders: dict[str, list[str]] = {}  # user_id -> job_ids

    async def schedule_trip_reminders(
        self,
        user_id: str,
        checklist: TripChecklist,
        channel_id: int
    ):
        """旅行関連のリマインダーを設定."""
        # 既存のリマインダーをクリア
        await self.clear_user_reminders(user_id)

        reminders = []

        # チェックリストリマインダー
        reminders.extend(self._create_checklist_reminders(checklist))

        # スケジュールリマインダー
        if checklist.itinerary:
            reminders.extend(self._create_schedule_reminders(checklist.itinerary))

        # リマインダーをスケジュール
        job_ids = []
        for reminder in reminders:
            if reminder["time"] > datetime.now():
                job = self.scheduler.add_job(
                    self._send_reminder,
                    "date",
                    run_date=reminder["time"],
                    args=[user_id, channel_id, reminder["message"], reminder.get("action")]
                )
                job_ids.append(job.id)

        self.reminders[user_id] = job_ids
        logger.info(f"Scheduled {len(job_ids)} reminders for user {user_id}")

    def _create_checklist_reminders(
        self,
        checklist: TripChecklist
    ) -> list[dict[str, Any]]:
        """チェックリスト関連のリマインダー."""
        reminders = []

        # 出発3日前
        three_days_before = checklist.start_date - timedelta(days=3)
        reminders.append({
            "time": datetime.combine(three_days_before, datetime.min.time()).replace(hour=20),
            "message": "🧳 出発まであと3日です！チェックリストを確認しましょう。",
            "action": "show_checklist"
        })

        # 出発前日
        one_day_before = checklist.start_date - timedelta(days=1)
        reminders.append({
            "time": datetime.combine(one_day_before, datetime.min.time()).replace(hour=20),
            "message": "📋 明日出発です！最終確認をしましょう。",
            "action": "show_pending_items"
        })

        # 出発当日朝
        reminders.append({
            "time": datetime.combine(checklist.start_date, datetime.min.time()).replace(hour=7),
            "message": "🌅 出発日です！忘れ物はありませんか？",
            "action": "final_check"
        })

        return reminders

    def _create_schedule_reminders(
        self,
        itinerary: TripItinerary
    ) -> list[dict[str, Any]]:
        """スケジュール関連のリマインダー."""
        reminders = []

        for flight in itinerary.flights:
            # オンラインチェックイン（24時間前）
            checkin_time = flight.scheduled_departure - timedelta(hours=24)
            reminders.append({
                "time": checkin_time,
                "message": f"✈️ {flight.flight_number}のオンラインチェックインが可能です！",
                "action": "online_checkin"
            })

            # 出発準備（3時間前）
            prep_time = flight.scheduled_departure - timedelta(hours=3)
            reminders.append({
                "time": prep_time,
                "message": f"🚗 空港への出発準備を始めましょう（{flight.flight_number}）",
                "action": "departure_prep"
            })

            # 早朝便特別リマインダー
            if flight.is_early_morning:
                wake_time = flight.scheduled_departure - timedelta(hours=4)
                reminders.append({
                    "time": wake_time,
                    "message": f"⏰ 早朝便です！起床時刻です（{flight.flight_number}）",
                    "action": "wake_up"
                })

        for hotel in itinerary.accommodations:
            # チェックアウトリマインダー（1時間前）
            checkout_reminder = hotel.check_out - timedelta(hours=1)
            reminders.append({
                "time": checkout_reminder,
                "message": f"🏨 {hotel.name}のチェックアウトまであと1時間です",
                "action": None
            })

        return reminders

    async def _send_reminder(
        self,
        user_id: str,
        channel_id: int,
        message: str,
        action: str | None
    ):
        """リマインダーを送信."""
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return

            user = self.bot.get_user(int(user_id))
            if not user:
                logger.error(f"User {user_id} not found")
                return

            # Embedでリマインダーを送信
            embed = discord.Embed(
                title="🔔 リマインダー",
                description=message,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )

            # アクション付きの場合はボタンを追加
            view = None
            if action:
                view = ReminderActionView(action, user_id)

            await channel.send(
                content=f"{user.mention}",
                embed=embed,
                view=view
            )

        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")

    async def clear_user_reminders(self, user_id: str):
        """ユーザーのリマインダーをクリア."""
        if user_id in self.reminders:
            for job_id in self.reminders[user_id]:
                self.scheduler.remove_job(job_id)
            del self.reminders[user_id]


class ReminderActionView(discord.ui.View):
    """リマインダーアクション用のView."""

    def __init__(self, action: str, user_id: str):
        super().__init__(timeout=3600)  # 1時間
        self.action = action
        self.user_id = user_id

        # アクションに応じたボタンを追加
        if action == "show_checklist":
            self.add_item(
                discord.ui.Button(
                    label="チェックリストを表示",
                    style=discord.ButtonStyle.primary,
                    custom_id="show_checklist"
                )
            )
        elif action == "online_checkin":
            self.add_item(
                discord.ui.Button(
                    label="チェックイン手順を表示",
                    style=discord.ButtonStyle.success,
                    custom_id="checkin_guide"
                )
            )
```

## 🔧 実装の統合方法

### 1. 既存コードへの統合

```python
# main.py の修正

from src.bot.schedule_commands import ScheduleCommands
from src.core.reminder_service import ReminderService

def main():
    # 既存のコード...

    # リマインダーサービスの初期化
    reminder_service = ReminderService(bot)

    # 新しいコマンドグループを追加
    bot.add_cog(ScheduleCommands(bot))

    # リマインダーサービスをbotに登録
    bot.reminder_service = reminder_service

    # 既存のコード...
```

### 2. 設定ファイルの更新

```yaml
# src/config/settings.yaml に追加

features:
  weather: true
  github_sync: true
  schedule_integration: true  # 新機能
  reminders: true  # 新機能

# 対応する予約サイト・航空会社
supported_providers:
  airlines:
    - JAL
    - ANA
    - Peach
    - Jetstar
    - Skymark
  hotels:
    - booking.com
    - 楽天トラベル
    - じゃらん
    - 一休.com
```

## 📊 実装優先順位とロードマップ

### Phase 3-A: 基礎実装（2週間）

1. データモデルの拡張
2. 基本的なスケジュール表示機能
3. 手動でのフライト・ホテル情報入力

### Phase 3-B: 自動取得（3週間）

1. メールパーサーの実装
2. 主要航空会社対応
3. 主要予約サイト対応

### Phase 3-C: 統合機能（2週間）

1. スマートチェックリストとの連携
2. スケジュールベースの自動調整
3. リマインダー機能

### Phase 3-D: 高度な機能（1週間）

1. 交通情報API連携
2. 遅延・変更通知
3. 代替ルート提案

## 🎯 期待される効果

### ユーザーメリット

- **統合管理**: 予約情報とチェックリストの一元管理
- **自動調整**: スケジュールに基づく最適な持ち物提案
- **忘れ防止**: タイムリーなリマインダー
- **ストレス軽減**: 移動の不安を解消

### システムメリット

- **差別化**: 他にない統合的な旅行管理システム
- **拡張性**: 将来的な外部サービス連携の基盤
- **学習データ**: より精度の高い個人最適化

## ⚠️ 技術的課題と対策

### 課題

1. **メール解析の複雑性**: 各社フォーマットが異なる
2. **APIアクセス**: 公式APIが限定的
3. **プライバシー**: 予約情報の取り扱い

### 対策

1. **段階的実装**: 主要サービスから順次対応
2. **フォールバック**: 手動入力オプションを常に提供
3. **暗号化**: 機密情報の適切な管理

## 📝 テスト計画

### ユニットテスト

```python
# tests/unit/test_booking_parser.py

import pytest
from src.core.booking_parser import JALBookingParser

@pytest.mark.asyncio
async def test_jal_parser():
    """JALパーサーのテスト."""
    parser = JALBookingParser()
    sample_email = """
    JAL予約確認
    便名: JAL515
    出発: 2025年7月1日 08:00 羽田空港
    到着: 2025年7月1日 09:35 新千歳空港
    """

    flights = await parser.parse(sample_email)
    assert len(flights) == 1
    assert flights[0].flight_number == "JAL515"
```

### 統合テスト

- エンドツーエンドのフロー確認
- Discord UIでの動作確認
- リマインダーの送信テスト

## 🚀 次のステップ

1. **即実装可能**
   - データモデルの定義
   - 基本的なスケジュール表示

2. **段階的実装**
   - JAL/ANAパーサー実装
   - 主要ホテルサイト対応

3. **将来拡張**
   - Google Calendar連携
   - Apple Wallet連携
   - 交通系ICカード残高確認

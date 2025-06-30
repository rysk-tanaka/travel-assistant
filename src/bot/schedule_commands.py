"""
Discord bot commands for schedule management.

スケジュール管理関連のDiscordコマンドを定義します。
"""

from __future__ import annotations

from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from src.models import (
    AccommodationInfo,
    FlightInfo,
    Meeting,
    TripItinerary,
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ScheduleCommands(commands.Cog):
    """スケジュール管理関連のコマンド."""

    def __init__(self, bot: commands.Bot):
        """初期化."""
        self.bot = bot
        # 旅行行程を一時的に保存（本来はDBやRedisを使用）
        self.itineraries: dict[str, TripItinerary] = {}
        logger.info("ScheduleCommands cog initialized")

    @app_commands.command(name="schedule", description="旅行スケジュールを管理します")
    @app_commands.describe(
        action="実行するアクション (add_flight/add_hotel/add_meeting/show/clear)"
    )
    async def schedule(self, interaction: discord.Interaction, action: str) -> None:
        """スケジュール管理のメインコマンド."""
        if action == "add_flight":
            await self._handle_add_flight(interaction)
        elif action == "add_hotel":
            await self._handle_add_hotel(interaction)
        elif action == "add_meeting":
            await self._handle_add_meeting(interaction)
        elif action == "show":
            await self._handle_show_schedule(interaction)
        elif action == "clear":
            await self._handle_clear_schedule(interaction)
        else:
            await interaction.response.send_message(
                "❌ 無効なアクションです。"
                "add_flight, add_hotel, add_meeting, show, clear のいずれかを指定してください。",
                ephemeral=True,
            )

    async def _handle_add_flight(self, interaction: discord.Interaction) -> None:
        """フライト情報追加のハンドラー."""
        # モーダルでフライト情報を入力
        modal = FlightInputModal(self)
        await interaction.response.send_modal(modal)

    async def _handle_add_hotel(self, interaction: discord.Interaction) -> None:
        """宿泊情報追加のハンドラー."""
        # モーダルでホテル情報を入力
        modal = HotelInputModal(self)
        await interaction.response.send_modal(modal)

    async def _handle_add_meeting(self, interaction: discord.Interaction) -> None:
        """会議情報追加のハンドラー."""
        # モーダルで会議情報を入力
        modal = MeetingInputModal(self)
        await interaction.response.send_modal(modal)

    async def _handle_show_schedule(self, interaction: discord.Interaction) -> None:
        """スケジュール表示のハンドラー."""
        user_id = str(interaction.user.id)
        trip_id = f"{user_id}_current"  # 簡易的な実装

        if trip_id not in self.itineraries:
            await interaction.response.send_message(
                "📅 まだスケジュールが登録されていません。", ephemeral=True
            )
            return

        itinerary = self.itineraries[trip_id]
        embed = self._create_schedule_embed(itinerary)
        await interaction.response.send_message(embed=embed)

    async def _handle_clear_schedule(self, interaction: discord.Interaction) -> None:
        """スケジュールクリアのハンドラー."""
        user_id = str(interaction.user.id)
        trip_id = f"{user_id}_current"

        if trip_id in self.itineraries:
            del self.itineraries[trip_id]
            await interaction.response.send_message(
                "✅ スケジュールをクリアしました。", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "📅 クリアするスケジュールがありません。", ephemeral=True
            )

    def _create_schedule_embed(self, itinerary: TripItinerary) -> discord.Embed:
        """スケジュール表示用のEmbed作成."""
        embed = discord.Embed(
            title="🗓️ 旅行スケジュール",
            description=f"旅行ID: {itinerary.trip_id}",
            color=discord.Color.blue(),
            timestamp=datetime.now(),
        )

        # タイムライン表示
        timeline_events = itinerary.timeline_events
        if timeline_events:
            timeline_text = ""
            for event_time, _event_type, event_desc in timeline_events[:10]:  # 最大10件
                time_str = event_time.strftime("%m/%d %H:%M")
                timeline_text += f"**{time_str}** {event_desc}\n"

            if len(timeline_events) > 10:
                timeline_text += f"\n... 他 {len(timeline_events) - 10} 件のイベント"

            embed.add_field(
                name="📋 タイムライン", value=timeline_text or "イベントなし", inline=False
            )

        # フライト情報
        if itinerary.flights:
            flight_text = ""
            for flight in itinerary.flights[:3]:
                flight_text += (
                    f"✈️ **{flight.flight_number}** ({flight.airline})\n"
                    f"   {flight.departure_airport} → {flight.arrival_airport}\n"
                    f"   {flight.scheduled_departure.strftime('%m/%d %H:%M')}\n"
                )
            embed.add_field(name="✈️ フライト", value=flight_text, inline=True)

        # 宿泊情報
        if itinerary.accommodations:
            hotel_text = ""
            for hotel in itinerary.accommodations[:3]:
                hotel_text += (
                    f"🏨 **{hotel.name}**\n"
                    f"   {hotel.nights}泊\n"
                    f"   {hotel.check_in.strftime('%m/%d')} - {hotel.check_out.strftime('%m/%d')}\n"
                )
            embed.add_field(name="🏨 宿泊", value=hotel_text, inline=True)

        # 会議情報
        if itinerary.meetings:
            meeting_text = ""
            for meeting in itinerary.meetings[:3]:
                meeting_text += (
                    f"📅 **{meeting.title}**\n"
                    f"   {meeting.location}\n"
                    f"   {meeting.start_time.strftime('%m/%d %H:%M')}\n"
                )
            embed.add_field(name="📅 会議・イベント", value=meeting_text, inline=True)

        embed.set_footer(text="💡 /schedule add_flight などで情報を追加できます")

        return embed

    def get_or_create_itinerary(self, user_id: str) -> TripItinerary:
        """ユーザーの現在の旅行行程を取得または作成."""
        trip_id = f"{user_id}_current"
        if trip_id not in self.itineraries:
            self.itineraries[trip_id] = TripItinerary(trip_id=trip_id)
        return self.itineraries[trip_id]


# モーダルクラス
class FlightInputModal(discord.ui.Modal, title="フライト情報を入力"):
    """フライト情報入力用モーダル."""

    def __init__(self, cog: ScheduleCommands):
        """初期化."""
        super().__init__()
        self.cog = cog

    flight_number: discord.ui.TextInput[FlightInputModal] = discord.ui.TextInput(
        label="便名", placeholder="例: JAL515", required=True, max_length=20
    )

    airline: discord.ui.TextInput[FlightInputModal] = discord.ui.TextInput(
        label="航空会社", placeholder="例: JAL", required=True, max_length=30
    )

    airports: discord.ui.TextInput[FlightInputModal] = discord.ui.TextInput(
        label="出発空港 → 到着空港", placeholder="例: HND → CTS", required=True, max_length=20
    )

    departure_time: discord.ui.TextInput[FlightInputModal] = discord.ui.TextInput(
        label="出発時刻", placeholder="例: 2025-07-01 08:00", required=True, max_length=20
    )

    arrival_time: discord.ui.TextInput[FlightInputModal] = discord.ui.TextInput(
        label="到着時刻", placeholder="例: 2025-07-01 09:35", required=True, max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """送信時の処理."""
        try:
            # 空港コードを分割
            airports_parts = self.airports.value.replace("→", "->").split("->")
            if len(airports_parts) != 2:
                raise ValueError("出発空港と到着空港を → で区切って入力してください")

            departure_airport = airports_parts[0].strip()
            arrival_airport = airports_parts[1].strip()

            # 時刻をパース
            departure_dt = datetime.strptime(self.departure_time.value, "%Y-%m-%d %H:%M")
            arrival_dt = datetime.strptime(self.arrival_time.value, "%Y-%m-%d %H:%M")

            # フライト情報を作成
            flight = FlightInfo(
                flight_number=self.flight_number.value,
                airline=self.airline.value,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                scheduled_departure=departure_dt,
                scheduled_arrival=arrival_dt,
            )

            # 旅行行程に追加
            user_id = str(interaction.user.id)
            itinerary = self.cog.get_or_create_itinerary(user_id)
            itinerary.flights.append(flight)

            await interaction.response.send_message(
                f"✅ フライト {flight.flight_number} を追加しました！", ephemeral=True
            )

        except ValueError as e:
            await interaction.response.send_message(f"❌ エラー: {e!s}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error adding flight: {e}")
            await interaction.response.send_message(
                "❌ フライト情報の追加中にエラーが発生しました。", ephemeral=True
            )


class HotelInputModal(discord.ui.Modal, title="宿泊情報を入力"):
    """宿泊情報入力用モーダル."""

    def __init__(self, cog: ScheduleCommands):
        """初期化."""
        super().__init__()
        self.cog = cog

    hotel_name: discord.ui.TextInput[HotelInputModal] = discord.ui.TextInput(
        label="宿泊施設名", placeholder="例: 札幌グランドホテル", required=True, max_length=100
    )

    hotel_type: discord.ui.TextInput[HotelInputModal] = discord.ui.TextInput(
        label="宿泊タイプ",
        placeholder="hotel/ryokan/airbnb/friends/other",
        required=True,
        default="hotel",
        max_length=20,
    )

    check_in: discord.ui.TextInput[HotelInputModal] = discord.ui.TextInput(
        label="チェックイン日時", placeholder="例: 2025-07-01 15:00", required=True, max_length=20
    )

    check_out: discord.ui.TextInput[HotelInputModal] = discord.ui.TextInput(
        label="チェックアウト日時", placeholder="例: 2025-07-03 11:00", required=True, max_length=20
    )

    address: discord.ui.TextInput[HotelInputModal] = discord.ui.TextInput(
        label="住所", placeholder="例: 札幌市中央区北1条西4丁目", required=True, max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """送信時の処理."""
        try:
            # 時刻をパース
            check_in_dt = datetime.strptime(self.check_in.value, "%Y-%m-%d %H:%M")
            check_out_dt = datetime.strptime(self.check_out.value, "%Y-%m-%d %H:%M")

            # 宿泊タイプのバリデーション
            valid_types = {"hotel", "ryokan", "airbnb", "friends", "other"}
            hotel_type = self.hotel_type.value.lower()
            if hotel_type not in valid_types:
                raise ValueError(
                    f"宿泊タイプは {', '.join(valid_types)} のいずれかを指定してください"
                )

            # 宿泊情報を作成
            hotel = AccommodationInfo(
                name=self.hotel_name.value,
                type=hotel_type,  # type: ignore[arg-type]
                check_in=check_in_dt,
                check_out=check_out_dt,
                address=self.address.value,
            )

            # 旅行行程に追加
            user_id = str(interaction.user.id)
            itinerary = self.cog.get_or_create_itinerary(user_id)
            itinerary.accommodations.append(hotel)

            await interaction.response.send_message(
                f"✅ 宿泊施設 {hotel.name} を追加しました！（{hotel.nights}泊）", ephemeral=True
            )

        except ValueError as e:
            await interaction.response.send_message(f"❌ エラー: {e!s}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error adding hotel: {e}")
            await interaction.response.send_message(
                "❌ 宿泊情報の追加中にエラーが発生しました。", ephemeral=True
            )


class MeetingInputModal(discord.ui.Modal, title="会議・イベント情報を入力"):
    """会議情報入力用モーダル."""

    def __init__(self, cog: ScheduleCommands):
        """初期化."""
        super().__init__()
        self.cog = cog

    meeting_title: discord.ui.TextInput[MeetingInputModal] = discord.ui.TextInput(
        label="タイトル",
        placeholder="例: プロジェクトキックオフ会議",
        required=True,
        max_length=100,
    )

    location: discord.ui.TextInput[MeetingInputModal] = discord.ui.TextInput(
        label="場所", placeholder="例: 札幌オフィス 会議室A", required=True, max_length=100
    )

    start_time: discord.ui.TextInput[MeetingInputModal] = discord.ui.TextInput(
        label="開始時刻", placeholder="例: 2025-07-02 10:00", required=True, max_length=20
    )

    end_time: discord.ui.TextInput[MeetingInputModal] = discord.ui.TextInput(
        label="終了時刻", placeholder="例: 2025-07-02 12:00", required=True, max_length=20
    )

    attendees: discord.ui.TextInput[MeetingInputModal] = discord.ui.TextInput(
        label="参加者（カンマ区切り）",
        placeholder="例: 田中, 佐藤, 鈴木",
        required=False,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """送信時の処理."""
        try:
            # 時刻をパース
            start_dt = datetime.strptime(self.start_time.value, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(self.end_time.value, "%Y-%m-%d %H:%M")

            # 参加者リストを作成
            attendees_list = []
            if self.attendees.value:
                attendees_list = [a.strip() for a in self.attendees.value.split(",")]

            # 会議情報を作成
            meeting = Meeting(
                title=self.meeting_title.value,
                location=self.location.value,
                start_time=start_dt,
                end_time=end_dt,
                attendees=attendees_list,
            )

            # 旅行行程に追加
            user_id = str(interaction.user.id)
            itinerary = self.cog.get_or_create_itinerary(user_id)
            itinerary.meetings.append(meeting)

            await interaction.response.send_message(
                f"✅ 会議 「{meeting.title}」 を追加しました！", ephemeral=True
            )

        except ValueError as e:
            await interaction.response.send_message(f"❌ エラー: {e!s}", ephemeral=True)
        except Exception as e:
            logger.error(f"Error adding meeting: {e}")
            await interaction.response.send_message(
                "❌ 会議情報の追加中にエラーが発生しました。", ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Cogをボットに追加."""
    await bot.add_cog(ScheduleCommands(bot))

"""
Discord bot commands.

Discord Botのコマンドとインタラクションを定義します。
"""

from datetime import date, datetime
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from src.bot.checklist_check import ChecklistCheckView
from src.bot.checklist_detail import ChecklistDetailView, create_detailed_checklist_text
from src.config.settings import settings
from src.core.github_sync import GitHubSync
from src.core.smart_engine import SmartTemplateEngine
from src.models import GitHubSyncError, TransportMethod, TripChecklist, TripPurpose, TripRequest
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TripCommands(commands.Cog):
    """旅行準備関連のコマンド."""

    def __init__(self, bot: commands.Bot):
        """初期化."""
        self.bot = bot
        self.smart_engine = SmartTemplateEngine()
        # チェックリストを一時的に保存（本来はDBやRedisを使用）
        self.checklists: dict[str, TripChecklist] = {}

        # GitHub同期機能の初期化
        self.github_sync: GitHubSync | None = None
        if settings.is_feature_enabled("github"):
            try:
                self.github_sync = GitHubSync()
                logger.info("GitHub sync initialized")
            except GitHubSyncError as e:
                logger.error(f"Failed to initialize GitHub sync: {e}")

        logger.info("TripCommands cog initialized")

    @app_commands.command(name="trip", description="旅行準備アシスタントのメインコマンド")
    @app_commands.describe(subcommand="実行するサブコマンド (smart/check/help)")
    async def trip(self, interaction: discord.Interaction, subcommand: str = "help") -> None:
        """旅行準備アシスタントのメインコマンド."""
        if subcommand == "help":
            await self.show_help(interaction)
        else:
            await interaction.response.send_message(
                f"サブコマンド '{subcommand}' は実装されていません。"
            )

    @app_commands.command(name="trip_smart", description="スマートチェックリストを生成します")
    @app_commands.describe(
        destination="目的地（例: 札幌、大阪、東京）",
        start_date="開始日 (YYYY-MM-DD形式)",
        end_date="終了日 (YYYY-MM-DD形式)",
        purpose="旅行の目的",
        transport="交通手段（オプション）",
    )
    @app_commands.choices(
        purpose=[
            app_commands.Choice(name="出張・ビジネス", value="business"),
            app_commands.Choice(name="レジャー・観光", value="leisure"),
        ],
        transport=[
            app_commands.Choice(name="飛行機", value="airplane"),
            app_commands.Choice(name="新幹線・電車", value="train"),
            app_commands.Choice(name="車", value="car"),
            app_commands.Choice(name="バス", value="bus"),
            app_commands.Choice(name="その他", value="other"),
        ],
    )
    async def trip_smart(
        self,
        interaction: discord.Interaction,
        destination: str,
        start_date: str,
        end_date: str,
        purpose: TripPurpose,
        transport: TransportMethod | None = None,
    ) -> None:
        """スマートチェックリストを生成."""
        await interaction.response.defer()

        try:
            # 日付の検証
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

            if end_dt < start_dt:
                await interaction.followup.send(
                    "❌ エラー: 終了日は開始日より後である必要があります。"
                )
                return

            # リクエスト作成
            request = TripRequest(
                destination=destination,
                start_date=start_dt,
                end_date=end_dt,
                purpose=purpose,
                transport_method=transport,
                user_id=str(interaction.user.id),
            )

            # チェックリスト生成
            checklist = await self.smart_engine.generate_checklist(request)

            # チェックリストを一時保存
            self.checklists[checklist.id] = checklist

            # Embed作成
            embed = self.create_checklist_embed(checklist)
            view = ChecklistView(checklist.id, self)

            await interaction.followup.send(embed=embed, view=view)

            logger.info(f"Generated checklist for user {interaction.user.id}: {checklist.id}")

        except ValueError as e:
            await interaction.followup.send(
                f"❌ エラー: 日付の形式が正しくありません。YYYY-MM-DD形式で入力してください。\n{e}"
            )
        except Exception as e:
            logger.error(f"Error generating checklist: {e}")
            await interaction.followup.send("❌ チェックリストの生成中にエラーが発生しました。")

    @app_commands.command(name="trip_reschedule", description="既存の旅行の日程を変更します")
    @app_commands.describe(
        checklist_id="変更する旅行のチェックリストID（省略時は最新の旅行）",
        start_date="新しい開始日 (YYYY-MM-DD形式)",
        end_date="新しい終了日 (YYYY-MM-DD形式)",
    )
    async def trip_reschedule(
        self,
        interaction: discord.Interaction,
        start_date: str,
        end_date: str,
        checklist_id: str | None = None,
    ) -> None:
        """既存の旅行の日程を変更."""
        await interaction.response.defer()

        try:
            # 日付の検証
            new_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            new_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            if new_end_date < new_start_date:
                await interaction.followup.send(
                    "❌ エラー: 終了日は開始日より後である必要があります。"
                )
                return

            # チェックリストを取得
            user_id = str(interaction.user.id)
            checklist = await self._get_checklist_for_reschedule(user_id, checklist_id)

            if not checklist:
                await interaction.followup.send(
                    "❌ チェックリストが見つかりません。\n"
                    "先に `/trip_smart` で旅行計画を作成してください。"
                )
                return

            # 日程変更を実行
            result = self._execute_reschedule(checklist, new_start_date, new_end_date)

            # 成功メッセージ
            embed = discord.Embed(
                title="✅ 日程を変更しました",
                description=result["description"],
                color=discord.Color.green(),
            )

            # 更新されたチェックリストを表示
            checklist_embed = self.create_checklist_embed(checklist)
            view = ChecklistView(checklist.id, self)

            await interaction.followup.send(embeds=[embed, checklist_embed], view=view)

            logger.info(
                f"Rescheduled checklist {checklist.id} for user {user_id}: "
                f"{result['old_dates']} -> {result['new_dates']}"
            )

        except ValueError as e:
            await interaction.followup.send(
                f"❌ エラー: 日付の形式が正しくありません。YYYY-MM-DD形式で入力してください。\n{e}"
            )
        except Exception as e:
            logger.error(f"Error rescheduling trip: {e}")
            await interaction.followup.send("❌ 日程変更中にエラーが発生しました。")

    async def _get_checklist_for_reschedule(
        self, user_id: str, checklist_id: str | None
    ) -> TripChecklist | None:
        """日程変更用のチェックリストを取得."""
        if checklist_id:
            # 指定されたIDのチェックリストを取得
            checklist = self.checklists.get(checklist_id)
            if checklist and checklist.user_id == user_id:
                return checklist
            return None

        # 最新のチェックリストを取得
        user_checklists = [cl for cl in self.checklists.values() if cl.user_id == user_id]
        if not user_checklists:
            return None

        # 作成日時でソートして最新を取得
        return sorted(user_checklists, key=lambda x: x.created_at, reverse=True)[0]

    def _execute_reschedule(
        self, checklist: TripChecklist, new_start_date: date, new_end_date: date
    ) -> dict[str, Any]:
        """日程変更を実行し、結果を返す."""
        # 変更前の情報を保存
        old_start_date = checklist.start_date
        old_end_date = checklist.end_date
        old_duration = (old_end_date - old_start_date).days

        # 日程を更新
        checklist.start_date = new_start_date
        checklist.end_date = new_end_date
        checklist.updated_at = datetime.now()

        new_duration = (new_end_date - new_start_date).days

        # 調整メッセージを生成
        adjustment_msg = self._generate_adjustment_message(checklist, old_duration, new_duration)
        weather_update_msg = self._get_weather_update_message()

        description = (
            f"**{checklist.destination}**旅行の日程を更新しました。\n\n"
            f"**変更前**: {old_start_date} ～ {old_end_date} ({old_duration}泊)\n"
            f"**変更後**: {new_start_date} ～ {new_end_date} ({new_duration}泊)"
            f"{adjustment_msg}{weather_update_msg}"
        )

        return {
            "description": description,
            "old_dates": f"{old_start_date} - {old_end_date}",
            "new_dates": f"{new_start_date} - {new_end_date}",
        }

    def _generate_adjustment_message(
        self, checklist: TripChecklist, old_duration: int, new_duration: int
    ) -> str:
        """期間変更に伴う調整メッセージを生成."""
        if new_duration == old_duration:
            return ""

        adjustments = checklist.adjust_for_duration_change(old_duration, new_duration)

        if adjustments:
            msg = "\n\n📦 **期間変更に伴う調整:**\n"
            for adj in adjustments:
                msg += f"• {adj}\n"
            return msg

        if new_duration > old_duration:
            return f"\n📦 期間が{old_duration}泊から{new_duration}泊に延長されました。"
        else:
            return f"\n📦 期間が{old_duration}泊から{new_duration}泊に短縮されました。"

    def _get_weather_update_message(self) -> str:
        """天気予報更新メッセージを取得."""
        if settings.is_feature_enabled("weather"):
            return "\n⛅ 天気予報の更新は次回のアップデートで対応予定です。"
        return ""

    @app_commands.command(name="trip_history", description="過去の旅行履歴を表示します")
    @app_commands.describe(limit="表示する件数（デフォルト: 10件）")
    async def trip_history(self, interaction: discord.Interaction, limit: int = 10) -> None:
        """過去の旅行履歴を表示."""
        if not settings.is_feature_enabled("github"):
            await interaction.response.send_message(
                "GitHub同期機能は無効になっています。", ephemeral=True
            )
            return

        if not self.github_sync:
            await interaction.response.send_message(
                "GitHub同期機能が初期化されていません。", ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            # ユーザーの旅行履歴を取得
            user_id = str(interaction.user.id)
            trips = self.github_sync.get_user_trips(user_id, limit=limit)

            if not trips:
                embed = discord.Embed(
                    title="📜 旅行履歴",
                    description="まだ保存された旅行はありません。",
                    color=discord.Color.blue(),
                )
                await interaction.followup.send(embed=embed)
                return

            # 履歴のEmbedを作成
            embed = discord.Embed(
                title="📜 旅行履歴",
                description=f"過去の旅行記録（最新{len(trips)}件）",
                color=discord.Color.blue(),
            )

            for trip in trips[:10]:  # 最大10件まで表示
                # ファイル名から情報を抽出
                filename = trip["filename"]
                status_emoji = {"planning": "📝", "ongoing": "✈️", "completed": "✅"}.get(
                    trip.get("status", "planning"), "📋"
                )

                completion = trip.get("completion_percentage", 0)

                embed.add_field(
                    name=f"{status_emoji} {filename}",
                    value=(
                        f"**進捗**: {completion:.1f}%\n"
                        f"**更新**: {trip.get('updated_at', '不明')[:10]}\n"
                        f"[GitHubで表示]({trip['github_url']})"
                    ),
                    inline=True,
                )

            embed.set_footer(text=f"合計 {len(trips)} 件の旅行記録")

            # 履歴選択ビューを追加
            view = TripHistoryView(trips[:10], self)

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error fetching trip history: {e}")
            await interaction.followup.send(
                "❌ 旅行履歴の取得中にエラーが発生しました。", ephemeral=True
            )

    async def show_help(self, interaction: discord.Interaction) -> None:
        """ヘルプメッセージを表示."""
        embed = discord.Embed(
            title="🧳 TravelAssistant ヘルプ",
            description="AI支援による旅行準備アシスタント",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="📋 利用可能なコマンド",
            value=(
                "`/trip_smart` - スマートチェックリスト生成\n"
                "`/trip_reschedule` - 旅行の日程変更\n"
                "`/trip_history` - 過去の旅行履歴\n"
                "`/trip_check` - チェックリスト確認（開発中）"
            ),
            inline=False,
        )

        embed.add_field(
            name="🚀 使い方",
            value=(
                "1. `/trip_smart`コマンドで必要情報を入力\n"
                "2. 自動生成されたチェックリストを確認\n"
                "3. ボタンでアイテムをチェック"
            ),
            inline=False,
        )

        embed.add_field(
            name="✨ 特徴",
            value=(
                "• 目的地・期間に応じた自動調整\n• 天気予報連携（開発中）\n• 個人最適化（開発中）"
            ),
            inline=False,
        )

        embed.set_footer(text="Powered by Claude AI")

        await interaction.response.send_message(embed=embed)

    def create_checklist_embed(self, checklist: TripChecklist) -> discord.Embed:
        """チェックリストのEmbedを作成."""
        embed = discord.Embed(
            title=f"🧳 {checklist.destination}旅行チェックリスト",
            description=(
                f"**期間**: {checklist.start_date} ～ {checklist.end_date}\n"
                f"**目的**: {'出張' if checklist.purpose == 'business' else 'レジャー'}\n"
                f"**進捗**: {checklist.completion_percentage:.1f}% "
                f"({checklist.completed_count}/{checklist.total_count})"
            ),
            color=discord.Color.green()
            if checklist.completion_percentage >= 80
            else discord.Color.blue(),
        )

        # カテゴリ別に表示（最初の3カテゴリのみ）
        for i, (category, items) in enumerate(checklist.items_by_category.items()):
            if i >= 3:  # Embedのフィールド数制限対策
                embed.add_field(
                    name="...",
                    value=f"他 {len(checklist.items_by_category) - 3} カテゴリ",
                    inline=False,
                )
                break

            # 各カテゴリの最初の5項目を表示
            value_lines = []
            for _j, item in enumerate(items[:5]):
                check_mark = "✅" if item.checked else "⬜"
                value_lines.append(f"{check_mark} {item.name}")

            if len(items) > 5:
                value_lines.append(f"... 他{len(items) - 5}項目")

            embed.add_field(name=f"📋 {category}", value="\n".join(value_lines), inline=True)

        # 進捗フィールドを追加
        progress_text = (
            f"{checklist.completion_percentage:.2f}% "
            f"({checklist.completed_count}/{checklist.total_count})"
        )
        embed.add_field(
            name="📊 進捗",
            value=progress_text,
            inline=True,
        )

        embed.set_footer(
            text=f"ID: {checklist.id} | 作成: {checklist.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

        return embed


class ChecklistView(discord.ui.View):
    """チェックリスト操作用のView."""

    def __init__(self, checklist_id: str, cog: TripCommands, timeout: float = 300):
        """初期化."""
        super().__init__(timeout=timeout)
        self.checklist_id = checklist_id
        self.cog = cog

    @discord.ui.button(
        label="✅ 項目をチェック", style=discord.ButtonStyle.green, custom_id="check_items"
    )
    async def check_items(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """チェックリスト項目をチェック."""
        # チェックリストを取得
        checklist = self.cog.checklists.get(self.checklist_id)

        if not checklist:
            await interaction.response.send_message(
                "チェックリストが見つかりませんでした。", ephemeral=True
            )
            return

        # チェック機能ビューを作成
        check_view = ChecklistCheckView(checklist, self.cog)
        embed = check_view.get_embed()

        await interaction.response.send_message(embed=embed, view=check_view, ephemeral=True)

    @discord.ui.button(
        label="📊 詳細表示", style=discord.ButtonStyle.primary, custom_id="show_details"
    )
    async def show_details(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """チェックリストの詳細を表示."""
        # チェックリストを取得
        checklist = self.cog.checklists.get(self.checklist_id)

        if not checklist:
            await interaction.response.send_message(
                "チェックリストが見つかりませんでした。", ephemeral=True
            )
            return

        # 詳細テキストを作成
        detailed_text = create_detailed_checklist_text(checklist)

        # 詳細表示ビューを作成
        detail_view = ChecklistDetailView(detailed_text)
        embed = detail_view.get_embed()

        await interaction.response.send_message(embed=embed, view=detail_view, ephemeral=True)

    @discord.ui.button(label="💾 保存", style=discord.ButtonStyle.gray, custom_id="save_checklist")
    async def save_checklist(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """チェックリストを保存."""
        if not settings.is_feature_enabled("github"):
            await interaction.response.send_message(
                "GitHub同期機能は無効になっています。", ephemeral=True
            )
            return

        if not self.cog.github_sync:
            await interaction.response.send_message(
                "GitHub同期機能が初期化されていません。", ephemeral=True
            )
            return

        # チェックリストを取得
        checklist = self.cog.checklists.get(self.checklist_id)
        if not checklist:
            await interaction.response.send_message(
                "チェックリストが見つかりませんでした。", ephemeral=True
            )
            return

        # 処理中のメッセージを表示
        await interaction.response.defer(ephemeral=True)

        try:
            # GitHub に保存
            github_url = self.cog.github_sync.save_checklist(checklist)

            # 成功メッセージ
            embed = discord.Embed(
                title="✅ チェックリストを保存しました",
                description="GitHubリポジトリに正常に保存されました。",
                color=discord.Color.green(),
            )

            if github_url:
                embed.add_field(
                    name="📍 保存場所", value=f"[GitHubで表示]({github_url})", inline=False
                )

            embed.add_field(
                name="📊 保存内容",
                value=(
                    f"• **目的地**: {checklist.destination}\n"
                    f"• **期間**: {checklist.start_date} ～ {checklist.end_date}\n"
                    f"• **進捗**: {checklist.completion_percentage:.1f}%"
                ),
                inline=False,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except GitHubSyncError as e:
            logger.error(f"Failed to save checklist to GitHub: {e}")
            await interaction.followup.send(
                f"❌ GitHub保存中にエラーが発生しました: {e}", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Unexpected error saving checklist: {e}")
            await interaction.followup.send("❌ 予期しないエラーが発生しました。", ephemeral=True)

    @discord.ui.button(
        label="📅 日程変更", style=discord.ButtonStyle.secondary, custom_id="reschedule"
    )
    async def reschedule(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """日程変更モーダルを表示."""
        # チェックリストを取得
        checklist = self.cog.checklists.get(self.checklist_id)
        if not checklist:
            await interaction.response.send_message(
                "チェックリストが見つかりませんでした。", ephemeral=True
            )
            return

        # 日程変更モーダルを表示
        modal = RescheduleModal(checklist, self.cog)
        await interaction.response.send_modal(modal)


class RescheduleModal(discord.ui.Modal, title="旅行の日程を変更"):
    """日程変更用のモーダル."""

    def __init__(self, checklist: TripChecklist, cog: TripCommands):
        """初期化."""
        super().__init__()
        self.checklist = checklist
        self.cog = cog

        # 現在の日付をデフォルト値として設定
        self.start_date.default = checklist.start_date.strftime("%Y-%m-%d")
        self.end_date.default = checklist.end_date.strftime("%Y-%m-%d")

    start_date: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="新しい開始日",
        placeholder="例: 2025-07-01",
        required=True,
        max_length=10,
        min_length=10,
    )

    end_date: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="新しい終了日",
        placeholder="例: 2025-07-03",
        required=True,
        max_length=10,
        min_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """送信時の処理."""
        try:
            # 日付の検証
            new_start_date = datetime.strptime(self.start_date.value, "%Y-%m-%d").date()
            new_end_date = datetime.strptime(self.end_date.value, "%Y-%m-%d").date()

            if new_end_date < new_start_date:
                await interaction.response.send_message(
                    "❌ エラー: 終了日は開始日より後である必要があります。", ephemeral=True
                )
                return

            # 日程変更前の情報を保存
            old_start_date = self.checklist.start_date
            old_end_date = self.checklist.end_date
            old_duration = (old_end_date - old_start_date).days

            # 日程を更新
            self.checklist.start_date = new_start_date
            self.checklist.end_date = new_end_date
            self.checklist.updated_at = datetime.now()

            # 日程変更に伴う調整
            new_duration = (new_end_date - new_start_date).days
            duration_changed = new_duration != old_duration

            # 期間が変更された場合の調整
            adjustment_msg = ""
            if duration_changed:
                adjustments = self.checklist.adjust_for_duration_change(old_duration, new_duration)

                if adjustments:
                    adjustment_msg = "\n\n📦 **期間変更に伴う調整:**\n"
                    for adj in adjustments:
                        adjustment_msg += f"• {adj}\n"

            # 成功メッセージ
            embed = discord.Embed(
                title="✅ 日程を変更しました",
                description=(
                    f"**{self.checklist.destination}**旅行の日程を更新しました。\n\n"
                    f"**変更前**: {old_start_date} ～ {old_end_date} ({old_duration}泊)\n"
                    f"**変更後**: {new_start_date} ～ {new_end_date} ({new_duration}泊)"
                    f"{adjustment_msg}"
                ),
                color=discord.Color.green(),
            )

            # 更新されたチェックリストを表示
            checklist_embed = self.cog.create_checklist_embed(self.checklist)
            view = ChecklistView(self.checklist.id, self.cog)

            await interaction.response.send_message(
                embeds=[embed, checklist_embed], view=view, ephemeral=False
            )

            logger.info(
                f"Rescheduled checklist {self.checklist.id} via modal: "
                f"{old_start_date} - {old_end_date} -> {new_start_date} - {new_end_date}"
            )

        except ValueError as e:
            await interaction.response.send_message(
                f"❌ エラー: 日付の形式が正しくありません。YYYY-MM-DD形式で入力してください。\n{e}",
                ephemeral=True,
            )
        except Exception as e:
            logger.error(f"Error rescheduling trip via modal: {e}")
            await interaction.response.send_message(
                "❌ 日程変更中にエラーが発生しました。", ephemeral=True
            )


class TripHistoryView(discord.ui.View):
    """旅行履歴選択用のView."""

    def __init__(self, trips: list[dict[str, Any]], cog: TripCommands, timeout: float = 300):
        """初期化."""
        super().__init__(timeout=timeout)
        self.trips = trips
        self.cog = cog

        # ドロップダウンメニューを追加
        if trips:
            self.add_item(TripSelectDropdown(trips, cog))


class TripSelectDropdown(discord.ui.Select[discord.ui.View]):
    """旅行選択ドロップダウン."""

    def __init__(self, trips: list[dict[str, Any]], cog: TripCommands):
        """初期化."""
        self.cog = cog

        # ドロップダウンのオプションを作成
        options = []
        for trip in trips[:25]:  # Discord制限：最大25個
            filename = trip["filename"]
            completion = trip.get("completion_percentage", 0)
            status_emoji = {"planning": "📝", "ongoing": "✈️", "completed": "✅"}.get(
                trip.get("status", "planning"), "📋"
            )

            options.append(
                discord.SelectOption(
                    label=f"{status_emoji} {filename[:50]}",  # 長すぎる場合は切り詰め
                    description=f"進捗: {completion:.1f}% | {trip.get('updated_at', '不明')[:10]}",
                    value=trip["checklist_id"],
                )
            )

        super().__init__(
            placeholder="表示する旅行を選択してください...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="select_trip",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """選択されたときの処理."""
        checklist_id = self.values[0]
        user_id = str(interaction.user.id)

        if not self.cog.github_sync:
            await interaction.response.send_message(
                "GitHub同期機能が初期化されていません。", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # チェックリストを読み込み
            checklist = self.cog.github_sync.load_checklist(checklist_id, user_id)

            if not checklist:
                await interaction.followup.send(
                    "チェックリストが見つかりませんでした。", ephemeral=True
                )
                return

            # メモリに保存（操作できるように）
            self.cog.checklists[checklist.id] = checklist

            # Embed作成
            embed = self.cog.create_checklist_embed(checklist)
            view = ChecklistView(checklist.id, self.cog)

            await interaction.followup.send(
                content="📋 チェックリストを読み込みました！",
                embed=embed,
                view=view,
                ephemeral=False,
            )

        except Exception as e:
            logger.error(f"Error loading checklist from history: {e}")
            await interaction.followup.send(
                f"❌ チェックリストの読み込み中にエラーが発生しました: {e}", ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Cogをセットアップ."""
    await bot.add_cog(TripCommands(bot))

"""
Discord bot commands.

Discord Botのコマンドとインタラクションを定義します。
"""

from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from src.config.settings import settings
from src.core.smart_engine import SmartTemplateEngine
from src.types import TransportMethod, TripPurpose, TripRequest
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TripCommands(commands.Cog):
    """旅行準備関連のコマンド."""

    def __init__(self, bot: commands.Bot):
        """初期化."""
        self.bot = bot
        self.smart_engine = SmartTemplateEngine()
        logger.info("TripCommands cog initialized")

    @app_commands.command(name="trip", description="旅行準備アシスタントのメインコマンド")
    @app_commands.describe(subcommand="実行するサブコマンド (smart/check/help)")
    async def trip(self, interaction: discord.Interaction, subcommand: str = "help"):
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
    ):
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

    async def show_help(self, interaction: discord.Interaction):
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
                "`/trip_check` - チェックリスト確認（開発中）\n"
                "`/trip_history` - 過去の旅行履歴（開発中）"
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

    def create_checklist_embed(self, checklist) -> discord.Embed:
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
    async def check_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        """チェックリスト項目をチェック."""
        # TODO: モーダルでアイテム選択
        await interaction.response.send_message("チェック機能は開発中です。", ephemeral=True)

    @discord.ui.button(
        label="📊 詳細表示", style=discord.ButtonStyle.blue, custom_id="show_details"
    )
    async def show_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        """チェックリストの詳細を表示."""
        # TODO: 詳細表示実装
        await interaction.response.send_message("詳細表示機能は開発中です。", ephemeral=True)

    @discord.ui.button(label="💾 保存", style=discord.ButtonStyle.gray, custom_id="save_checklist")
    async def save_checklist(self, interaction: discord.Interaction, button: discord.ui.Button):
        """チェックリストを保存."""
        if not settings.is_feature_enabled("github"):
            await interaction.response.send_message(
                "GitHub同期機能は無効になっています。", ephemeral=True
            )
            return

        # TODO: GitHub保存実装
        await interaction.response.send_message("保存機能は開発中です。", ephemeral=True)


async def setup(bot: commands.Bot):
    """Cogをセットアップ."""
    await bot.add_cog(TripCommands(bot))

"""
Extension for showing full checklist details.

チェックリストの詳細表示機能を追加します。
"""

import io
from typing import Any

import discord

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ChecklistDetailView(discord.ui.View):
    """チェックリスト詳細表示用のView."""

    def __init__(self, checklist_data: str, timeout: float = 180):
        """初期化."""
        super().__init__(timeout=timeout)
        self.checklist_data = checklist_data
        self.current_page = 0
        self.items_per_page = 20

        # チェックリストを行に分割
        self.lines = checklist_data.split("\n")
        self.total_pages = (len(self.lines) - 1) // self.items_per_page + 1

    def get_page_content(self) -> str:
        """現在のページの内容を取得."""
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_lines = self.lines[start_idx:end_idx]

        return "\n".join(page_lines) or "内容がありません"

    def get_embed(self) -> discord.Embed:
        """現在のページのEmbedを作成."""
        embed = discord.Embed(
            title=f"📋 チェックリスト詳細 (ページ {self.current_page + 1}/{self.total_pages})",
            description=f"```\n{self.get_page_content()}\n```",
            color=discord.Color.blue(),
        )
        embed.set_footer(text="⬅️前ページ / ➡️次ページ でナビゲート")
        return embed

    @discord.ui.button(label="⬅️ 前へ", style=discord.ButtonStyle.primary)
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """前のページへ."""
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.send_message("最初のページです", ephemeral=True)

    @discord.ui.button(label="➡️ 次へ", style=discord.ButtonStyle.primary)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """次のページへ."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.send_message("最後のページです", ephemeral=True)

    @discord.ui.button(label="📄 テキストファイルで送信", style=discord.ButtonStyle.secondary)
    async def send_as_file(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """テキストファイルとして送信."""
        file = discord.File(
            filename="checklist.txt", fp=io.BytesIO(self.checklist_data.encode("utf-8"))
        )
        await interaction.response.send_message(
            "チェックリストをテキストファイルとして送信します：", file=file, ephemeral=True
        )


def create_detailed_checklist_text(checklist: Any) -> str:
    """チェックリストの詳細テキストを作成."""
    lines = []
    lines.append(f"{'=' * 50}")
    lines.append(f"{checklist.destination}旅行チェックリスト")
    lines.append(f"{'=' * 50}")
    lines.append(f"期間: {checklist.start_date} ～ {checklist.end_date}")
    lines.append(f"目的: {'出張' if checklist.purpose == 'business' else 'レジャー'}")
    progress = f"{checklist.completion_percentage:.1f}%"
    lines.append(f"進捗: {progress} ({checklist.completed_count}/{checklist.total_count})")
    lines.append("")

    for category, items in checklist.items_by_category.items():
        lines.append(f"\n【{category}】")
        lines.append("-" * 30)

        for i, item in enumerate(items, 1):
            check = "✓" if item.checked else "□"
            lines.append(f"{check} {i:2d}. {item.name}")
            if item.auto_added and item.reason:
                lines.append(f"     ⭐ {item.reason}")

    lines.append(f"\n{'=' * 50}")
    lines.append(f"合計: {checklist.total_count}項目")

    return "\n".join(lines)

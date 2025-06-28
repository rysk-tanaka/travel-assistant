"""
Checklist item checking functionality.

チェックリスト項目のチェック/アンチェック機能を提供します。
"""

from typing import Any

import discord

from src.models import ChecklistItem, TripChecklist
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CategorySelectMenu(discord.ui.Select[Any]):
    """カテゴリ選択用のセレクトメニュー."""

    def __init__(
        self,
        checklist: TripChecklist,
        cog: Any,
        placeholder: str = "チェックするカテゴリを選択...",
    ):
        """初期化."""
        self.checklist = checklist
        self.cog = cog

        # カテゴリリストを作成
        categories = list(checklist.items_by_category.keys())
        options = []

        for category in categories[:25]:  # Discordの制限: 最大25個
            items = checklist.items_by_category[category]
            checked_count = sum(1 for item in items if item.checked)
            total_count = len(items)

            # カテゴリの説明文を作成
            description = f"{checked_count}/{total_count} 完了"
            if checked_count == total_count:
                description = "✅ すべて完了"
            elif checked_count == 0:
                description = "⬜ 未着手"

            option = discord.SelectOption(
                label=category,
                description=description,
                value=category,
                emoji="📋",
            )
            options.append(option)

        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """カテゴリが選択されたときの処理."""
        selected_category = self.values[0]
        items = self.checklist.items_by_category.get(selected_category, [])  # type: ignore[call-overload]

        if not items:
            await interaction.response.send_message(
                "このカテゴリにはアイテムがありません。", ephemeral=True
            )
            return

        # アイテム選択ビューを表示
        view = ItemCheckView(self.checklist, selected_category, self.cog)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ItemCheckView(discord.ui.View):
    """アイテムチェック用のView."""

    def __init__(
        self,
        checklist: TripChecklist,
        category: str,
        cog: Any,
        timeout: float = 300,
    ):
        """初期化."""
        super().__init__(timeout=timeout)
        self.checklist = checklist
        self.category = category
        self.cog = cog
        self.items = checklist.items_by_category.get(category, [])  # type: ignore[call-overload]
        self.current_page = 0
        self.items_per_page = 10

        # アイテム選択メニューを追加
        self.add_item(ItemSelectMenu(self.items, self.current_page, self.items_per_page, self))

        # ページネーションボタンを更新
        self.update_buttons()

    def get_embed(self) -> discord.Embed:
        """現在のページのEmbedを作成."""
        embed = discord.Embed(
            title=f"📋 {self.category} - アイテムチェック",
            description="チェックを切り替えたいアイテムを選択してください",
            color=discord.Color.blue(),
        )

        # 進捗情報
        checked_count = sum(1 for item in self.items if item.checked)
        total_count = len(self.items)
        progress = (checked_count / total_count * 100) if total_count > 0 else 0

        embed.add_field(
            name="進捗",
            value=f"{progress:.1f}% ({checked_count}/{total_count})",
            inline=False,
        )

        # 現在のページのアイテムリスト
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.items))

        items_text = []
        for i in range(start_idx, end_idx):
            item = self.items[i]
            check_mark = "✅" if item.checked else "⬜"
            items_text.append(f"{check_mark} {i + 1}. {item.name}")
            if item.auto_added and item.reason:
                items_text.append(f"    ⭐ {item.reason}")

        embed.add_field(
            name=f"アイテム一覧 (ページ {self.current_page + 1}/{self.total_pages})",
            value="\n".join(items_text) or "アイテムがありません",
            inline=False,
        )

        return embed

    @property
    def total_pages(self) -> int:
        """総ページ数を計算."""
        return (len(self.items) - 1) // self.items_per_page + 1 if self.items else 1

    def update_buttons(self) -> None:
        """ページネーションボタンの有効/無効を更新."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.custom_id == "prev_page":
                    item.disabled = self.current_page == 0
                elif item.custom_id == "next_page":
                    item.disabled = self.current_page >= self.total_pages - 1

    @discord.ui.button(
        label="⬅️ 前へ",
        style=discord.ButtonStyle.primary,
        custom_id="prev_page",
        row=2,
    )
    async def previous_page(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """前のページへ."""
        if self.current_page > 0:
            self.current_page -= 1
            # セレクトメニューを更新
            self.clear_items()
            self.add_item(ItemSelectMenu(self.items, self.current_page, self.items_per_page, self))
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.send_message("最初のページです", ephemeral=True)

    @discord.ui.button(
        label="➡️ 次へ",
        style=discord.ButtonStyle.primary,
        custom_id="next_page",
        row=2,
    )
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """次のページへ."""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            # セレクトメニューを更新
            self.clear_items()
            self.add_item(ItemSelectMenu(self.items, self.current_page, self.items_per_page, self))
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        else:
            await interaction.response.send_message("最後のページです", ephemeral=True)

    @discord.ui.button(
        label="✅ すべてチェック",
        style=discord.ButtonStyle.success,
        custom_id="check_all",
        row=2,
    )
    async def check_all(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """カテゴリ内のすべてのアイテムをチェック."""
        for item in self.items:
            item.checked = True

        # チェックリストを更新
        self.cog.checklists[self.checklist.id] = self.checklist

        # ビューを更新
        self.clear_items()
        self.add_item(ItemSelectMenu(self.items, self.current_page, self.items_per_page, self))
        self.update_buttons()

        await interaction.response.edit_message(embed=self.get_embed(), view=self)
        await interaction.followup.send(
            f"✅ {self.category}のすべてのアイテムをチェックしました！", ephemeral=True
        )

    @discord.ui.button(
        label="⬜ すべて解除",
        style=discord.ButtonStyle.danger,
        custom_id="uncheck_all",
        row=2,
    )
    async def uncheck_all(
        self, interaction: discord.Interaction, button: discord.ui.Button[Any]
    ) -> None:
        """カテゴリ内のすべてのアイテムのチェックを解除."""
        for item in self.items:
            item.checked = False

        # チェックリストを更新
        self.cog.checklists[self.checklist.id] = self.checklist

        # ビューを更新
        self.clear_items()
        self.add_item(ItemSelectMenu(self.items, self.current_page, self.items_per_page, self))
        self.update_buttons()

        await interaction.response.edit_message(embed=self.get_embed(), view=self)
        await interaction.followup.send(
            f"⬜ {self.category}のすべてのアイテムのチェックを解除しました。", ephemeral=True
        )


class ItemSelectMenu(discord.ui.Select[Any]):
    """アイテム選択用のセレクトメニュー."""

    def __init__(
        self,
        items: list[ChecklistItem],
        current_page: int,
        items_per_page: int,
        parent_view: ItemCheckView,
    ):
        """初期化."""
        self.all_items = items
        self.current_page = current_page
        self.items_per_page = items_per_page
        self.parent_view = parent_view

        # 現在のページのアイテムを取得
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        page_items = items[start_idx:end_idx]

        options = []
        for i, item in enumerate(page_items):
            # グローバルインデックス
            global_idx = start_idx + i

            # チェック状態を表すemoji
            emoji = "✅" if item.checked else "⬜"

            # 説明文
            description = f"{'チェック済み' if item.checked else '未チェック'}"
            if item.auto_added and item.reason:
                description = f"{description[:40]}... ⭐"  # 説明文は最大50文字

            option = discord.SelectOption(
                label=f"{global_idx + 1}. {item.name[:80]}",  # ラベルは最大100文字
                description=description,
                value=str(global_idx),
                emoji=emoji,
            )
            options.append(option)

        super().__init__(
            placeholder="チェックを切り替えるアイテムを選択（複数可）...",
            min_values=0,
            max_values=len(options),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """アイテムが選択されたときの処理."""
        # 選択されたアイテムのインデックスを取得
        selected_indices = [int(value) for value in self.values]

        # チェック状態を切り替え
        toggled_items = []
        for idx in selected_indices:
            if 0 <= idx < len(self.all_items):
                item = self.all_items[idx]
                item.checked = not item.checked
                toggled_items.append((item.name, item.checked))

        # チェックリストを更新
        self.parent_view.cog.checklists[self.parent_view.checklist.id] = self.parent_view.checklist

        # ビューを更新
        self.parent_view.clear_items()
        self.parent_view.add_item(
            ItemSelectMenu(
                self.all_items,
                self.current_page,
                self.items_per_page,
                self.parent_view,
            )
        )
        self.parent_view.update_buttons()

        # メッセージを更新
        await interaction.response.edit_message(
            embed=self.parent_view.get_embed(), view=self.parent_view
        )

        # フィードバックメッセージ
        if toggled_items:
            feedback = []
            for name, checked in toggled_items[:5]:  # 最大5個まで表示
                status = "✅ チェック" if checked else "⬜ 解除"
                feedback.append(f"{status}: {name}")

            if len(toggled_items) > 5:
                feedback.append(f"... 他{len(toggled_items) - 5}項目")

            await interaction.followup.send("\n".join(feedback), ephemeral=True)


class ChecklistCheckView(discord.ui.View):
    """チェックリストチェック機能のメインView."""

    def __init__(self, checklist: TripChecklist, cog: Any, timeout: float = 300):
        """初期化."""
        super().__init__(timeout=timeout)
        self.checklist = checklist
        self.cog = cog

        # カテゴリ選択メニューを追加
        self.add_item(CategorySelectMenu(checklist, cog))

    def get_embed(self) -> discord.Embed:
        """メインEmbedを作成."""
        embed = discord.Embed(
            title=f"✅ {self.checklist.destination}旅行チェックリスト - 項目管理",
            description="カテゴリを選択してアイテムのチェック状態を管理できます",
            color=discord.Color.green(),
        )

        # 全体の進捗
        embed.add_field(
            name="📊 全体進捗",
            value=(
                f"{self.checklist.completion_percentage:.1f}% "
                f"({self.checklist.completed_count}/{self.checklist.total_count})"
            ),
            inline=False,
        )

        # カテゴリ別の進捗
        category_progress = []
        for category, items in self.checklist.items_by_category.items():
            checked = sum(1 for item in items if item.checked)
            total = len(items)
            if checked == total:
                status = "✅"
            elif checked == 0:
                status = "⬜"
            else:
                status = "🔶"
            category_progress.append(f"{status} {category}: {checked}/{total}")

        # 最初の10カテゴリを表示
        if category_progress:
            display_progress = category_progress[:10]
            if len(category_progress) > 10:
                display_progress.append(f"... 他{len(category_progress) - 10}カテゴリ")

            embed.add_field(
                name="📋 カテゴリ別進捗",
                value="\n".join(display_progress),
                inline=False,
            )

        embed.set_footer(text="カテゴリを選択してアイテムを管理してください")

        return embed

"""
Markdown utilities for template processing.

Markdownテンプレートの読み込み、解析、変数置換を行うユーティリティ集です。
"""

import re
from pathlib import Path
from typing import Any

import frontmatter
from jinja2 import Environment, FileSystemLoader, TemplateError
from pydantic import BaseModel, Field

from src.config.settings import settings
from src.models import TemplateMetadataDict, TemplateNotFoundError
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TemplateData(BaseModel):
    """テンプレートデータの構造."""

    metadata: TemplateMetadataDict = Field(..., description="テンプレートメタデータ")
    content: str = Field(..., description="テンプレート本文")

    @classmethod
    def from_file(cls, file_path: Path) -> "TemplateData":
        """ファイルからテンプレートデータを読み込む."""
        try:
            with file_path.open(encoding="utf-8") as f:
                post = frontmatter.load(f)

            metadata = TemplateMetadataDict(
                template_type=post.metadata.get("template_type", "unknown"),
                template_version=post.metadata.get("template_version", "1.0"),
                last_updated=post.metadata.get("last_updated", ""),
                customizable_fields=post.metadata.get("customizable_fields", []),
            )

            return cls(metadata=metadata, content=post.content)

        except Exception as e:
            logger.error(f"Failed to load template from {file_path}: {e}")
            raise TemplateNotFoundError(f"テンプレート読み込みエラー: {file_path}") from e


class MarkdownProcessor:
    """Markdownテンプレート処理クラス."""

    def __init__(self, template_dir: Path | None = None):
        """初期化."""
        self.template_dir = template_dir or Path(settings.TEMPLATE_PATH)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False,  # Markdownなのでエスケープ不要
            trim_blocks=True,
            lstrip_blocks=True,
        )
        logger.debug(f"MarkdownProcessor initialized with template_dir: {self.template_dir}")

    def load_template(self, template_name: str) -> TemplateData:
        """テンプレートファイルを読み込む."""
        template_path = self.template_dir / template_name

        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            raise TemplateNotFoundError(f"テンプレートが見つかりません: {template_name}")

        logger.info(f"Loading template: {template_name}")
        return TemplateData.from_file(template_path)

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """テンプレートに変数を適用してレンダリング."""
        try:
            # Jinja2テンプレートとして読み込み
            template = self.env.get_template(template_name)

            # デフォルト値を設定
            default_context = {
                "destination": "未定",
                "start_date": "未定",
                "end_date": "未定",
                "duration": 0,
                "purpose": "未定",
                "transport_method": "未定",
                "weather_items": "",
                "regional_items": "",
                "hotel_name": "未定",
                "hotel_phone": "未定",
                "client_name": "",
                "client_phone": "",
                "emergency_contact": "",
                "meeting_location": "",
                "company_emergency": "",
                "business_cards_count": "50-100",
                "recommended_cash": "20,000",
                "weather_condition": "晴れ",
                "souvenir_notes": "",
            }

            # コンテキストをマージ（入力が優先）
            final_context = {**default_context, **context}

            # レンダリング
            rendered = template.render(**final_context)
            logger.debug(
                f"Rendered template {template_name} with context keys: {list(context.keys())}"
            )

            return rendered

        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise TemplateNotFoundError(f"テンプレートレンダリングエラー: {e}") from e

    def combine_templates(
        self, base_template: str, *module_templates: str, context: dict[str, Any]
    ) -> str:
        """ベーステンプレートとモジュールを組み合わせてレンダリング."""
        logger.info(f"Combining templates: base={base_template}, modules={module_templates}")

        # ベーステンプレートをレンダリング
        base_content = self.render_template(base_template, context)

        # モジュールテンプレートを追加
        module_contents = []
        for module_name in module_templates:
            try:
                module_content = self.render_template(f"modules/{module_name}", context)
                module_contents.append(module_content)
            except TemplateNotFoundError:
                logger.warning(f"Module template not found: {module_name}")

        # 結合
        combined = base_content
        if module_contents:
            combined += "\n\n---\n\n" + "\n\n".join(module_contents)

        return combined

    def extract_checklist_items(self, markdown_content: str) -> list[tuple[str, str, bool]]:
        """Markdownからチェックリスト項目を抽出.

        Returns:
            List of (category, item_name, checked) tuples
        """
        items = []
        current_category = "その他"

        lines = markdown_content.split("\n")
        for line in lines:
            # カテゴリヘッダーを検出
            if line.startswith("### ") or line.startswith("## "):
                # アイコンと説明文を除去してカテゴリ名を抽出
                category_match = re.match(r"#{2,3}\s*[🎫💼👔🧳📱💰🌦️🏠📞🎁]*\s*(.+)", line)
                if category_match:
                    current_category = category_match.group(1).strip()

            # チェックリスト項目を検出
            elif line.strip().startswith("- [ ]") or line.strip().startswith("- [x]"):
                checked = line.strip().startswith("- [x]")
                # チェックボックス部分を除去してアイテム名を抽出
                item_match = re.match(r"- \[[x ]\]\s*(.+)", line.strip())
                if item_match:
                    item_name = item_match.group(1).strip()
                    items.append((current_category, item_name, checked))

        logger.debug(f"Extracted {len(items)} checklist items from markdown")
        return items

    def update_checklist_status(self, markdown_content: str, updates: dict[str, bool]) -> str:
        """チェックリストの状態を更新.

        Args:
            markdown_content: 元のMarkdown
            updates: {item_name: checked} の辞書

        Returns:
            更新されたMarkdown
        """
        lines = markdown_content.split("\n")
        updated_lines = []

        for line in lines:
            if line.strip().startswith("- [ ]") or line.strip().startswith("- [x]"):
                # アイテム名を抽出
                item_match = re.match(r"- \[[x ]\]\s*(.+)", line.strip())
                if item_match:
                    item_name = item_match.group(1).strip()
                    if item_name in updates:
                        # チェック状態を更新
                        check_mark = "x" if updates[item_name] else " "
                        indent = len(line) - len(line.lstrip())
                        updated_line = " " * indent + f"- [{check_mark}] {item_name}"
                        updated_lines.append(updated_line)
                        continue

            updated_lines.append(line)

        return "\n".join(updated_lines)

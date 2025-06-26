"""
Smart template engine for checklist generation.

条件に応じてテンプレートを自動調整し、最適なチェックリストを生成します。
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config.settings import settings
from src.types import (
    ChecklistItem,
    ItemCategory,
    TemplateType,
    TripChecklist,
    TripRequest,
)
from src.utils.logging_config import get_logger
from src.utils.markdown_utils import MarkdownProcessor

logger = get_logger(__name__)


class SmartTemplateEngine:
    """スマートテンプレートエンジン."""

    def __init__(self):
        """初期化."""
        self.markdown_processor = MarkdownProcessor()
        self.template_cache = {}
        logger.info("SmartTemplateEngine initialized")

    async def generate_checklist(self, request: TripRequest) -> TripChecklist:
        """チェックリストを生成."""
        logger.info(
            f"Generating checklist for {request.destination} "
            f"({request.start_date} to {request.end_date})"
        )

        # 1. テンプレート選択
        template_type = self._select_template(request)

        # 2. コンテキスト準備
        context = self._prepare_context(request)

        # 3. テンプレートレンダリング
        if template_type == "sapporo_business":
            # 札幌出張専用テンプレート
            rendered = self.markdown_processor.render_template(
                "sapporo_business.md",
                context
            )
        elif request.purpose == "business":
            # ビジネス用モジュラーテンプレート
            rendered = self.markdown_processor.combine_templates(
                "base_travel.md",
                "business.md",
                context=context
            )
        else:
            # レジャー用モジュラーテンプレート
            rendered = self.markdown_processor.combine_templates(
                "base_travel.md",
                "leisure.md",
                context=context
            )

        # 4. チェックリスト項目抽出
        items = self._extract_items_from_markdown(rendered)

        # 5. 調整適用（天気、地域、個人）
        adjusted_items = await self._apply_adjustments(items, request)

        # 6. チェックリストオブジェクト作成
        checklist = TripChecklist(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            purpose=request.purpose,
            items=adjusted_items,
            user_id=request.user_id,
            template_used=template_type
        )

        logger.info(
            f"Generated checklist with {len(checklist.items)} items "
            f"(ID: {checklist.id})"
        )

        return checklist

    def _select_template(self, request: TripRequest) -> TemplateType:
        """適切なテンプレートを選択."""
        # 札幌出張の特別処理
        if request.purpose == "business" and "札幌" in request.destination:
            return "sapporo_business"
        elif request.purpose == "business":
            return "domestic_business"
        else:
            return "leisure_domestic"

    def _prepare_context(self, request: TripRequest) -> dict:
        """テンプレート用のコンテキストを準備."""
        return {
            "destination": request.destination,
            "start_date": request.start_date.strftime("%Y年%m月%d日"),
            "end_date": request.end_date.strftime("%Y年%m月%d日"),
            "duration": request.duration,
            "purpose": "出張" if request.purpose == "business" else "レジャー",
            "transport_method": self._get_transport_display(request.transport_method),
            # 追加のコンテキスト
            "hotel_name": request.accommodation or "未定",
            "business_cards_count": "100" if request.duration >= 3 else "50",
            "recommended_cash": f"{10000 + (request.duration * 10000):,}",
        }

    def _get_transport_display(self, transport: Optional[str]) -> str:
        """交通手段の表示名を取得."""
        transport_map = {
            "airplane": "飛行機",
            "train": "新幹線・電車",
            "car": "車",
            "bus": "バス",
            "other": "その他",
        }
        return transport_map.get(transport, "未定")

    def _extract_items_from_markdown(self, markdown: str) -> list[ChecklistItem]:
        """Markdownからチェックリスト項目を抽出."""
        items = []
        raw_items = self.markdown_processor.extract_checklist_items(markdown)

        for category_name, item_name, checked in raw_items:
            # カテゴリ名を正規化
            category = self._normalize_category(category_name)

            item = ChecklistItem(
                name=item_name,
                category=category,
                checked=checked,
                auto_added=False
            )
            items.append(item)

        return items

    def _normalize_category(self, category_name: str) -> ItemCategory:
        """カテゴリ名を正規化."""
        category_map = {
            "移動関連": "移動関連",
            "仕事関連": "仕事関連",
            "ビジネス": "仕事関連",
            "服装": "服装・身だしなみ",
            "身だしなみ": "服装・身だしなみ",
            "生活用品": "生活用品",
            "基本生活用品": "生活用品",
            "金銭": "金銭関連",
            "支払い": "金銭関連",
            "予算": "金銭関連",
            "天気": "天気対応",
            "気候": "天気対応",
            "地域": "地域特有",
            "特有": "地域特有",
        }

        # キーワードマッチング
        for keyword, category in category_map.items():
            if keyword in category_name:
                return category

        return "生活用品"  # デフォルト

    async def _apply_adjustments(
        self,
        items: list[ChecklistItem],
        request: TripRequest
    ) -> list[ChecklistItem]:
        """各種調整を適用."""
        adjusted_items = items.copy()

        # 1. 地域調整
        regional_items = self._get_regional_adjustments(request)
        adjusted_items.extend(regional_items)

        # 2. 期間調整
        duration_items = self._get_duration_adjustments(request)
        adjusted_items.extend(duration_items)

        # 3. 交通手段調整
        if request.transport_method:
            transport_items = self._get_transport_adjustments(request)
            adjusted_items.extend(transport_items)

        # 4. 天気調整（Phase 2で実装）
        if settings.is_feature_enabled("weather"):
            # TODO: 天気API連携
            pass

        # 5. 個人調整（Phase 3で実装）
        # TODO: 個人履歴に基づく調整

        return adjusted_items

    def _get_regional_adjustments(self, request: TripRequest) -> list[ChecklistItem]:
        """地域特性による調整."""
        items = []
        month = request.start_date.month

        if "北海道" in request.destination or "札幌" in request.destination:
            # 北海道特有の調整
            if month in [10, 11, 12, 1, 2, 3]:
                items.append(ChecklistItem(
                    name="防寒着（ダウンジャケット等）",
                    category="服装・身だしなみ",
                    auto_added=True,
                    reason="北海道の冬は寒いため"
                ))
                items.append(ChecklistItem(
                    name="手袋・マフラー",
                    category="服装・身だしなみ",
                    auto_added=True,
                    reason="防寒対策"
                ))

            if month in [6, 7, 8]:
                items.append(ChecklistItem(
                    name="薄手の上着",
                    category="服装・身だしなみ",
                    auto_added=True,
                    reason="北海道の夏は朝夕冷えるため"
                ))

        elif "沖縄" in request.destination:
            # 沖縄特有の調整
            items.append(ChecklistItem(
                name="日焼け止め（SPF50+）",
                category="生活用品",
                auto_added=True,
                reason="沖縄の強い日差し対策"
            ))
            items.append(ChecklistItem(
                name="虫除けスプレー",
                category="生活用品",
                auto_added=True,
                reason="亜熱帯気候のため"
            ))

        return items

    def _get_duration_adjustments(self, request: TripRequest) -> list[ChecklistItem]:
        """期間による調整."""
        items = []

        if request.duration >= 4:
            # 長期滞在の調整
            items.append(ChecklistItem(
                name="洗濯用洗剤（小分け）",
                category="生活用品",
                auto_added=True,
                reason=f"{request.duration}泊の長期滞在のため"
            ))
            items.append(ChecklistItem(
                name="予備の着替え（追加分）",
                category="服装・身だしなみ",
                auto_added=True,
                reason="長期滞在のため"
            ))

        if request.duration <= 1:
            # 短期滞在の調整（軽量化）
            # 実際には削除する項目があるが、今回は追加のみ
            pass

        return items

    def _get_transport_adjustments(self, request: TripRequest) -> list[ChecklistItem]:
        """交通手段による調整."""
        items = []

        if request.transport_method == "airplane":
            items.extend([
                ChecklistItem(
                    name="機内持ち込み用透明袋（液体用）",
                    category="移動関連",
                    auto_added=True,
                    reason="飛行機の液体制限対応"
                ),
                ChecklistItem(
                    name="耳栓・アイマスク",
                    category="移動関連",
                    auto_added=True,
                    reason="機内快適グッズ"
                ),
            ])

        elif request.transport_method == "car":
            items.extend([
                ChecklistItem(
                    name="ETCカード",
                    category="移動関連",
                    auto_added=True,
                    reason="車移動のため"
                ),
                ChecklistItem(
                    name="車載充電器",
                    category="移動関連",
                    auto_added=True,
                    reason="車移動のため"
                ),
            ])

        return items

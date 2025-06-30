"""
Smart template engine for checklist generation.

条件に応じてテンプレートを自動調整し、最適なチェックリストを生成します。
"""

from typing import Any

from src.config.settings import settings
from src.core.transport_rules import TransportRulesLoader
from src.core.weather_service import WeatherService
from src.models import (
    ChecklistItem,
    ItemCategory,
    TemplateType,
    TripChecklist,
    TripRequest,
    WeatherAPIError,
    WeatherDataDict,
)
from src.utils.logging_config import get_logger
from src.utils.markdown_utils import MarkdownProcessor

logger = get_logger(__name__)


class SmartTemplateEngine:
    """スマートテンプレートエンジン."""

    def __init__(self) -> None:
        """初期化."""
        self.markdown_processor = MarkdownProcessor()
        self.weather_service = WeatherService() if settings.is_feature_enabled("weather") else None
        self.transport_rules = TransportRulesLoader()
        self.template_cache: dict[str, Any] = {}
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
        if request.purpose == "business":
            # ビジネス用モジュラーテンプレート
            rendered = self.markdown_processor.combine_templates(
                "base_travel.md", "business.md", context=context
            )
        else:
            # レジャー用モジュラーテンプレート
            rendered = self.markdown_processor.combine_templates(
                "base_travel.md", "leisure.md", context=context
            )

        # 4. チェックリスト項目抽出
        items = self._extract_items_from_markdown(rendered)

        # 5. 調整適用（天気、地域、個人）
        adjusted_items = await self._apply_adjustments(items, request)

        # 6. 天気データを取得（オプション）
        weather_data = None
        if settings.is_feature_enabled("weather") and self.weather_service:
            try:
                weather_summary = await self.weather_service.get_weather_summary(
                    request.destination, request.start_date, request.end_date
                )
                weather_data = WeatherDataDict(
                    average_temperature=weather_summary.avg_temperature,
                    max_temperature=weather_summary.max_temperature,
                    min_temperature=weather_summary.min_temperature,
                    rain_probability=weather_summary.max_rain_probability,
                    conditions="rainy" if weather_summary.has_rain else "sunny",
                    forecast_date=request.start_date.isoformat(),
                )
            except WeatherAPIError as e:
                logger.warning(f"Failed to get weather data: {e}")

        # 7. チェックリストオブジェクト作成
        checklist = TripChecklist(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            purpose=request.purpose,
            items=adjusted_items,
            user_id=request.user_id,
            template_used=template_type,
            weather_data=weather_data,
        )

        logger.info(f"Generated checklist with {len(checklist.items)} items (ID: {checklist.id})")

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

    def _prepare_context(self, request: TripRequest) -> dict[str, Any]:
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

    def _get_transport_display(self, transport: str | None) -> str:
        """交通手段の表示名を取得."""
        transport_map: dict[str, str] = {
            "airplane": "飛行機",
            "train": "新幹線・電車",
            "car": "車",
            "bus": "バス",
            "other": "その他",
        }
        return transport_map.get(transport or "", "未定")

    def _extract_items_from_markdown(self, markdown: str) -> list[ChecklistItem]:
        """Markdownからチェックリスト項目を抽出."""
        items = []
        raw_items = self.markdown_processor.extract_checklist_items(markdown)

        for category_name, item_name, checked in raw_items:
            # カテゴリ名を正規化
            category = self._normalize_category(category_name)

            item = ChecklistItem(
                name=item_name, category=category, checked=checked, auto_added=False
            )
            items.append(item)

        return items

    def _normalize_category(self, category_name: str) -> ItemCategory:
        """カテゴリ名を正規化."""
        category_map: dict[str, ItemCategory] = {
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

        # デフォルトとして生活用品を返す
        default_category: ItemCategory = "生活用品"
        return default_category

    async def _apply_adjustments(
        self, items: list[ChecklistItem], request: TripRequest
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

        # 4. 天気調整
        weather_items = await self._get_weather_adjustments(request)
        adjusted_items.extend(weather_items)

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
                items.append(
                    ChecklistItem(
                        name="防寒着（ダウンジャケット等）",
                        category="服装・身だしなみ",
                        auto_added=True,
                        reason="北海道の冬は寒いため",
                    )
                )
                items.append(
                    ChecklistItem(
                        name="手袋・マフラー",
                        category="服装・身だしなみ",
                        auto_added=True,
                        reason="防寒対策",
                    )
                )

            if month in [6, 7, 8]:
                items.append(
                    ChecklistItem(
                        name="薄手の上着",
                        category="服装・身だしなみ",
                        auto_added=True,
                        reason="北海道の夏は朝夕冷えるため",
                    )
                )

        elif "沖縄" in request.destination:
            # 沖縄特有の調整
            items.append(
                ChecklistItem(
                    name="日焼け止め（SPF50+）",
                    category="生活用品",
                    auto_added=True,
                    reason="沖縄の強い日差し対策",
                )
            )
            items.append(
                ChecklistItem(
                    name="虫除けスプレー",
                    category="生活用品",
                    auto_added=True,
                    reason="亜熱帯気候のため",
                )
            )

        return items

    def _get_duration_adjustments(self, request: TripRequest) -> list[ChecklistItem]:
        """期間による調整."""
        items = []

        if request.duration >= 4:
            # 長期滞在の調整
            items.append(
                ChecklistItem(
                    name="洗濯用洗剤（小分け）",
                    category="生活用品",
                    auto_added=True,
                    reason=f"{request.duration}泊の長期滞在のため",
                )
            )
            items.append(
                ChecklistItem(
                    name="予備の着替え（追加分）",
                    category="服装・身だしなみ",
                    auto_added=True,
                    reason="長期滞在のため",
                )
            )

        if request.duration <= 1:
            # 短期滞在の調整（軽量化）
            # 実際には削除する項目があるが、今回は追加のみ
            pass

        return items

    def _get_transport_adjustments(self, request: TripRequest) -> list[ChecklistItem]:
        """交通手段による調整."""
        if not request.transport_method:
            return []

        # 追加条件の設定
        additional_conditions: dict[str, Any] = {}

        # 新幹線かどうか（より詳細な判定）
        if request.transport_method == "train":
            # 新幹線駅がある都市のリスト
            shinkansen_cities = [
                "東京",
                "品川",
                "新横浜",
                "小田原",
                "熱海",
                "三島",
                "新富士",
                "静岡",
                "掛川",
                "浜松",
                "豊橋",
                "三河安城",
                "名古屋",
                "岐阜羽島",
                "米原",
                "京都",
                "新大阪",
                "新神戸",
                "西明石",
                "姫路",
                "岡山",
                "福山",
                "広島",
                "新山口",
                "小倉",
                "博多",
                "仙台",
                "盛岡",
                "新青森",
                "新函館北斗",
                "金沢",
                "富山",
                "長野",
                "高崎",
                "大宮",
                "鹿児島",
                "熊本",
                "長崎",
            ]
            # 主要都市間の移動なら新幹線の可能性が高い
            is_shinkansen = any(city in request.destination for city in shinkansen_cities)
            additional_conditions["is_shinkansen"] = is_shinkansen

            # 移動距離の推定（簡易版）
            if request.duration >= 2 or any(
                city in request.destination for city in ["札幌", "福岡", "仙台", "広島"]
            ):
                additional_conditions["long_distance"] = True

        # バスの詳細判定
        if request.transport_method == "bus":
            # 長距離移動の可能性を判定
            is_long_distance = request.duration >= 1  # 1泊以上なら高速バスの可能性大
            additional_conditions["is_highway"] = is_long_distance

            # 夜行バスの判定（宿泊を伴わない長距離移動の可能性）
            if request.duration == 0 and any(
                city in request.destination for city in ["大阪", "名古屋", "仙台", "広島"]
            ):
                additional_conditions["night_bus"] = True

        # 車の詳細判定
        if request.transport_method == "car":
            # レンタカーの可能性を判定（観光地や空港近くの目的地）
            tourist_areas = ["沖縄", "北海道", "石垣", "宮古", "屋久島", "小豆島"]
            additional_conditions["is_rental"] = any(
                area in request.destination for area in tourist_areas
            )

            # 移動距離の推定
            additional_conditions["distance"] = 200 if request.duration >= 2 else 100

        # その他の交通手段
        if request.transport_method == "other":
            # デフォルトで自転車を想定
            additional_conditions["sub_method"] = "bicycle"

        # 共通の長距離判定
        additional_conditions["long_distance"] = request.duration >= 2

        # TransportRulesLoaderを使用してアイテムを取得
        items = self.transport_rules.get_transport_items(
            transport_method=request.transport_method,
            trip_duration=request.duration,
            is_domestic=True,  # 現在は国内のみ対応
            month=request.start_date.month,
            additional_conditions=additional_conditions,
        )

        logger.info(
            f"Transport adjustments for {request.transport_method}: "
            f"{len(items)} items added (conditions: {additional_conditions})"
        )

        return items

    async def _get_weather_adjustments(self, request: TripRequest) -> list[ChecklistItem]:
        """天気予報による調整."""
        items: list[ChecklistItem] = []

        if not settings.is_feature_enabled("weather") or not self.weather_service:
            return items

        try:
            # 天気予報を取得
            weather_summary = await self.weather_service.get_weather_summary(
                request.destination, request.start_date, request.end_date
            )
            logger.info(
                f"Weather summary for {request.destination}: "
                f"Rain: {weather_summary.has_rain}, "
                f"Temp: {weather_summary.min_temperature:.1f}-"
                f"{weather_summary.max_temperature:.1f}°C"
            )

            # 雨天対策
            if weather_summary.has_rain or weather_summary.max_rain_probability > 30:
                items.append(
                    ChecklistItem(
                        name="折り畳み傘",
                        category="天気対応",
                        auto_added=True,
                        reason=f"降水確率{weather_summary.max_rain_probability:.0f}%の予報",
                    )
                )

                if weather_summary.max_rain_probability > 60:
                    items.append(
                        ChecklistItem(
                            name="レインコート",
                            category="天気対応",
                            auto_added=True,
                            reason="高い降水確率のため",
                        )
                    )
                    items.append(
                        ChecklistItem(
                            name="防水バッグ・カバー",
                            category="天気対応",
                            auto_added=True,
                            reason="荷物の雨対策",
                        )
                    )

            # 気温対策
            if weather_summary.min_temperature < 10:
                items.append(
                    ChecklistItem(
                        name="防寒着（ジャケット・コート）",
                        category="服装・身だしなみ",
                        auto_added=True,
                        reason=f"最低気温{weather_summary.min_temperature:.1f}°Cの予報",
                    )
                )

                if weather_summary.min_temperature < 5:
                    items.append(
                        ChecklistItem(
                            name="ホッカイロ",
                            category="天気対応",
                            auto_added=True,
                            reason="寒さ対策",
                        )
                    )

            if weather_summary.max_temperature > 30:
                items.append(
                    ChecklistItem(
                        name="日焼け止め（SPF30以上）",
                        category="生活用品",
                        auto_added=True,
                        reason=f"最高気温{weather_summary.max_temperature:.1f}°Cの予報",
                    )
                )
                items.append(
                    ChecklistItem(
                        name="冷却グッズ（冷却タオル等）",
                        category="生活用品",
                        auto_added=True,
                        reason="暑さ対策",
                    )
                )
                items.append(
                    ChecklistItem(
                        name="水分補給用ボトル",
                        category="生活用品",
                        auto_added=True,
                        reason="熟中症対策",
                    )
                )

            # 特殊な天気条件
            if "Snow" in weather_summary.weather_conditions:
                items.append(
                    ChecklistItem(
                        name="滑り止め付き靴",
                        category="服装・身だしなみ",
                        auto_added=True,
                        reason="雪予報のため",
                    )
                )

            if "Wind" in weather_summary.weather_conditions:
                items.append(
                    ChecklistItem(
                        name="ウィンドブレーカー",
                        category="服装・身だしなみ",
                        auto_added=True,
                        reason="強風予報のため",
                    )
                )

            return items

        except WeatherAPIError as e:
            logger.warning(f"Failed to get weather adjustments: {e}")
            return items

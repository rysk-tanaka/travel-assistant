"""
Transport rules loader for enhanced transport adjustments.

このモジュールは、交通手段別の詳細なルールをYAMLファイルから読み込み、
条件に応じた適切な持ち物を提供します。
"""

from pathlib import Path
from typing import Any

import yaml

from src.models import ChecklistItem, ItemCategory, TransportMethod
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TransportRulesLoader:
    """交通手段別ルールの読み込みと処理."""

    def __init__(self) -> None:
        """初期化."""
        self.rules_file = Path(__file__).parent.parent / "data" / "transport_rules.yaml"
        self._rules_cache: dict[str, Any] | None = None
        logger.info(f"TransportRulesLoader initialized with rules file: {self.rules_file}")

    def load_rules(self) -> dict[str, Any]:
        """ルールファイルを読み込み."""
        if self._rules_cache is not None:
            return self._rules_cache

        try:
            with self.rules_file.open(encoding="utf-8") as f:
                self._rules_cache = yaml.safe_load(f)
                logger.info("Transport rules loaded successfully")
                return self._rules_cache
        except FileNotFoundError:
            logger.error(f"Transport rules file not found: {self.rules_file}")
            return {"transport_methods": {}}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse transport rules YAML: {e}")
            return {"transport_methods": {}}

    def get_transport_items(
        self,
        transport_method: TransportMethod,
        trip_duration: int,
        is_domestic: bool = True,
        month: int | None = None,
        additional_conditions: dict[str, Any] | None = None,
    ) -> list[ChecklistItem]:
        """交通手段に基づくアイテムを取得.

        Args:
            transport_method: 交通手段
            trip_duration: 旅行期間（日数）
            is_domestic: 国内旅行かどうか
            month: 旅行月（季節調整用）
            additional_conditions: 追加条件（long_distance, night_bus等）

        Returns:
            ChecklistItem のリスト
        """
        rules = self.load_rules()
        transport_rules = rules.get("transport_methods", {})

        if transport_method not in transport_rules:
            logger.warning(f"No rules found for transport method: {transport_method}")
            return []

        method_rules = transport_rules[transport_method]
        items = []
        conditions = additional_conditions or {}

        # 基本的な条件を追加
        conditions["duration"] = trip_duration
        conditions["is_domestic"] = is_domestic
        conditions["month"] = month

        # 交通手段別の処理
        if transport_method == "airplane":
            items.extend(self._process_airplane_rules(method_rules, conditions))
        elif transport_method == "train":
            items.extend(self._process_train_rules(method_rules, conditions))
        elif transport_method == "car":
            items.extend(self._process_car_rules(method_rules, conditions))
        elif transport_method == "bus":
            items.extend(self._process_bus_rules(method_rules, conditions))
        elif transport_method == "other":
            items.extend(self._process_other_rules(method_rules, conditions))

        return items

    def _process_airplane_rules(
        self, method_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """飛行機のルールを処理."""
        items = []

        # 国内/国際で分岐
        if conditions.get("is_domestic", True):
            domestic_rules = method_rules.get("domestic", {})

            # 制限事項
            restrictions = domestic_rules.get("restrictions", {})
            for restriction_type, restriction_data in restrictions.items():
                if restriction_type == "prohibited":
                    continue  # 警告のみなのでスキップ

                for item_data in restriction_data.get("items", []):
                    items.append(self._create_checklist_item(item_data))

            # 推奨事項
            recommendations = domestic_rules.get("recommendations", {})
            for rec_type, rec_data in recommendations.items():
                if rec_type == "timing":
                    continue  # タイミングの推奨事項はスキップ

                for item_data in rec_data.get("items", []):
                    if self._check_condition(item_data, conditions):
                        items.append(self._create_checklist_item(item_data))
        else:
            # 国際線の追加アイテム
            international_rules = method_rules.get("international", {})
            additional_items = international_rules.get("additional_items", {})

            for _category, category_data in additional_items.items():
                for item_data in category_data.get("items", []):
                    if not item_data.get("conditional", False):
                        items.append(self._create_checklist_item(item_data))

        return items

    def _process_train_rules(
        self, method_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """新幹線・電車のルールを処理."""
        items = []

        # 新幹線の場合
        if conditions.get("is_shinkansen", True):
            shinkansen_rules = method_rules.get("shinkansen", {}).get("items", {})

            for _category, category_items in shinkansen_rules.items():
                for item_data in category_items:
                    if (
                        self._check_condition(item_data, conditions)
                        and item_data.get("type") != "task"
                    ):
                        items.append(self._create_checklist_item(item_data))
        else:
            # 在来線の場合
            local_rules = method_rules.get("local_train", {}).get("items", [])
            for item_data in local_rules:
                if item_data.get("type") != "app":  # アプリ推奨は除外
                    items.append(self._create_checklist_item(item_data))

        return items

    def _process_car_rules(
        self, method_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """車のルールを処理."""
        if conditions.get("is_rental", False):
            return self._process_rental_car_rules(method_rules, conditions)
        else:
            return self._process_personal_car_rules(method_rules, conditions)

    def _process_rental_car_rules(
        self, method_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """レンタカーのルールを処理."""
        items = []
        rental_rules = method_rules.get("rental_car", {})

        for item_data in rental_rules.get("additional_items", []):
            if item_data.get("type") != "task":
                items.append(self._create_checklist_item(item_data))

        return items

    def _process_personal_car_rules(
        self, method_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """自家用車のルールを処理."""
        items = []
        personal_rules = method_rules.get("personal_car", {})

        # 各カテゴリのアイテム
        items.extend(self._process_car_category_items(personal_rules, conditions))

        # 季節別アイテム
        items.extend(self._process_car_seasonal_items(personal_rules, conditions))

        return items

    def _process_car_category_items(
        self, personal_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """車のカテゴリ別アイテムを処理."""
        items = []

        for _category, category_data in personal_rules.get("items", {}).items():
            if isinstance(category_data, list):
                for item_data in category_data:
                    if self._check_condition(item_data, conditions) and item_data.get(
                        "type"
                    ) not in ["task", "check", "equipment"]:
                        items.append(self._create_checklist_item(item_data))

        return items

    def _process_car_seasonal_items(
        self, personal_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """車の季節別アイテムを処理."""
        items: list[ChecklistItem] = []
        month = conditions.get("month")

        if not month:
            return items

        seasonal_rules = personal_rules.get("seasonal", {})

        # 冬季・夏季の判定と処理
        season_map = {"winter": [12, 1, 2, 3], "summer": [6, 7, 8, 9]}

        for season, months in season_map.items():
            if month in months:
                for item_data in seasonal_rules.get(season, []):
                    if month in item_data.get("months", []):
                        items.append(self._create_checklist_item(item_data))

        return items

    def _process_bus_rules(
        self, method_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """バスのルールを処理."""
        items = []

        # 高速バス/夜行バス
        if conditions.get("is_highway", True):
            highway_rules = method_rules.get("highway_bus", {}).get("items", {})

            for _category, category_items in highway_rules.items():
                for item_data in category_items:
                    if self._check_condition(item_data, conditions):
                        items.append(self._create_checklist_item(item_data))
        else:
            # 路線バス
            local_rules = method_rules.get("local_bus", {}).get("items", [])
            for item_data in local_rules:
                if self._check_condition(item_data, conditions):
                    items.append(self._create_checklist_item(item_data))

        return items

    def _process_other_rules(
        self, method_rules: dict[str, Any], conditions: dict[str, Any]
    ) -> list[ChecklistItem]:
        """その他の交通手段のルールを処理."""
        items = []

        # 自転車、バイクなど
        sub_method = conditions.get("sub_method", "bicycle")
        if sub_method in method_rules:
            sub_rules = method_rules[sub_method].get("items", [])
            for item_data in sub_rules:
                if self._check_condition(item_data, conditions):
                    items.append(self._create_checklist_item(item_data))

        return items

    def _check_condition(self, item_data: dict[str, Any], conditions: dict[str, Any]) -> bool:
        """条件チェック."""
        if "condition" not in item_data:
            return True

        condition_str = item_data["condition"]

        # 簡単な条件評価（セキュリティ注意: evalは使わない）
        if ">=" in condition_str:
            parts = condition_str.split(">=")
            if len(parts) == 2:
                param = parts[0].strip()
                value = int(parts[1].strip())
                return bool(conditions.get(param, 0) >= value)

        # その他の条件はキーの存在チェック
        return bool(conditions.get(condition_str, False))

    def _create_checklist_item(self, item_data: dict[str, Any]) -> ChecklistItem:
        """アイテムデータからChecklistItemを作成."""
        # カテゴリ名を正規化
        category_map = {
            "移動関連": "移動関連",
            "生活用品": "生活用品",
            "金銭関連": "金銭関連",
            "天気対応": "天気対応",
            "服装・身だしなみ": "服装・身だしなみ",
        }

        category_str = item_data.get("category", "移動関連")
        category: ItemCategory = category_map.get(category_str, "移動関連")  # type: ignore

        return ChecklistItem(
            name=item_data["name"],
            category=category,
            auto_added=True,
            reason=item_data.get("reason", "交通手段別の推奨アイテム"),
        )

    def get_recommendations(self, transport_method: TransportMethod) -> list[str]:
        """交通手段別の推奨事項を取得."""
        rules = self.load_rules()
        transport_rules = rules.get("transport_methods", {})
        general_recs = rules.get("general_recommendations", {})

        recommendations = []

        # 全交通手段共通
        recommendations.extend(general_recs.get("all_methods", []))

        # 交通手段別
        if transport_method in transport_rules:
            method_rules = transport_rules[transport_method]

            # 飛行機の場合
            if transport_method == "airplane":
                domestic = method_rules.get("domestic", {})
                timing = domestic.get("recommendations", {}).get("timing", {})
                recommendations.extend(timing.get("recommendations", []))

            # 新幹線の場合
            elif transport_method == "train":
                shinkansen = method_rules.get("shinkansen", {})
                recommendations.extend(shinkansen.get("recommendations", []))

            # バスの場合
            elif transport_method == "bus":
                highway = method_rules.get("highway_bus", {})
                recommendations.extend(highway.get("recommendations", []))

        return recommendations

"""
Test for transport rules loader.

交通手段別ルールローダーのテスト。
"""

import pytest

from src.core.transport_rules import TransportRulesLoader
from src.models import ChecklistItem


class TestTransportRulesLoader:
    """TransportRulesLoaderのテスト."""

    @pytest.fixture
    def loader(self) -> TransportRulesLoader:
        """TransportRulesLoaderのインスタンス."""
        return TransportRulesLoader()

    def test_load_rules(self, loader: TransportRulesLoader) -> None:
        """ルールファイルの読み込みテスト."""
        rules = loader.load_rules()

        # 基本構造の確認
        assert "transport_methods" in rules
        assert "general_recommendations" in rules

        # 各交通手段が定義されているか
        transport_methods = rules["transport_methods"]
        assert "airplane" in transport_methods
        assert "train" in transport_methods
        assert "car" in transport_methods
        assert "bus" in transport_methods
        assert "other" in transport_methods

    def test_airplane_domestic_items(self, loader: TransportRulesLoader) -> None:
        """飛行機（国内）のアイテム取得テスト."""
        items = loader.get_transport_items(
            transport_method="airplane",
            trip_duration=2,
            is_domestic=True,
            month=6,
        )

        # 基本的なアイテムが含まれているか
        item_names = [item.name for item in items]
        assert "機内持ち込み用透明袋（1L以下）" in item_names
        assert "モバイルバッテリー（手荷物用）" in item_names

        # アイテムの属性確認
        for item in items:
            assert isinstance(item, ChecklistItem)
            assert item.auto_added is True
            assert item.reason is not None

    def test_airplane_international_items(self, loader: TransportRulesLoader) -> None:
        """飛行機（国際）のアイテム取得テスト."""
        items = loader.get_transport_items(
            transport_method="airplane",
            trip_duration=5,
            is_domestic=False,
            month=7,
        )

        item_names = [item.name for item in items]
        # 国際線特有のアイテム
        assert "パスポート" in item_names
        assert "現地通貨" in item_names
        assert "変換プラグ" in item_names

    def test_train_shinkansen_items(self, loader: TransportRulesLoader) -> None:
        """新幹線のアイテム取得テスト."""
        items = loader.get_transport_items(
            transport_method="train",
            trip_duration=2,
            is_domestic=True,
            month=5,
            additional_conditions={"is_shinkansen": True},
        )

        item_names = [item.name for item in items]
        assert "指定席券・乗車券" in item_names
        assert "車内用の飲み物・軽食" in item_names

    def test_car_personal_items(self, loader: TransportRulesLoader) -> None:
        """自家用車のアイテム取得テスト."""
        items = loader.get_transport_items(
            transport_method="car",
            trip_duration=3,
            is_domestic=True,
            month=8,
            additional_conditions={"is_rental": False},
        )

        item_names = [item.name for item in items]
        assert "運転免許証" in item_names
        assert "ETCカード" in item_names
        assert "車載充電器（シガーソケット）" in item_names

    def test_car_winter_items(self, loader: TransportRulesLoader) -> None:
        """車（冬季）のアイテム取得テスト."""
        items = loader.get_transport_items(
            transport_method="car",
            trip_duration=2,
            is_domestic=True,
            month=1,  # 1月
            additional_conditions={"is_rental": False},
        )

        item_names = [item.name for item in items]
        # 冬季特有のアイテム
        assert "スタッドレスタイヤ/チェーン" in item_names
        assert "解氷スプレー" in item_names

    def test_bus_highway_items(self, loader: TransportRulesLoader) -> None:
        """高速バスのアイテム取得テスト."""
        items = loader.get_transport_items(
            transport_method="bus",
            trip_duration=1,
            is_domestic=True,
            month=6,
            additional_conditions={"is_highway": True, "night_bus": True},
        )

        item_names = [item.name for item in items]
        assert "ネックピロー" in item_names
        assert "アイマスク・耳栓" in item_names
        assert "モバイルバッテリー" in item_names

    def test_condition_check(self, loader: TransportRulesLoader) -> None:
        """条件チェックのテスト."""
        # duration >= 2 の条件
        item_data = {"condition": "duration >= 2"}
        conditions = {"duration": 3}
        assert loader._check_condition(item_data, conditions) is True

        conditions = {"duration": 1}
        assert loader._check_condition(item_data, conditions) is False

        # キー存在チェック
        item_data = {"condition": "night_bus"}
        conditions = {"night_bus": True}
        assert loader._check_condition(item_data, conditions) is True

        conditions = {"night_bus": False}
        assert loader._check_condition(item_data, conditions) is False

    def test_recommendations(self, loader: TransportRulesLoader) -> None:
        """推奨事項の取得テスト."""
        # 飛行機の推奨事項
        recs = loader.get_recommendations("airplane")
        assert len(recs) > 0
        assert any("チケット" in rec for rec in recs)

        # 新幹線の推奨事項
        recs = loader.get_recommendations("train")
        assert len(recs) > 0

        # バスの推奨事項
        recs = loader.get_recommendations("bus")
        assert len(recs) > 0

    def test_empty_transport_method(self, loader: TransportRulesLoader) -> None:
        """未知の交通手段のテスト."""
        items = loader.get_transport_items(
            transport_method="unknown",  # 存在しない交通手段
            trip_duration=2,
            is_domestic=True,
        )

        assert items == []  # 空のリストが返される

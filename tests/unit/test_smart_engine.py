"""
Unit tests for smart_engine module.

スマートテンプレートエンジンのテストを実施します。
"""

from datetime import date

import pytest

from src.core.smart_engine import SmartTemplateEngine
from src.models import ChecklistItem, TripChecklist, TripRequest


@pytest.fixture
def engine() -> SmartTemplateEngine:
    """テスト用のSmartTemplateEngineインスタンス."""
    return SmartTemplateEngine()


@pytest.fixture
def sample_request() -> TripRequest:
    """テスト用のTripRequest."""
    return TripRequest(
        destination="札幌",
        start_date=date(2025, 6, 28),
        end_date=date(2025, 6, 30),
        purpose="business",
        user_id="test-user",
        transport_method="airplane",
        accommodation="札幌ビジネスホテル",
    )


def test_init(engine: SmartTemplateEngine):
    """初期化のテスト."""
    assert engine.markdown_processor is not None
    assert isinstance(engine.template_cache, dict)
    assert len(engine.template_cache) == 0


def test_select_template_sapporo_business(engine: SmartTemplateEngine):
    """札幌出張テンプレート選択."""
    request = TripRequest(
        destination="札幌",
        start_date=date(2025, 6, 28),
        end_date=date(2025, 6, 30),
        purpose="business",
        user_id="user123",
    )

    template_type = engine._select_template(request)
    assert template_type == "sapporo_business"


def test_select_template_general_business(engine: SmartTemplateEngine):
    """一般出張テンプレート選択."""
    request = TripRequest(
        destination="東京",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 2),
        purpose="business",
        user_id="user123",
    )

    template_type = engine._select_template(request)
    assert template_type == "domestic_business"


def test_select_template_leisure(engine: SmartTemplateEngine):
    """レジャーテンプレート選択."""
    request = TripRequest(
        destination="沖縄",
        start_date=date(2025, 8, 10),
        end_date=date(2025, 8, 15),
        purpose="leisure",
        user_id="user123",
    )

    template_type = engine._select_template(request)
    assert template_type == "leisure_domestic"


def test_prepare_context(engine: SmartTemplateEngine, sample_request: TripRequest):
    """テンプレート用コンテキストの準備."""
    context = engine._prepare_context(sample_request)

    assert context["destination"] == "札幌"
    assert context["start_date"] == "2025年06月28日"
    assert context["end_date"] == "2025年06月30日"
    assert context["duration"] == 2
    assert context["purpose"] == "出張"
    assert context["transport_method"] == "飛行機"
    assert context["hotel_name"] == "札幌ビジネスホテル"
    assert context["business_cards_count"] == "50"  # 2泊なので50枚
    assert context["recommended_cash"] == "30,000"  # 10000 + (2 * 10000)


def test_prepare_context_long_trip(engine: SmartTemplateEngine):
    """長期旅行のコンテキスト準備."""
    request = TripRequest(
        destination="大阪",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 5),
        purpose="business",
        user_id="user123",
    )

    context = engine._prepare_context(request)

    assert context["duration"] == 4
    assert context["business_cards_count"] == "100"  # 3泊以上なので100枚
    assert context["recommended_cash"] == "50,000"  # 10000 + (4 * 10000)


def test_get_transport_display(engine: SmartTemplateEngine):
    """交通手段の表示名取得."""
    assert engine._get_transport_display("airplane") == "飛行機"
    assert engine._get_transport_display("train") == "新幹線・電車"
    assert engine._get_transport_display("car") == "車"
    assert engine._get_transport_display("bus") == "バス"
    assert engine._get_transport_display("other") == "その他"
    assert engine._get_transport_display(None) == "未定"
    assert engine._get_transport_display("unknown") == "未定"


def test_normalize_category(engine: SmartTemplateEngine):
    """カテゴリ名の正規化."""
    assert engine._normalize_category("移動関連") == "移動関連"
    assert engine._normalize_category("仕事関連") == "仕事関連"
    assert engine._normalize_category("ビジネス") == "仕事関連"
    assert engine._normalize_category("服装") == "服装・身だしなみ"
    assert engine._normalize_category("身だしなみ") == "服装・身だしなみ"
    assert engine._normalize_category("生活用品") == "生活用品"
    assert engine._normalize_category("基本生活用品") == "生活用品"
    assert engine._normalize_category("金銭") == "金銭関連"
    assert engine._normalize_category("支払い") == "金銭関連"
    assert engine._normalize_category("予算") == "金銭関連"
    assert engine._normalize_category("天気") == "天気対応"
    assert engine._normalize_category("気候") == "天気対応"
    assert engine._normalize_category("地域") == "地域特有"
    assert engine._normalize_category("特有") == "地域特有"
    assert engine._normalize_category("その他") == "生活用品"  # デフォルト


def test_extract_items_from_markdown(engine: SmartTemplateEngine, monkeypatch):
    """Markdownからのアイテム抽出."""

    # markdown_processorをモック - monkeypatchを使用
    def mock_extract_checklist_items(markdown):
        return [
            ("移動関連", "パスポート", False),
            ("仕事関連", "ノートPC", False),
            ("ビジネス", "名刺", True),  # 正規化テスト
        ]

    monkeypatch.setattr(
        engine.markdown_processor,
        "extract_checklist_items",
        mock_extract_checklist_items,
    )

    markdown = "ダミーMarkdown"
    items = engine._extract_items_from_markdown(markdown)

    assert len(items) == 3
    assert items[0].name == "パスポート"
    assert items[0].category == "移動関連"
    assert items[0].checked is False
    assert items[0].auto_added is False

    assert items[1].name == "ノートPC"
    assert items[1].category == "仕事関連"

    assert items[2].name == "名刺"
    assert items[2].category == "仕事関連"  # ビジネス→仕事関連に正規化
    assert items[2].checked is True


def test_get_regional_adjustments_hokkaido_winter(engine: SmartTemplateEngine):
    """北海道冬季の地域調整."""
    request = TripRequest(
        destination="北海道札幌市",
        start_date=date(2025, 12, 20),
        end_date=date(2025, 12, 22),
        purpose="business",
        user_id="user123",
    )

    items = engine._get_regional_adjustments(request)

    assert len(items) == 2
    assert any(item.name == "防寒着（ダウンジャケット等）" for item in items)
    assert any(item.name == "手袋・マフラー" for item in items)
    assert all(item.auto_added for item in items)
    assert all(item.category == "服装・身だしなみ" for item in items)


def test_get_regional_adjustments_hokkaido_summer(engine: SmartTemplateEngine):
    """北海道夏季の地域調整."""
    request = TripRequest(
        destination="札幌",
        start_date=date(2025, 7, 15),
        end_date=date(2025, 7, 17),
        purpose="leisure",
        user_id="user123",
    )

    items = engine._get_regional_adjustments(request)

    assert len(items) == 1
    assert items[0].name == "薄手の上着"
    assert items[0].reason == "北海道の夏は朝夕冷えるため"


def test_get_regional_adjustments_okinawa(engine: SmartTemplateEngine):
    """沖縄の地域調整."""
    request = TripRequest(
        destination="沖縄県那覇市",
        start_date=date(2025, 8, 1),
        end_date=date(2025, 8, 5),
        purpose="leisure",
        user_id="user123",
    )

    items = engine._get_regional_adjustments(request)

    assert len(items) == 2
    assert any(item.name == "日焼け止め（SPF50+）" for item in items)
    assert any(item.name == "虫除けスプレー" for item in items)


def test_get_duration_adjustments_long_trip(engine: SmartTemplateEngine):
    """長期滞在の調整."""
    request = TripRequest(
        destination="東京",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 6),
        purpose="business",
        user_id="user123",
    )

    items = engine._get_duration_adjustments(request)

    assert len(items) == 2
    assert any(item.name == "洗濯用洗剤（小分け）" for item in items)
    assert any(item.name == "予備の着替え（追加分）" for item in items)
    assert all(item.auto_added for item in items)


def test_get_duration_adjustments_short_trip(engine: SmartTemplateEngine):
    """短期滞在の調整."""
    request = TripRequest(
        destination="大阪",
        start_date=date(2025, 7, 10),
        end_date=date(2025, 7, 11),
        purpose="business",
        user_id="user123",
    )

    items = engine._get_duration_adjustments(request)

    # 短期滞在では追加アイテムなし（現在の実装）
    assert len(items) == 0


def test_get_transport_adjustments_airplane(engine: SmartTemplateEngine):
    """飛行機利用時の調整."""
    request = TripRequest(
        destination="福岡",
        start_date=date(2025, 8, 1),
        end_date=date(2025, 8, 3),
        purpose="business",
        transport_method="airplane",
        user_id="user123",
    )

    items = engine._get_transport_adjustments(request)

    assert len(items) == 2
    assert any(item.name == "機内持ち込み用透明袋（液体用）" for item in items)
    assert any(item.name == "耳栓・アイマスク" for item in items)
    assert all(item.category == "移動関連" for item in items)


def test_get_transport_adjustments_car(engine: SmartTemplateEngine):
    """車利用時の調整."""
    request = TripRequest(
        destination="名古屋",
        start_date=date(2025, 9, 1),
        end_date=date(2025, 9, 2),
        purpose="leisure",
        transport_method="car",
        user_id="user123",
    )

    items = engine._get_transport_adjustments(request)

    assert len(items) == 2
    assert any(item.name == "ETCカード" for item in items)
    assert any(item.name == "車載充電器" for item in items)


@pytest.mark.asyncio
async def test_apply_adjustments(engine: SmartTemplateEngine, sample_request: TripRequest):
    """調整適用の統合テスト."""
    base_items = [
        ChecklistItem(name="基本アイテム1", category="移動関連"),
        ChecklistItem(name="基本アイテム2", category="生活用品"),
    ]

    adjusted_items = await engine._apply_adjustments(base_items, sample_request)

    # 基本アイテム + 地域調整(札幌6月:1) + 交通手段調整(飛行機:2)
    assert len(adjusted_items) >= 5

    # 基本アイテムが含まれている
    assert any(item.name == "基本アイテム1" for item in adjusted_items)
    assert any(item.name == "基本アイテム2" for item in adjusted_items)

    # 地域調整アイテムが含まれている（6月の札幌）
    assert any(item.name == "薄手の上着" for item in adjusted_items)

    # 交通手段調整アイテムが含まれている
    assert any("透明袋" in item.name for item in adjusted_items)


@pytest.mark.asyncio
async def test_generate_checklist_full_flow(
    engine: SmartTemplateEngine, sample_request: TripRequest, monkeypatch
):
    """チェックリスト生成の全体フロー."""

    # markdown_processorをモック - monkeypatchを使用
    class MockProcessor:
        def combine_templates(self, *args, **kwargs):
            self.combine_templates_called = True
            self.combine_templates_args = args
            return """
# 札幌出張チェックリスト

## 移動関連
- [ ] パスポート
- [ ] 航空券

## 仕事関連
- [ ] ノートPC
- [ ] 名刺
"""

        def extract_checklist_items(self, markdown):
            return [
                ("移動関連", "パスポート", False),
                ("移動関連", "航空券", False),
                ("仕事関連", "ノートPC", False),
                ("仕事関連", "名刺", False),
            ]

    mock_processor = MockProcessor()
    monkeypatch.setattr(engine, "markdown_processor", mock_processor)

    # チェックリスト生成
    checklist = await engine.generate_checklist(sample_request)

    # 基本的な属性の確認
    assert isinstance(checklist, TripChecklist)
    assert checklist.destination == "札幌"
    assert checklist.start_date == date(2025, 6, 28)
    assert checklist.end_date == date(2025, 6, 30)
    assert checklist.purpose == "business"
    assert checklist.user_id == "test-user"
    assert checklist.template_used == "sapporo_business"

    # アイテムの確認（基本4 + 調整で追加されたもの）
    assert len(checklist.items) >= 4

    # combine_templatesが正しく呼ばれたか
    assert mock_processor.combine_templates_called
    assert mock_processor.combine_templates_args[0] == "base_travel.md"
    assert mock_processor.combine_templates_args[1] == "business.md"


@pytest.mark.asyncio
async def test_generate_checklist_leisure(engine: SmartTemplateEngine, monkeypatch):
    """レジャー用チェックリスト生成."""
    request = TripRequest(
        destination="沖縄",
        start_date=date(2025, 8, 10),
        end_date=date(2025, 8, 15),
        purpose="leisure",
        user_id="test-user",
    )

    # markdown_processorをモック - monkeypatchを使用
    class MockProcessor:
        def combine_templates(self, *args, **kwargs):
            self.combine_templates_called = True
            self.combine_templates_args = args
            return "# レジャーチェックリスト"

        def extract_checklist_items(self, markdown):
            return []

    mock_processor = MockProcessor()
    monkeypatch.setattr(engine, "markdown_processor", mock_processor)

    await engine.generate_checklist(request)

    # レジャー用テンプレートが使用されたか確認
    assert mock_processor.combine_templates_called
    assert mock_processor.combine_templates_args[0] == "base_travel.md"
    assert mock_processor.combine_templates_args[1] == "leisure.md"

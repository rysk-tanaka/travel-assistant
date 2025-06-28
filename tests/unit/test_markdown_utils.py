"""
Unit tests for markdown_utils module.

Markdownテンプレート処理のテストを実施します。
"""

from pathlib import Path

import pytest

from src.models import TemplateNotFoundError
from src.utils.markdown_utils import MarkdownProcessor, TemplateData


# TemplateData Tests
def test_create_template_data():
    """基本的なテンプレートデータの作成."""
    metadata = {
        "template_type": "domestic_business",
        "template_version": "1.0",
        "last_updated": "2025-06-27",
        "customizable_fields": ["destination", "duration"],
    }
    content = "# テンプレート内容"

    template_data = TemplateData(metadata=metadata, content=content)

    assert template_data.metadata["template_type"] == "domestic_business"
    assert template_data.metadata["template_version"] == "1.0"
    assert template_data.metadata["last_updated"] == "2025-06-27"
    assert template_data.metadata["customizable_fields"] == ["destination", "duration"]
    assert template_data.content == "# テンプレート内容"


def test_from_file_success(tmp_path: Path):
    """ファイルからのテンプレートデータ読み込み（正常系）."""
    # テストファイルを作成
    test_file = tmp_path / "test_template.md"
    test_file.write_text(
        """---
template_type: domestic_business
template_version: 1.0
last_updated: 2025-06-27
customizable_fields:
  - destination
  - duration
---

# テンプレート本文

チェックリスト項目など
""",
        encoding="utf-8",
    )

    # 読み込みテスト
    template_data = TemplateData.from_file(test_file)

    assert template_data.metadata["template_type"] == "domestic_business"
    assert template_data.metadata["template_version"] == "1.0"
    assert "# テンプレート本文" in template_data.content


def test_from_file_not_found(tmp_path: Path):
    """存在しないファイルからの読み込み."""
    non_existent = tmp_path / "non_existent.md"

    with pytest.raises(TemplateNotFoundError, match="テンプレート読み込みエラー"):
        TemplateData.from_file(non_existent)


def test_from_file_invalid_format(tmp_path: Path):
    """不正な形式のファイルからの読み込み."""
    # Front Matterのないファイル
    test_file = tmp_path / "invalid.md"
    test_file.write_text("# 通常のMarkdown", encoding="utf-8")

    # エラーにはならず、メタデータがデフォルト値で読み込まれる
    template_data = TemplateData.from_file(test_file)
    assert template_data.metadata["template_type"] == "domestic_business"  # デフォルト値
    assert template_data.metadata["template_version"] == "1.0"


# MarkdownProcessor Tests
@pytest.fixture
def processor(tmp_path: Path) -> MarkdownProcessor:
    """テスト用のMarkdownProcessorインスタンス."""
    return MarkdownProcessor(template_dir=tmp_path)


@pytest.fixture
def create_test_template(tmp_path: Path):
    """テストテンプレートを作成するヘルパー関数."""

    def _create(filename: str, content: str):
        template_file = tmp_path / filename
        template_file.write_text(content, encoding="utf-8")
        return template_file

    return _create


def test_init_default_template_dir(monkeypatch):
    """デフォルトテンプレートディレクトリでの初期化."""

    # settingsをモック
    class MockSettings:
        TEMPLATE_PATH = "/default/path"

    monkeypatch.setattr("src.utils.markdown_utils.settings", MockSettings())
    processor = MarkdownProcessor()
    assert processor.template_dir == Path("/default/path")


def test_load_template_success(processor: MarkdownProcessor, create_test_template):
    """テンプレートの正常な読み込み."""
    create_test_template(
        "test.md",
        """---
template_type: domestic_business
template_version: 1.0
---
# テスト内容
""",
    )

    template_data = processor.load_template("test.md")
    assert template_data.metadata["template_type"] == "domestic_business"
    assert "# テスト内容" in template_data.content


def test_load_template_not_found(processor: MarkdownProcessor):
    """存在しないテンプレートの読み込み."""
    with pytest.raises(TemplateNotFoundError, match="テンプレートが見つかりません"):
        processor.load_template("non_existent.md")


def test_render_template_basic(processor: MarkdownProcessor, create_test_template):
    """基本的なテンプレートレンダリング."""
    create_test_template(
        "basic.md",
        """# {{destination}}旅行チェックリスト

期間: {{start_date}} ～ {{end_date}}
目的: {{purpose}}
""",
    )

    context = {
        "destination": "札幌",
        "start_date": "2025-06-28",
        "end_date": "2025-06-30",
        "purpose": "出張",
    }

    result = processor.render_template("basic.md", context)

    assert "# 札幌旅行チェックリスト" in result
    assert "期間: 2025-06-28 ～ 2025-06-30" in result
    assert "目的: 出張" in result


def test_render_template_with_defaults(processor: MarkdownProcessor, create_test_template):
    """デフォルト値を使用したレンダリング."""
    create_test_template(
        "defaults.md",
        """目的地: {{destination}}
ホテル: {{hotel_name}}
交通手段: {{transport_method}}
""",
    )

    # 一部のみコンテキストを提供
    context = {"destination": "東京"}

    result = processor.render_template("defaults.md", context)

    assert "目的地: 東京" in result
    assert "ホテル: 未定" in result  # デフォルト値
    assert "交通手段: 未定" in result  # デフォルト値


def test_render_template_error(processor: MarkdownProcessor):
    """テンプレートレンダリングエラー."""
    with pytest.raises(TemplateNotFoundError, match="テンプレートレンダリングエラー"):
        processor.render_template("non_existent.md", {})


def test_combine_templates(processor: MarkdownProcessor, create_test_template):
    """複数テンプレートの組み合わせ."""
    # ベーステンプレート
    create_test_template(
        "base.md",
        """# {{destination}}旅行

基本情報
""",
    )

    # モジュールディレクトリを作成
    modules_dir = processor.template_dir / "modules"
    modules_dir.mkdir()

    # モジュールテンプレート
    (modules_dir / "extra.md").write_text(
        """## 追加項目

- 項目1
- 項目2
""",
        encoding="utf-8",
    )

    context = {"destination": "大阪"}
    result = processor.combine_templates("base.md", "extra.md", context=context)

    assert "# 大阪旅行" in result
    assert "基本情報" in result
    assert "---" in result  # セパレータ
    assert "## 追加項目" in result
    assert "- 項目1" in result


def test_combine_templates_missing_module(processor: MarkdownProcessor, create_test_template):
    """存在しないモジュールを含む組み合わせ."""
    create_test_template("base.md", "# ベース")

    # モジュールが存在しなくても、ベーステンプレートは返される
    result = processor.combine_templates("base.md", "missing.md", context={})

    assert "# ベース" in result
    assert "---" not in result  # モジュールがないのでセパレータもない


def test_extract_checklist_items_basic(processor: MarkdownProcessor):
    """基本的なチェックリスト項目の抽出."""
    markdown = """# チェックリスト

## 移動関連
- [ ] パスポート
- [x] 航空券
- [ ] 身分証明書

### 仕事関連
- [ ] ノートPC
- [x] 名刺

普通のテキスト（無視される）
"""

    items = processor.extract_checklist_items(markdown)

    assert len(items) == 5
    assert items[0] == ("移動関連", "パスポート", False)
    assert items[1] == ("移動関連", "航空券", True)
    assert items[2] == ("移動関連", "身分証明書", False)
    assert items[3] == ("仕事関連", "ノートPC", False)
    assert items[4] == ("仕事関連", "名刺", True)


def test_extract_checklist_items_with_icons(processor: MarkdownProcessor):
    """アイコン付きカテゴリからの抽出."""
    markdown = """## 🎫 移動関連
- [ ] チケット

### 💼 仕事関連
- [x] 資料
"""

    items = processor.extract_checklist_items(markdown)

    assert len(items) == 2
    assert items[0] == ("移動関連", "チケット", False)
    assert items[1] == ("仕事関連", "資料", True)


def test_extract_checklist_items_empty(processor: MarkdownProcessor):
    """チェックリスト項目がない場合."""
    markdown = """# ただのドキュメント

これは普通のテキストです。
チェックリストはありません。
"""

    items = processor.extract_checklist_items(markdown)
    assert len(items) == 0


def test_update_checklist_status(processor: MarkdownProcessor):
    """チェックリスト状態の更新."""
    original = """## カテゴリ
- [ ] 項目1
- [x] 項目2
- [ ] 項目3

### サブカテゴリ
- [ ] 項目4
"""

    updates = {
        "項目1": True,
        "項目2": False,
        "項目4": True,
    }

    result = processor.update_checklist_status(original, updates)

    assert "- [x] 項目1" in result
    assert "- [ ] 項目2" in result
    assert "- [ ] 項目3" in result  # 更新なし
    assert "- [x] 項目4" in result


def test_update_checklist_status_preserve_indent(processor: MarkdownProcessor):
    """インデントを保持した更新."""
    original = """## カテゴリ
  - [ ] インデント項目
    - [ ] ネスト項目
"""

    updates = {"インデント項目": True}

    result = processor.update_checklist_status(original, updates)

    assert "  - [x] インデント項目" in result  # インデント保持
    assert "    - [ ] ネスト項目" in result  # 他の行は変更なし


def test_update_checklist_status_no_match(processor: MarkdownProcessor):
    """マッチしない項目の更新."""
    original = """- [ ] 項目A
- [ ] 項目B
"""

    updates = {"項目C": True}  # 存在しない項目

    result = processor.update_checklist_status(original, updates)

    # 元のまま変更されない
    assert result == original

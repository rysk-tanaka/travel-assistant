"""
Simple test to verify test framework is working.
"""


def test_simple():
    """シンプルなテスト."""
    assert 1 + 1 == 2


def test_list():
    """リストのテスト."""
    items = [1, 2, 3]
    assert len(items) == 3
    assert items[0] == 1


def test_string():
    """文字列のテスト."""
    text = "Hello"
    assert text.lower() == "hello"
    assert text.upper() == "HELLO"

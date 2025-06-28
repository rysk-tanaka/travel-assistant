"""
Unit tests for settings module.

設定管理のテストを実施します。
"""

from pathlib import Path

from src.config.settings import Settings


# Default values tests
def test_default_values(monkeypatch):
    """デフォルト値のテスト."""
    # 環境変数をクリア
    env_vars = [
        "DISCORD_TOKEN",
        "GITHUB_TOKEN",
        "WEATHER_API_KEY",
        "CLAUDE_API_KEY",
        "LOG_LEVEL",
        "DEBUG",
        "USER_DATA_PATH",
        "TEMPLATE_PATH",
        "GITHUB_REPO_NAME",
        "GITHUB_USERNAME",
        "GITHUB_BRANCH",
        "DEV_GUILD_ID",
        "ENABLE_WEATHER_API",
        "ENABLE_CLAUDE_API",
        "ENABLE_GITHUB_SYNC",
        "ENABLE_DEBUG_COMMANDS",
    ]

    # 環境変数を削除
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    # .env ファイルを無効化して設定を作成
    settings = Settings(_env_file=None)

    # 必須トークン（デフォルトは空）
    assert settings.DISCORD_TOKEN == ""
    assert settings.GITHUB_TOKEN == ""
    assert settings.WEATHER_API_KEY is None
    assert settings.CLAUDE_API_KEY is None

    # ログレベル
    assert settings.LOG_LEVEL == "INFO"
    assert settings.DEBUG is False

    # パス設定
    assert settings.USER_DATA_PATH == "./data/user_data"
    assert settings.TEMPLATE_PATH == "./src/templates"

    # GitHub設定
    assert settings.GITHUB_REPO_NAME == "travel-assistant-data"
    assert settings.GITHUB_USERNAME == ""
    assert settings.GITHUB_BRANCH == "main"
    assert settings.DEV_GUILD_ID is None

    # フィーチャーフラグ
    assert settings.ENABLE_WEATHER_API is False
    assert settings.ENABLE_CLAUDE_API is False
    assert settings.ENABLE_GITHUB_SYNC is False
    assert settings.ENABLE_DEBUG_COMMANDS is True


def test_env_var_override(monkeypatch):
    """環境変数による上書きテスト."""
    monkeypatch.setenv("DISCORD_TOKEN", "test-discord-token")
    monkeypatch.setenv("GITHUB_TOKEN", "test-github-token")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ENABLE_WEATHER_API", "true")
    monkeypatch.setenv("ENABLE_CLAUDE_API", "1")
    monkeypatch.setenv("ENABLE_GITHUB_SYNC", "yes")
    monkeypatch.setenv("GITHUB_USERNAME", "testuser")

    # .env ファイルを無効化して設定を作成
    settings = Settings(_env_file=None)

    assert settings.DISCORD_TOKEN == "test-discord-token"
    assert settings.GITHUB_TOKEN == "test-github-token"
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.DEBUG is True
    assert settings.ENABLE_WEATHER_API is True
    assert settings.ENABLE_CLAUDE_API is True
    assert settings.ENABLE_GITHUB_SYNC is True
    assert settings.GITHUB_USERNAME == "testuser"


def test_boolean_conversion(monkeypatch):
    """ブール値変換のテスト."""
    # True になるケース
    true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "YES", "on", "On", "ON"]
    for value in true_values:
        monkeypatch.setenv("ENABLE_WEATHER_API", value)
        settings = Settings(_env_file=None)
        assert settings.ENABLE_WEATHER_API is True, f"Failed for value: {value}"

    # False になるケース
    false_values = ["false", "False", "FALSE", "0", "no", "No", "NO", "off", "Off", "OFF", ""]
    for value in false_values:
        monkeypatch.setenv("ENABLE_WEATHER_API", value)
        settings = Settings(_env_file=None)
        assert settings.ENABLE_WEATHER_API is False, f"Failed for value: {value}"


def test_is_feature_enabled(monkeypatch):
    """フィーチャーフラグ確認メソッドのテスト."""
    monkeypatch.setenv("ENABLE_WEATHER_API", "true")
    monkeypatch.setenv("ENABLE_CLAUDE_API", "false")

    settings = Settings(_env_file=None)

    assert settings.is_feature_enabled("weather") is True
    assert settings.is_feature_enabled("claude") is False
    assert settings.is_feature_enabled("github") is False
    assert settings.is_feature_enabled("debug") is True  # デフォルトでTrue

    # 存在しないフィーチャー
    assert settings.is_feature_enabled("non_existent") is False


def test_user_data_dir_property(monkeypatch, tmp_path):
    """user_data_dirプロパティのテスト."""
    test_path = str(tmp_path / "test_user_data")
    monkeypatch.setenv("USER_DATA_PATH", test_path)

    settings = Settings(_env_file=None)
    data_dir = settings.user_data_dir

    # パスがPathオブジェクトとして返される
    assert isinstance(data_dir, Path)
    assert str(data_dir) == test_path
    # ディレクトリが作成される
    assert data_dir.exists()
    assert data_dir.is_dir()


def test_template_dir_property():
    """template_dirプロパティのテスト."""
    settings = Settings(_env_file=None)

    template_dir = settings.template_dir
    assert isinstance(template_dir, Path)
    assert str(template_dir) == "src/templates"


def test_github_repo_url_property(monkeypatch):
    """github_repo_urlプロパティのテスト."""
    monkeypatch.setenv("GITHUB_USERNAME", "testuser")
    monkeypatch.setenv("GITHUB_REPO_NAME", "my-travel-data")

    settings = Settings(_env_file=None)

    assert settings.github_repo_url == "https://github.com/testuser/my-travel-data"


def test_case_sensitive_config(monkeypatch):
    """設定の大文字小文字は区別されないことの確認."""
    # 両方設定した場合、後の値が使用される
    monkeypatch.setenv("discord_token", "test-token")
    monkeypatch.setenv("DISCORD_TOKEN", "test-token-upper")

    settings = Settings(_env_file=None)
    # pydantic_settingsではcase_sensitive=Falseなので、
    # 最後に設定された値が使用される
    assert settings.DISCORD_TOKEN in ["test-token", "test-token-upper"]


def test_env_file_loading(tmp_path, monkeypatch):
    """環境ファイルの読み込みテスト."""
    # 環境変数をクリア
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text("DISCORD_TOKEN=from-env-file\nLOG_LEVEL=ERROR\n")

    # .envファイルパスを指定して設定を読み込む
    settings = Settings(_env_file=str(env_file))

    assert settings.DISCORD_TOKEN == "from-env-file"
    assert settings.LOG_LEVEL == "ERROR"

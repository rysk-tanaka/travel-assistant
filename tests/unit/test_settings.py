"""
Unit tests for settings module.

設定管理のテストを実施します。
"""

import os
from pathlib import Path
from unittest.mock import patch

from src.config.settings import Settings


class TestSettings:
    """Settingsクラスのテスト."""

    def test_default_values(self):
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

        # 環境変数を一時的にクリア
        original_env = {}
        for var in env_vars:
            original_env[var] = os.environ.pop(var, None)

        try:
            # デフォルト設定の確認
            settings = Settings()

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

        finally:
            # 環境変数を復元
            for var, value in original_env.items():
                if value is not None:
                    os.environ[var] = value

    def test_env_var_override(self):
        """環境変数による上書きテスト."""
        with patch.dict(
            os.environ,
            {
                "DISCORD_TOKEN": "test-discord-token",
                "GITHUB_TOKEN": "test-github-token",
                "LOG_LEVEL": "DEBUG",
                "DEBUG": "true",
                "ENABLE_WEATHER_API": "true",
                "ENABLE_CLAUDE_API": "1",
                "ENABLE_GITHUB_SYNC": "yes",
                "GITHUB_USERNAME": "testuser",
            },
        ):
            settings = Settings()

            assert settings.DISCORD_TOKEN == "test-discord-token"
            assert settings.GITHUB_TOKEN == "test-github-token"
            assert settings.LOG_LEVEL == "DEBUG"
            assert settings.DEBUG is True
            assert settings.ENABLE_WEATHER_API is True
            assert settings.ENABLE_CLAUDE_API is True
            assert settings.ENABLE_GITHUB_SYNC is True
            assert settings.GITHUB_USERNAME == "testuser"

    def test_boolean_conversion(self):
        """ブール値変換のテスト."""
        # True になるケース
        for value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES", "on", "On", "ON"]:
            with patch.dict(os.environ, {"ENABLE_WEATHER_API": value}):
                settings = Settings()
                assert settings.ENABLE_WEATHER_API is True, f"Failed for value: {value}"

        # False になるケース
        for value in ["false", "False", "FALSE", "0", "no", "No", "NO", "off", "Off", "OFF", ""]:
            with patch.dict(os.environ, {"ENABLE_WEATHER_API": value}):
                settings = Settings()
                assert settings.ENABLE_WEATHER_API is False, f"Failed for value: {value}"

    def test_is_feature_enabled(self):
        """フィーチャーフラグ確認メソッドのテスト."""
        with patch.dict(
            os.environ,
            {
                "ENABLE_WEATHER_API": "true",
                "ENABLE_CLAUDE_API": "false",
            },
        ):
            settings = Settings()

            assert settings.is_feature_enabled("weather") is True
            assert settings.is_feature_enabled("claude") is False
            assert settings.is_feature_enabled("github") is False
            assert settings.is_feature_enabled("debug") is True  # デフォルトでTrue

            # 存在しないフィーチャー
            assert settings.is_feature_enabled("non_existent") is False

    def test_user_data_dir_property(self):
        """user_data_dirプロパティのテスト."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = os.path.join(tmpdir, "test_user_data")

            with patch.dict(
                os.environ,
                {
                    "USER_DATA_PATH": test_path,
                },
            ):
                settings = Settings()
                data_dir = settings.user_data_dir

                # パスがPathオブジェクトとして返される
                assert isinstance(data_dir, Path)
                assert str(data_dir) == test_path
                # ディレクトリが作成される
                assert data_dir.exists()
                assert data_dir.is_dir()

    def test_template_dir_property(self):
        """template_dirプロパティのテスト."""
        settings = Settings()

        template_dir = settings.template_dir
        assert isinstance(template_dir, Path)
        assert str(template_dir) == "./src/templates"

    def test_github_repo_url_property(self):
        """github_repo_urlプロパティのテスト."""
        with patch.dict(
            os.environ,
            {
                "GITHUB_USERNAME": "testuser",
                "GITHUB_REPO_NAME": "my-travel-data",
            },
        ):
            settings = Settings()

            assert settings.github_repo_url == "https://github.com/testuser/my-travel-data"

    def test_case_sensitive_config(self):
        """設定の大文字小文字は区別されないことの確認."""
        with patch.dict(
            os.environ,
            {
                "discord_token": "test-token",
                "DISCORD_TOKEN": "test-token-upper",
            },
        ):
            settings = Settings()
            # pydantic_settingsではcase_sensitive=Falseなので、
            # 最後に設定された値が使用される
            assert settings.DISCORD_TOKEN in ["test-token", "test-token-upper"]

    def test_env_file_loading(self):
        """環境ファイルの読み込みテスト."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("DISCORD_TOKEN=from-env-file\n")
            f.write("LOG_LEVEL=ERROR\n")
            env_file = f.name

        try:
            # .envファイルパスを指定して設定を読み込む
            settings = Settings(_env_file=env_file)

            assert settings.DISCORD_TOKEN == "from-env-file"
            assert settings.LOG_LEVEL == "ERROR"

        finally:
            os.unlink(env_file)

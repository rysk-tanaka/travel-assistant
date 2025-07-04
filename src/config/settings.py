"""
Application settings and configuration.

環境変数から設定を読み込み、アプリケーション全体で使用する設定を管理します。
"""

from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Discord設定
    DISCORD_TOKEN: str = Field(default="", description="Discord Bot Token")
    DEV_GUILD_ID: str | None = Field(default=None, description="開発用サーバーID")

    # GitHub設定
    GITHUB_TOKEN: str = Field(default="", description="GitHub Personal Access Token")
    GITHUB_REPO_NAME: str = Field(
        default="travel-assistant-data", description="データ保存用リポジトリ名"
    )
    GITHUB_USERNAME: str = Field(default="", description="GitHubユーザー名")
    GITHUB_BRANCH: str = Field(default="main", description="使用するブランチ")

    # API設定
    WEATHER_API_KEY: str | None = Field(default=None, description="OpenWeatherMap API Key")
    CLAUDE_API_KEY: str | None = Field(default=None, description="Claude API Key")

    # アプリケーション設定
    DEBUG: bool = Field(default=False, description="デバッグモード")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="ログレベル"
    )

    # データ保存設定
    USER_DATA_PATH: str = Field(default="./data/user_data", description="ユーザーデータ保存パス")
    TEMPLATE_PATH: str = Field(default="./src/templates", description="テンプレート保存パス")

    # 機能フラグ
    ENABLE_WEATHER_API: bool = Field(default=False, description="天気API機能の有効化")
    ENABLE_CLAUDE_API: bool = Field(default=False, description="Claude API機能の有効化")
    ENABLE_GITHUB_SYNC: bool = Field(default=False, description="GitHub同期機能の有効化")
    ENABLE_DEBUG_COMMANDS: bool = Field(default=True, description="デバッグコマンドの有効化")

    @field_validator(
        "ENABLE_WEATHER_API",
        "ENABLE_CLAUDE_API",
        "ENABLE_GITHUB_SYNC",
        "ENABLE_DEBUG_COMMANDS",
        "DEBUG",
        mode="before",
    )
    @classmethod
    def parse_bool(cls, v: Any) -> bool:
        """ブール値のパースをカスタマイズ."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            if v.lower() in ("", "0", "false", "f", "no", "n", "off"):
                return False
            if v.lower() in ("1", "true", "t", "yes", "y", "on"):
                return True
        return bool(v)

    @property
    def user_data_dir(self) -> Path:
        """ユーザーデータディレクトリのPathオブジェクト."""
        path = Path(self.USER_DATA_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def template_dir(self) -> Path:
        """テンプレートディレクトリのPathオブジェクト."""
        return Path(self.TEMPLATE_PATH)

    @property
    def github_repo_url(self) -> str:
        """GitHubリポジトリのURL."""
        return f"https://github.com/{self.GITHUB_USERNAME}/{self.GITHUB_REPO_NAME}"

    def is_feature_enabled(self, feature: str) -> bool:
        """機能フラグの確認."""
        feature_flags = {
            "weather": self.ENABLE_WEATHER_API,
            "claude": self.ENABLE_CLAUDE_API,
            "github": self.ENABLE_GITHUB_SYNC,
            "debug": self.ENABLE_DEBUG_COMMANDS,
        }
        return feature_flags.get(feature, False)


# シングルトンインスタンス
settings = Settings()

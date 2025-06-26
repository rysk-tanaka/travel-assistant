"""
Logging configuration for TravelAssistant.

structlogを使用した構造化ログの設定を提供します。
"""

import logging
import sys
from pathlib import Path

import structlog


def setup_logging(
    *,
    log_level: str = "INFO",
    log_file: Path | None = None,
    json_format: bool = False,
) -> None:
    """
    アプリケーション全体のログ設定を行います。

    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: ログファイルのパス（Noneの場合は標準出力のみ）
        json_format: JSON形式でログを出力するか
    """
    # ログレベルの設定
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 標準ライブラリのログ設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )
    
    # structlogの設定
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                pad_event=30,
            )
        )
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # ファイル出力の設定
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        
        # ファイル用のフォーマッター
        if json_format:
            # JSONの場合はstructlogの出力をそのまま使用
            file_handler.setFormatter(logging.Formatter("%(message)s"))
        else:
            # テキスト形式の場合
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
        
        # ルートロガーにハンドラーを追加
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    構造化ロガーを取得します。

    Args:
        name: ロガー名（通常は__name__を使用）

    Returns:
        構造化ロガーインスタンス
    """
    return structlog.stdlib.get_logger(name)
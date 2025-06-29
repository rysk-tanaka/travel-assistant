# Claude Code Development Guidelines for TravelAssistant

このドキュメントは、Claude Codeが本プロジェクトで作業する際の指針を提供します。

## プロジェクト概要

TravelAssistantは、AI支援による旅行準備システムです。Discord Botを通じて、個人最適化されたチェックリストを自動生成します。

## 開発原則

### 1. 型ヒントの徹底

- すべての関数・メソッドに型ヒントを付ける
- Python 3.12+の新しい型構文（`type`文）を積極的に使用
- `models.py`に型定義とデータモデルを集約

```python
# 型エイリアス定義
ChecklistId = str
UserId = str
GitHubUrl = str

# Pydanticモデルでのバリデーション
class TripChecklist(BaseModel):
    id: ChecklistId
    user_id: UserId
    items: list[ChecklistItem]
```

### 2. エラーハンドリング

- 予期される例外は明示的にcatch
- エラーメッセージは日本語で分かりやすく
- ロガーを使用してエラーの詳細を記録

### 3. ログ実装

- すべての重要な処理にログを実装
- DEBUGレベル: 詳細な処理内容
- INFOレベル: 主要な処理の開始・完了
- WARNINGレベル: 予期しない状態だが処理は継続
- ERRORレベル: 処理が失敗

### 4. テスト戦略

- 単体テスト: 個々の関数・メソッドの動作確認
- プロパティベーステスト: 入力値の境界値や異常系
- 統合テスト: Discord Bot全体の動作確認

#### テスト対象

##### ✅ 単体テスト対象モジュール

ビジネスロジックに焦点を当てたテストを実施：

1. **`src/models.py`** - データモデル（カバレッジ: 100%）
   - データ構造の検証
   - バリデーションロジック
   - 計算プロパティ

2. **`src/core/smart_engine.py`** - スマートテンプレートエンジン（カバレッジ: 99%）
   - テンプレート選択ロジック
   - 条件別調整機能
   - チェックリスト生成

3. **`src/core/github_sync.py`** - GitHub連携（カバレッジ: 94%）
   - チェックリスト保存・読み込み
   - メタデータ管理
   - ファイル操作

4. **`src/utils/markdown_utils.py`** - Markdownユーティリティ（カバレッジ: 99%）
   - テンプレート処理
   - Markdown変換
   - チェックリスト操作

5. **`src/config/settings.py`** - 設定管理（カバレッジ: 98%）
   - 環境変数処理
   - 設定検証

##### ❌ 単体テスト対象外モジュール

Discord連携部分は外部サービス依存のため統合テストで検証：

- `src/bot/commands.py` - Discord Botコマンド
- `src/bot/checklist_check.py` - インタラクティブUI
- `src/bot/checklist_detail.py` - 詳細表示UI
- `src/bot/__init__.py` - Bot初期化

## ディレクトリ構造

```
travel-assistant/
├── src/
│   ├── bot/              # Discord Bot実装
│   ├── core/             # コアビジネスロジック
│   │   ├── smart_engine.py  # スマートテンプレートエンジン
│   │   └── github_sync.py   # GitHub連携
│   ├── templates/        # チェックリストテンプレート
│   ├── config/           # 設定管理
│   ├── utils/            # ユーティリティ
│   └── models.py         # データモデル・型定義
├── tests/
│   ├── unit/            # 単体テスト
│   ├── property/        # プロパティベーステスト
│   ├── integration/     # 統合テスト
│   └── conftest.py      # pytest設定
└── docs/                # ドキュメント
```

## 実装ルール

### 命名規則

- クラス: PascalCase (例: `TripCommands`)
- 関数/変数: snake_case (例: `generate_checklist`)
- 定数: UPPER_SNAKE_CASE (例: `MAX_ITEMS`)
- プライベート: 先頭に `_` (例: `_internal_method`)

### インポート順序

1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール

```python
# 標準ライブラリ
import os
from datetime import datetime

# サードパーティ
import discord
from pydantic import BaseModel

# ローカル
from src.core.smart_engine import SmartTemplateEngine
from src.types import ChecklistId
```

## コマンドリファレンス

### 開発時に使用するコマンド

```bash
# コードフォーマット
make format

# リント実行
make lint

# 型チェック
make typecheck

# テスト実行
make test

# すべてのチェック
make check

# pre-commitフック実行
make check-all
```

## 頻出エラーと対処法

### Discord.py関連

- `Intents`の設定忘れ → `intents.message_content = True`を確認
- スラッシュコマンドの同期忘れ → `bot.tree.sync()`を実行

### GitHub API関連

- レート制限 → キャッシュの実装、適切な待機時間
- 認証エラー → トークンの権限を確認（repo権限が必要）
- ファイル操作エラー → try-except でGithubExceptionをキャッチ
- 型エラー → `get_contents()`の戻り値は`ContentFile | list[ContentFile]`

## 参考実装

新しい機能を実装する際は、以下のファイルを参考にしてください：

- Discord Bot実装: `src/bot/commands.py`
- データモデル・型定義: `src/models.py`
- GitHub連携: `src/core/github_sync.py`
- テスト実装: `tests/unit/test_smart_engine.py`

## 更新履歴

- 2025-06-27: 初版作成
- 2025-06-30: GitHub連携機能の実装に伴う更新

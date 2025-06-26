# TravelAssistant

旅行・出張の準備を効率化するDiscord Bot

## 概要

目的地・期間・条件を入力するだけで、個人最適化されたチェックリストを自動生成し、Discord経由で管理できます。

### 主な機能

- 🤖 **スマートテンプレート**: 条件に応じた自動チェックリスト生成
- 📱 **Discord連携**: ボタン形式の直感的なチェックリスト管理
- 📝 **Markdown記録**: GitHub連携による旅行記録の自動保存

## セットアップ

### 必要環境

- Python 3.12+
- uv (パッケージマネージャー)
- Discord Bot Token
- GitHub Personal Access Token

### インストール

```bash
# リポジトリクローン
git clone https://github.com/yourusername/travel-assistant
cd travel-assistant

# 開発環境セットアップ
make setup

# 環境変数の設定
cp .env.example .env
# .envファイルに各種TOKENを設定

# 実行
uv run python main.py
```

## 使用方法

### Discord コマンド

```text
/trip smart 札幌 2025-06-28 2025-06-30 business
→ 札幌2泊出張用のスマートチェックリスト生成

/trip check
→ 現在のチェックリスト進捗確認
```

## 開発

### 開発コマンド

```bash
make help        # 利用可能なコマンド一覧
make check       # コード品質チェック (format + lint + typecheck + test)
make test        # テスト実行
```

### プロジェクト構成

```text
travel-assistant/
├── src/
│   ├── bot/              # Discord Bot実装
│   ├── core/             # コアビジネスロジック
│   ├── templates/        # チェックリストテンプレート
│   └── utils/            # ユーティリティ関数
├── docs/                 # 設計書・仕様書
├── tests/                # テストコード
└── pyproject.toml        # プロジェクト設定・依存関係
```

## ロードマップ

### v1.0 (基本機能)

- [ ] 基本テンプレート作成
- [ ] Discord Bot基本コマンド
- [ ] GitHub連携
- [ ] 基本チェックリスト管理

### v2.0 (スマート機能)

- [ ] 天気予報連携
- [ ] 地域特性調整
- [ ] 交通手段別調整

### v3.0 (AI機能)

- [ ] 学習型個人最適化
- [ ] Claude連携予測
- [ ] プロアクティブ提案

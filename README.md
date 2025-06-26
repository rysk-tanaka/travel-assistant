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

# 依存関係のインストール
uv sync

# 環境変数の設定
cp .env.example .env
# .envファイルに以下の値を設定:
# - DISCORD_TOKEN (Discord Developer Portalから取得)
# - GITHUB_TOKEN (GitHubのPersonal Access Token)
# - GITHUB_USERNAME (あなたのGitHubユーザー名)

# 実行
python main.py
```

### Discord Bot セットアップ

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. 新しいアプリケーションを作成
3. Bot セクションで Bot を作成し、Token をコピー
4. OAuth2 → URL Generator で以下の権限を選択：
   - Bot権限: Send Messages, Use Slash Commands, Embed Links
   - 生成されたURLでBotをサーバーに招待

## 使用方法

### Discord コマンド

```text
/trip_smart 札幌 2025-06-28 2025-06-30 出張・ビジネス 飛行機
→ 札幌2泊出張用のスマートチェックリスト生成

/trip_smart 沖縄 2025-07-15 2025-07-18 レジャー・観光
→ 沖縄3泊レジャー用のチェックリスト生成

/trip
→ ヘルプメッセージ表示
```

### 実装済みの機能

- ✅ **基本チェックリスト生成**: テンプレートベースの項目管理
- ✅ **地域別調整**: 北海道（防寒対策）、沖縄（日焼け・虫除け対策）
- ✅ **期間別調整**: 長期滞在時の洗濯用品追加
- ✅ **交通手段別調整**: 飛行機（液体制限）、車（ETC・充電器）
- ✅ **Discord Embed表示**: 進捗率・カテゴリ別表示

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

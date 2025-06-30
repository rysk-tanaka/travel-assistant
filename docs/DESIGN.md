# TravelAssistant システム設計書

## システム概要

**目的**: AI支援による旅行準備の自動化・最適化システム
**ユーザー**: 個人（出張・旅行する本人）
**スコープ**: 国内出張メイン、段階的にAI化レベルを向上
**技術基盤**: Python + Discord.py + GitHub API

### AI支援の基本フロー

```text
学習データ蓄積 → パターン認識 → 予測・提案 → 個人最適化
       ↓              ↓           ↓          ↓
   過去の記録     → AI分析    → 自動生成  → 継続改善
```

### 段階的AI化戦略

- **Phase 1**: AI補助型（テンプレート + 改善提案）
- **Phase 2**: AI協調型（AI生成 + 人間承認）
- **Phase 3**: AI主導型（完全自動化 + 例外処理のみ)

## アーキテクチャ

### システム構成

```text
Discord (UI)
    ↕ discord.py
Python Backend (Core Logic)
    ↕ REST API
GitHub (Storage)
    ↕ GitHub Actions
自動化処理
```

### データフロー

1. **計画段階**: GitHub テンプレート → 個人カスタマイズ → 新規ファイル作成
2. **実行段階**: Discord チェックリスト → Python Bot → GitHub 更新
3. **記録段階**: 実績入力 → Markdown 自動生成 → リポジトリ保存

## 技術選択

### Discord Bot: Python + discord.py

**理由**:

- 開発者のPython経験活用
- リッチUI対応（ボタン・フォーム・埋め込み）
- GitHub APIとの連携が容易
- 型ヒント・デバッグ環境の充実

### ストレージ: GitHub Repository

**理由**:

- Markdownネイティブ対応
- バージョン管理自動
- GitHub Actions で自動化可能
- 無料範囲内で十分

### データ形式: Markdown + YAML Front Matter

**理由**:

- 人間が読みやすい
- Git管理に最適
- Pythonの豊富な処理ライブラリ

## データ構造

### リポジトリ構成

```bash
travel-assistant/
├── src/
│   ├── templates/           # 再利用可能テンプレート
│   │   ├── domestic_business.md     # 国内出張用
│   │   └── sapporo_business.md # 札幌出張専用
│   ├── bot/              # Discord Bot実装
│   ├── core/             # コアロジック
│   └── utils/            # ユーティリティ
├── data/
│   └── user_data/        # 個人データ（.gitignore）
├── docs/                 # このドキュメント等
└── tests/                # テストコード
```

### Markdownファイル構造

```yaml
---
type: "business_trip"
destination: "札幌"
dates:
  start: "2025-06-28"
  end: "2025-06-30"
status: "planning" # planning/ongoing/completed
checklist_progress: 0.75
---

# 出張計画：札幌
[Markdown本文]
```

## 実装フェーズ

### Phase 1: 基本機能（MVP）

**目標**: 手動でも使える基本システム

- [ ] GitHubリポジトリ・テンプレート作成
- [ ] 基本的なDiscord Bot（チェックリスト表示・更新）
- [ ] 手動でのMarkdownファイル管理

### Phase 2: 自動化

**目標**: Discord ↔ GitHub 連携

- [ ] Bot からの新規旅行計画作成
- [ ] チェックリスト進捗の自動GitHub更新
- [ ] GitHub Actions での通知

### Phase 3: 高度化

**目標**: 学習・改善機能

- [ ] 過去データ分析
- [ ] 個人最適化されたチェックリスト
- [ ] 外部API連携（天気・交通）

## Python Discord Bot機能仕様

### 基本コマンド

```python
@bot.slash_command()
async def trip_smart(ctx, destination, start_date, end_date, purpose):
    """スマートチェックリスト生成"""
    pass

@bot.slash_command()
async def trip_check(ctx):
    """進捗確認"""
    pass

@bot.slash_command()
async def trip_sync(ctx):
    """GitHub同期"""
    pass

@bot.slash_command()
async def trip_complete(ctx):
    """完了処理"""
    pass
```

### インタラクティブ要素

- ボタン形式チェックリスト
- 選択式フォーム（目的地、期間等）
- 進捗バープログレス表示

## 運用考慮事項

### セキュリティ

- Discord Bot Token の安全な管理
- GitHub Personal Access Token の最小権限
- プライベート情報の分離

### パフォーマンス

- GitHub API Rate Limit 考慮
- 非同期処理によるレスポンス最適化
- 大量データ時のページネーション

### 保守性

- 設定の外部化（環境変数）
- 構造化ログとエラーハンドリング
- テンプレートの柔軟性
- 型ヒントによる保守性向上

## 技術的制約・前提

### 制約

- GitHub API: 5000req/hour/user
- Discord Bot: メッセージ長制限 2000文字
- Python非同期処理: asyncio制限考慮
- Markdown: 複雑な構造は避ける

### 前提

- 個人利用（1ユーザー）
- 月間旅行回数: 〜10回程度
- データ保存期間: 無制限
- Python 3.12+ 使用

## 設計判断記録（ADR）

### ADR-001: Python + discord.py 選択理由

**決定**: バックエンドにPython + discord.py を採用
**理由**: 開発者のPython経験活用、型ヒント充実、デバッグ容易性
**代案**: Node.js + discord.js、Go + discordgo
**影響**: 開発効率向上、データ分析ライブラリ活用可能

### ADR-002: Markdown + GitHub選択理由

**決定**: データ保存にMarkdown + GitHub
**理由**: 可視性、移植性、バージョン管理、Python処理ライブラリ充実
**代案**: JSON + DB、Google Sheets
**影響**: クエリ性能制約、GitHub依存

### ADR-003: uv パッケージマネージャー採用

**決定**: パッケージ管理にuvを採用
**理由**: 高速インストール、現代的な依存関係管理、型チェック統合
**代案**: pip + virtualenv、Poetry
**影響**: 開発効率向上、厳格な依存関係管理

---

## メンテナンス指針

### 月次レビュー項目

- [ ] 実際の使用パターン vs 設計の乖離確認
- [ ] 新しい要求事項の整理
- [ ] パフォーマンス問題の確認

### アップデート優先順位

1. **High**: セキュリティ、データ損失リスク
2. **Medium**: 使用頻度の高い機能改善
3. **Low**: 新機能、最適化

### 技術負債管理

- 四半期ごとにコード品質レビュー
- 外部ライブラリの定期アップデート
- 非推奨APIの移行計画

---
*作成: 2025-06-27*
*次回更新予定: Phase 1完了時*

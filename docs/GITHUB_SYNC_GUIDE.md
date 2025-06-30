# GitHub連携機能実装ガイド

## 概要

TravelAssistantにGitHub連携機能を実装しました。この機能により、生成したチェックリストをGitHubリポジトリに自動保存し、過去の旅行履歴を管理できます。

## 実装内容

### 1. GitHubSync クラス (`src/core/github_sync.py`)

GitHub APIとの連携を管理するメインクラスです。

**主な機能:**

- チェックリストのGitHub保存
- メタデータの管理
- 過去の旅行履歴取得
- チェックリストの削除

**ファイル構造:**

```bash
travel-assistant-data/
├── trips/
│   └── 2025/
│       └── 06/
│           ├── 20250628-札幌-business.md          # チェックリスト本体
│           └── 20250628-札幌-business_metadata.json  # メタデータ
```

### 2. Discord Bot コマンドの更新 (`src/bot/commands.py`)

**新機能:**

- 💾 保存ボタン: チェックリストをGitHubに保存
- `/trip_history` コマンド: 過去の旅行履歴を表示

### 3. 設定項目 (`src/config/settings.py`)

**必要な環境変数:**

```bash
# .env ファイル
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_USERNAME=your_github_username
GITHUB_REPO_NAME=travel-assistant-data
GITHUB_BRANCH=main
ENABLE_GITHUB_SYNC=true
```

## セットアップ手順

### 1. GitHub Personal Access Token の取得

1. GitHubの Settings > Developer settings > Personal access tokens へアクセス
2. "Generate new token" をクリック
3. 必要な権限を選択:
   - `repo` (Full control of private repositories)
   - `read:user` (Read all user profile data)
4. トークンを生成して保存

### 2. データ保存用リポジトリの作成

```bash
# プライベートリポジトリを作成
gh repo create travel-assistant-data --private
```

### 3. 環境変数の設定

`.env` ファイルに以下を追加:

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=your-username
GITHUB_REPO_NAME=travel-assistant-data
ENABLE_GITHUB_SYNC=true
```

## 使い方

### チェックリストの保存

1. `/trip_smart` コマンドでチェックリストを生成
2. 「💾 保存」ボタンをクリック
3. GitHubリポジトリへの保存が完了

### 過去の履歴確認

```bash
/trip_history
```

- 最新10件の旅行履歴を表示
- 各旅行の進捗状況を確認
- GitHubリンクから詳細を閲覧可能

## データフォーマット

### Markdownファイル

```markdown
---
type: "business_trip"
destination: "札幌"
dates:
  start: "2025-06-28"
  end: "2025-06-30"
status: "planning"
checklist_progress: 33.33
template_used: "sapporo_business"
---

# 札幌旅行チェックリスト
**期間**: 2025-06-28 ～ 2025-06-30
**目的**: business
**進捗**: 33.3% (1/3)

## 移動関連
- [x] 航空券
- [ ] 身分証明書

## 天気対応
- [ ] 折り畳み傘
  - ⭐ 降水確率60%
```

### メタデータファイル

```json
{
  "checklist_id": "abc123",
  "user_id": "user456",
  "status": "planning",
  "created_at": "2025-06-27T10:00:00",
  "updated_at": "2025-06-27T11:00:00",
  "completion_percentage": 33.33,
  "template_used": "sapporo_business",
  "item_stats": {
    "total": 45,
    "completed": 15,
    "auto_added": 5
  }
}
```

## テスト

```bash
# 単体テストの実行
pytest tests/unit/test_github_sync.py

# カバレッジレポート付き
pytest tests/unit/test_github_sync.py --cov=src.core.github_sync
```

## トラブルシューティング

### よくあるエラー

1. **"GitHub Token is not configured"**
   - `.env` ファイルに `GITHUB_TOKEN` が設定されているか確認
   - トークンが有効期限切れでないか確認

2. **"Failed to access repository"**
   - リポジトリ名とユーザー名が正しいか確認
   - トークンに `repo` 権限があるか確認

3. **"GitHub sync is disabled"**
   - `ENABLE_GITHUB_SYNC=true` が設定されているか確認

## 今後の拡張

- [ ] チェックリストのインポート機能
- [ ] 複数ユーザー対応（共有リポジトリ）
- [ ] 旅行レポートの自動生成
- [ ] 統計情報の可視化

## 注意事項

- GitHub API のレート制限: 5000 requests/hour
- プライベートリポジトリの使用を推奨
- 定期的なバックアップを推奨

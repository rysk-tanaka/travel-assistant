# TravelAssistant 実装計画書

## プロジェクト概要
**期間**: 2025年6月〜8月（約2ヶ月）  
**目標**: AI支援による旅行準備システムの構築・運用開始  
**成功指標**: 実際の札幌出張で効果的に使用できる  

## フェーズ別実装計画

### Phase 1: MVP構築（Week 1-3）
**目標**: 手動でも使える基本システム

#### Week 1: 基盤構築
- [ ] GitHubリポジトリセットアップ
- [ ] ディレクトリ構成作成
- [ ] 基本テンプレート作成（国内出張・旅行）
- [ ] Discord Bot基本セットアップ

#### Week 2: 基本機能実装
- [ ] Discord Bot基本コマンド実装
  - `/trip smart` - スマートチェックリスト生成
  - `/trip check` - チェックリスト表示
  - `/trip update` - チェック状態更新
- [ ] Markdownファイル生成機能
- [ ] GitHub API連携基礎

#### Week 3: 統合・テスト
- [ ] Discord ↔ GitHub 連携テスト
- [ ] 基本チェックリスト管理機能完成
- [ ] ドキュメント整備
- [ ] **マイルストーン**: 手動テンプレートで旅行準備ができる

### Phase 2: スマート機能（Week 4-6）
**目標**: 条件に応じた自動調整機能

#### Week 4: 天気予報連携
- [ ] OpenWeatherMap API統合
- [ ] 天気条件によるアイテム自動追加
  - 雨予報 → 傘・レインコート
  - 寒い → 防寒着・ホッカイロ
  - 暑い → 日焼け止め・水分補給
- [ ] テスト・デバッグ

#### Week 5: 地域・期間調整
- [ ] 地域特性データベース作成
- [ ] 地域別アイテム自動調整
  - 北海道 → 防寒対策
  - 沖縄 → 暑さ対策
  - 関西 → 歩きやすい靴
- [ ] 期間による持ち物調整ロジック
- [ ] 交通手段別調整（飛行機・新幹線・車）

#### Week 6: スマートテンプレート完成
- [ ] 統合テスト・調整
- [ ] スマートテンプレート機能の完成
- [ ] **マイルストーン**: 条件入力で最適化されたチェックリスト生成

### Phase 3: AI学習機能（Week 7-8）
**目標**: 個人最適化・予測機能

#### Week 7: 学習データ蓄積
- [ ] 旅行履歴データ構造設計
- [ ] 忘れ物・追加アイテム記録機能
- [ ] 個人パターン分析基礎ロジック

#### Week 8: AI連携
- [ ] Claude API連携実装
- [ ] 学習データに基づく予測・提案
- [ ] プロアクティブ機能（天気変化等の通知）
- [ ] **最終マイルストーン**: AI支援による個人最適化

## 技術実装詳細

### 必要な技術要素
#### Phase 1
```python
# Discord Bot基本実装
import discord
from discord.ext import commands

# GitHub連携
from github import Github

# 基本コマンド処理
@bot.slash_command()
async def trip_smart(ctx, destination, start_date, end_date, purpose):
    # テンプレート処理
    pass
```

#### Phase 2
```python
# 天気API連携
import aiohttp

async def get_weather(city):
    async with aiohttp.ClientSession() as session:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}"
        # API処理

# スマート調整ロジック
def adjust_template(base_template, conditions):
    # 地域・天気・期間による調整
    pass
```

#### Phase 3
```python
# Claude API連携
import anthropic

claude = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
response = await claude.messages.create(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": f"過去データ: {history}"}]
)
```

## リスク管理

### 技術的リスク
| リスク | 影響度 | 対策 |
|--------|--------|------|
| API制限 | 中 | レート制限考慮・キャッシュ実装 |
| Discord Bot障害 | 高 | エラーハンドリング・ログ記録 |
| GitHub API障害 | 中 | ローカルバックアップ機能 |

### スケジュールリスク
| リスク | 影響度 | 対策 |
|--------|--------|------|
| 実装遅延 | 中 | 機能優先順位の調整 |
| テスト不足 | 高 | 各フェーズでの検証強化 |

## 品質管理

### テスト計画
- **Unit Test**: 各機能の単体テスト
- **Integration Test**: Discord-GitHub連携テスト
- **User Test**: 実際の旅行準備での使用テスト

### 継続的改善
- 週次で進捗レビュー
- 実使用フィードバックの収集
- ドキュメント・コードの定期更新

## 成果物

### 各フェーズの成果物
**Phase 1**:
- 動作するDiscord Bot
- 基本テンプレート集
- GitHub連携機能

**Phase 2**:
- スマートテンプレート機能
- 天気・地域連携
- 使用マニュアル

**Phase 3**:
- AI学習機能
- 個人最適化システム
- 運用ガイド

### 最終成果物
- **フル機能システム**: 実用可能なTravelAssistant
- **ポートフォリオ**: 公開可能なプロジェクト
- **ドキュメント**: 設計書・使用方法・技術解説

## 次のアクション

### 今週実装すべきタスク（優先度順）
1. **Discord Bot基本実装** - アプリケーション作成・Token取得
2. **基本的なコマンド実装** - `/trip smart`コマンド
3. **テンプレート作成** - 札幌出張用テンプレート
4. **GitHub連携基礎** - リポジトリ作成・API接続

### 開発環境セットアップ
```bash
# 1. リポジトリクローン
git clone https://github.com/yourusername/travel-assistant
cd travel-assistant

# 2. uvのインストール（初回のみ）
curl -LsSf https://astral.sh/uv/install.sh | sh
# または: brew install uv

# 3. 依存関係インストール
uv sync          # 本番環境
uv sync --dev    # 開発環境（テストツール含む）

# 4. 環境変数設定
cp .env.example .env
# .envファイルを編集して各種トークンを設定

# 5. 実行
uv run python main.py

# 開発時のコマンド例
uv run pytest           # テスト実行
uv run black .          # コードフォーマット
uv run ruff check .     # リンター実行
```

### 来週の目標
- Discord Botで基本的なチェックリスト管理ができる状態
- GitHubにチェックリストが保存される機能
- 基本的なテンプレートからの生成が可能
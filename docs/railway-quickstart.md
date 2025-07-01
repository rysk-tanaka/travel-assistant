# Railway クイックスタートガイド

> 5分でTravelAssistant BotをRailwayにデプロイする最速手順

## 🚀 前提条件

- GitHubアカウント
- Discordアカウント
- クレジットカード（Hobby Plan用）

## 📝 手順

### 1. Discord Bot作成（1分）

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. "New Application" → アプリ名入力
3. 左メニュー "Bot" → "Add Bot"
4. "Reset Token" → トークンをコピー（後で使用）

### 2. GitHub準備（2分）

```bash
# プロジェクトディレクトリで実行
cd /Users/rysk/Repositories/rysk/travel-assistant

# 最小構成ファイル作成
echo "discord.py==2.3.2" > requirements.txt
echo "python-3.11.x" > runtime.txt

# Gitリポジトリ初期化
git init
git add .
git commit -m "Initial commit"

# GitHubで新規リポジトリ作成後
git remote add origin https://github.com/YOUR_USERNAME/travel-assistant.git
git push -u origin main
```

### 3. Railway デプロイ（2分）

1. [Railway.app](https://railway.app)にアクセス
2. "Start a New Project" をクリック
3. "Deploy from GitHub repo" を選択
4. GitHubアカウント連携 → `travel-assistant` リポジトリ選択
5. 環境変数設定:

   ```env
   DISCORD_TOKEN = [手順1でコピーしたトークン]
   ```

6. "Deploy" をクリック

## ✅ 動作確認

### Bot招待リンク生成

1. Discord Developer Portal → あなたのアプリ選択
2. "OAuth2" → "URL Generator"
3. Scopes: `bot` と `applications.commands` にチェック
4. Bot Permissions: 必要な権限を選択
5. 生成されたURLでBotをサーバーに招待

### 最小限のBotコード

```python
# src/bot.py
import os
import discord
from discord.ext import commands

# Bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました！')

@bot.command()
async def ping(ctx):
    """動作確認用コマンド"""
    await ctx.send(f'Pong! レイテンシ: {round(bot.latency * 1000)}ms')

@bot.command()
async def trip(ctx):
    """旅行準備コマンド（仮）"""
    await ctx.send('🧳 TravelAssistant Bot 開発中...')

# Bot起動
if __name__ == '__main__':
    bot.run(os.environ['DISCORD_TOKEN'])
```

## 🎯 次のステップ

### 機能追加の優先順位

1. **基本コマンド実装**

   ```python
   @bot.slash_command(description="新しい旅行を作成")
   async def trip_new(ctx, destination: str, start_date: str, end_date: str):
       # 実装
   ```

2. **GitHub連携**

   ```python
   # requirements.txt に追加
   PyGithub==2.1.1
   ```

3. **天気API連携**

   ```python
   # 環境変数追加
   WEATHER_API_KEY = your_openweathermap_key
   ```

## 💰 コスト管理

### 使用量モニタリング

Railway ダッシュボード → プロジェクト → "Usage" タブで確認

### 予想コスト（Bot 1台）

- CPU: ~$0.20/月
- メモリ: ~$0.30/月
- **合計: ~$0.50/月**（無料枠$5内）

## 🔧 トラブルシューティング

### Bot がオフラインの場合

1. Railway ダッシュボード → "Deployments" でエラー確認
2. "View Logs" でエラーメッセージ確認
3. 環境変数が正しく設定されているか確認

### よくあるエラー

```python
# エラー: discord.errors.LoginFailure
# 解決: DISCORD_TOKEN が正しいか確認

# エラー: ModuleNotFoundError
# 解決: requirements.txt にモジュール追加して再デプロイ

# エラー: Command raised an exception
# 解決: ログで詳細確認、権限設定を確認
```

## 📚 参考リソース

- [Railway Discord Botテンプレート](https://railway.app/new/template/PxM3nl)
- [discord.py ドキュメント](https://discordpy.readthedocs.io/)
- [Railway CLI ツール](https://docs.railway.app/cli/quick-start)

---

これで基本的なDiscord BotがRailwayで動作します！
次は[完全版ガイド](./railway-deployment-guide.md)で本格的な実装を始めましょう。

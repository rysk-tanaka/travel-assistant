# TravelAssistant Python版 技術スタック

## 🐍 Core Technology Stack

### **Backend Framework**
```python
# メインフレームワーク
discord.py              # Discord Bot開発
asyncio                 # 非同期処理
aiohttp                 # 非同期HTTP通信
aiofiles               # 非同期ファイル操作
```

### **Data Processing**
```python
# データ処理・操作
PyGithub               # GitHub API連携
python-frontmatter     # Markdown + YAML Front Matter
jinja2                 # テンプレートエンジン
pydantic              # データバリデーション
pandas                # データ分析（将来の学習機能用）
```

### **External APIs**
```python
# 外部API連携
anthropic             # Claude API (公式SDK)
requests              # HTTP通信（同期用）
python-dotenv         # 環境変数管理
```

### **Development Tools**
```python
# 開発・テスト
pytest                # テストフレームワーク
black                 # コードフォーマッター
mypy                  # 型チェック
pre-commit           # Git hooks
```

## 📁 プロジェクト構成

```
travel-assistant/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── commands.py        # Discord コマンド定義
│   │   ├── events.py          # イベントハンドラー
│   │   └── embeds.py          # Discord Embed作成
│   ├── core/
│   │   ├── __init__.py
│   │   ├── smart_engine.py    # スマートテンプレート処理
│   │   ├── github_sync.py     # GitHub連携
│   │   ├── weather.py         # 天気予報取得
│   │   └── learning.py        # 学習機能
│   ├── templates/
│   │   ├── business_trip.md
│   │   ├── sapporo_business.md
│   │   └── leisure_trip.md
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py        # 設定管理
│   │   └── regions.py         # 地域設定
│   └── utils/
│       ├── __init__.py
│       ├── markdown_utils.py  # Markdown操作
│       └── date_utils.py      # 日付処理
├── tests/
│   ├── test_smart_engine.py
│   ├── test_github_sync.py
│   └── test_commands.py
├── data/
│   └── user_data/            # ユーザーデータ（gitignore）
├── pyproject.toml            # プロジェクト設定・依存関係
├── uv.lock                   # ロックファイル（自動生成）
├── .env.example
└── main.py                   # エントリーポイント
```

## 🚀 実装例

### 環境セットアップ（uv使用）
```bash
# uvのインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクト依存関係のインストール
uv sync          # 本番環境
uv sync --dev    # 開発環境

# 実行
uv run python main.py

# その他のコマンド
uv run pytest              # テスト実行
uv run black .             # コードフォーマット
uv run ruff check .        # リンター実行
uv run mypy .              # 型チェック
```

### Discord Bot基本実装
```python
# src/bot/commands.py
import discord
from discord.ext import commands
from src.core.smart_engine import SmartTemplateEngine

class TripCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.smart_engine = SmartTemplateEngine()
    
    @discord.slash_command(
        description="スマートチェックリストを生成します"
    )
    async def trip_smart(
        self,
        ctx: discord.ApplicationContext,
        destination: discord.Option(str, "目的地"),
        start_date: discord.Option(str, "開始日 (YYYY-MM-DD)"),
        end_date: discord.Option(str, "終了日 (YYYY-MM-DD)"),
        purpose: discord.Option(
            str, 
            "目的", 
            choices=["business", "leisure"]
        )
    ):
        await ctx.defer()  # 処理時間確保
        
        try:
            # チェックリスト生成
            checklist = await self.smart_engine.generate_checklist(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                purpose=purpose,
                user_id=str(ctx.user.id)
            )
            
            # Discord Embed作成
            embed = self.create_checklist_embed(checklist)
            view = ChecklistView(checklist.id)
            
            await ctx.followup.send(embed=embed, view=view)
            
        except Exception as e:
            await ctx.followup.send(f"エラーが発生しました: {e}")
    
    def create_checklist_embed(self, checklist):
        embed = discord.Embed(
            title=f"🧳 {checklist.destination} チェックリスト",
            description=f"期間: {checklist.start_date} ～ {checklist.end_date}",
            color=discord.Color.blue()
        )
        
        # カテゴリ別に表示
        for category, items in checklist.items_by_category.items():
            value = "\n".join([
                f"{'☑️' if item.checked else '⬜'} {item.name}"
                for item in items[:5]  # 最初の5項目
            ])
            if len(items) > 5:
                value += f"\n... 他{len(items)-5}項目"
            
            embed.add_field(
                name=f"📋 {category}",
                value=value,
                inline=False
            )
        
        # 進捗情報
        progress = checklist.completion_percentage
        embed.add_field(
            name="📊 進捗",
            value=f"{progress:.1f}% ({checklist.completed_count}/{checklist.total_count})",
            inline=True
        )
        
        return embed

# ボタンインタラクション
class ChecklistView(discord.ui.View):
    def __init__(self, checklist_id: str):
        super().__init__(timeout=300)  # 5分でタイムアウト
        self.checklist_id = checklist_id
    
    @discord.ui.button(
        label="✅ 項目チェック", 
        style=discord.ButtonStyle.green
    )
    async def check_items(
        self, 
        button: discord.ui.Button, 
        interaction: discord.Interaction
    ):
        # モーダルでチェック項目選択
        modal = CheckItemModal(self.checklist_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="📊 進捗確認", 
        style=discord.ButtonStyle.blue
    )
    async def show_progress(
        self, 
        button: discord.ui.Button, 
        interaction: discord.Interaction
    ):
        # 進捗詳細表示
        pass
```

### スマートテンプレートエンジン
```python
# src/core/smart_engine.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date
import asyncio

from src.core.weather import WeatherService
from src.core.github_sync import GitHubSync
from src.utils.markdown_utils import MarkdownProcessor

@dataclass
class ChecklistItem:
    name: str
    category: str
    checked: bool = False
    auto_added: bool = False
    reason: Optional[str] = None

@dataclass 
class TripChecklist:
    id: str
    destination: str
    start_date: date
    end_date: date
    purpose: str
    items: List[ChecklistItem]
    
    @property
    def items_by_category(self) -> Dict[str, List[ChecklistItem]]:
        result = {}
        for item in self.items:
            if item.category not in result:
                result[item.category] = []
            result[item.category].append(item)
        return result
    
    @property
    def completion_percentage(self) -> float:
        if not self.items:
            return 0.0
        return (sum(1 for item in self.items if item.checked) / len(self.items)) * 100
    
    @property
    def completed_count(self) -> int:
        return sum(1 for item in self.items if item.checked)
    
    @property
    def total_count(self) -> int:
        return len(self.items)

class SmartTemplateEngine:
    def __init__(self):
        self.weather_service = WeatherService()
        self.github_sync = GitHubSync()
        self.markdown_processor = MarkdownProcessor()
    
    async def generate_checklist(
        self,
        destination: str,
        start_date: str,
        end_date: str,
        purpose: str,
        user_id: str
    ) -> TripChecklist:
        """スマートチェックリスト生成のメイン処理"""
        
        # 1. 基本テンプレート選択
        base_template = self._select_base_template(destination, purpose)
        
        # 2. 並行してデータ取得
        weather_data, user_history = await asyncio.gather(
            self.weather_service.get_forecast(destination, start_date, end_date),
            self._load_user_history(user_id),
            return_exceptions=True
        )
        
        # 3. 調整適用
        checklist_items = self._apply_adjustments(
            base_template=base_template,
            weather_data=weather_data if not isinstance(weather_data, Exception) else None,
            destination=destination,
            duration=self._calculate_duration(start_date, end_date),
            user_history=user_history if not isinstance(user_history, Exception) else None
        )
        
        # 4. チェックリストオブジェクト作成
        checklist = TripChecklist(
            id=self._generate_checklist_id(destination, start_date),
            destination=destination,
            start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
            end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
            purpose=purpose,
            items=checklist_items
        )
        
        # 5. GitHub保存
        await self.github_sync.save_checklist(checklist)
        
        return checklist
    
    def _select_base_template(self, destination: str, purpose: str) -> Dict:
        """ベーステンプレート選択ロジック"""
        # 札幌出張なら専用テンプレート
        if purpose == "business" and "札幌" in destination:
            return self.markdown_processor.load_template("sapporo_business.md")
        elif purpose == "business":
            return self.markdown_processor.load_template("domestic_business.md")
        else:
            return self.markdown_processor.load_template("leisure_domestic.md")
    
    def _apply_adjustments(
        self,
        base_template: Dict,
        weather_data: Optional[Dict],
        destination: str,
        duration: int,
        user_history: Optional[Dict]
    ) -> List[ChecklistItem]:
        """各種調整を適用してアイテムリスト生成"""
        
        items = []
        
        # ベーステンプレートから基本アイテム
        for category, base_items in base_template["categories"].items():
            for item_name in base_items:
                items.append(ChecklistItem(
                    name=item_name,
                    category=category,
                    auto_added=False
                ))
        
        # 天気調整
        if weather_data:
            weather_items = self._get_weather_adjustments(weather_data)
            items.extend(weather_items)
        
        # 地域調整
        regional_items = self._get_regional_adjustments(destination)
        items.extend(regional_items)
        
        # 期間調整
        duration_items = self._get_duration_adjustments(duration)
        items.extend(duration_items)
        
        # 個人履歴調整
        if user_history:
            personal_items = self._get_personal_adjustments(user_history, destination)
            items.extend(personal_items)
        
        return items
    
    def _get_weather_adjustments(self, weather_data: Dict) -> List[ChecklistItem]:
        """天気予報に基づく調整"""
        items = []
        
        if weather_data.get("rain_probability", 0) > 50:
            items.append(ChecklistItem(
                name="折り畳み傘",
                category="天気対応",
                auto_added=True,
                reason=f"降水確率{weather_data['rain_probability']}%"
            ))
            items.append(ChecklistItem(
                name="レインコート",
                category="天気対応", 
                auto_added=True,
                reason="雨予報のため"
            ))
        
        avg_temp = weather_data.get("average_temperature", 20)
        if avg_temp < 10:
            items.append(ChecklistItem(
                name="防寒着",
                category="服装",
                auto_added=True,
                reason=f"平均気温{avg_temp}℃"
            ))
        elif avg_temp > 30:
            items.append(ChecklistItem(
                name="日焼け止め",
                category="健康管理",
                auto_added=True,
                reason=f"平均気温{avg_temp}℃"
            ))
        
        return items

# メイン実行ファイル
# main.py
import asyncio
import discord
from discord.ext import commands
from src.bot.commands import TripCommands
from src.config.settings import Settings

def main():
    # Bot設定
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(
        command_prefix='!',
        intents=intents,
        description='AI-powered Travel Assistant'
    )
    
    # コマンド登録
    bot.add_cog(TripCommands(bot))
    
    @bot.event
    async def on_ready():
        print(f'{bot.user} としてログインしました！')
        await bot.sync_commands()  # スラッシュコマンド同期
    
    # Bot実行
    bot.run(Settings.DISCORD_TOKEN)

if __name__ == "__main__":
    main()
```

## 依存関係管理

### uvを使用したパッケージ管理
このプロジェクトでは `uv` を使用してPythonパッケージを管理しています。

**uvの利点:**
- ⚡ **高速**: pipよりも10-100倍高速なパッケージインストール
- 🔧 **統合環境**: Python環境とパッケージ管理が統合
- 🔒 **再現性**: ロックファイルによる完全な依存関係管理
- 📦 **互換性**: pyproject.toml標準に準拠

### pyproject.toml による設定管理
```toml
# pyproject.toml
[project]
name = "travel-assistant"
version = "0.1.0"
description = "AI-powered travel preparation assistant"

dependencies = [
    "discord.py>=2.3.2",
    "aiohttp>=3.8.0",
    "PyGithub>=1.59.0",
    "python-frontmatter>=1.0.0",
    "jinja2>=3.1.0",
    "anthropic>=0.3.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "mypy>=1.5.0",
    "pre-commit>=3.4.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## 開発効率の比較

### **Python経験者の場合**
```
開発時間:    Python 100%  vs  Node.js 150-200%
デバッグ:    Python 100%  vs  Node.js 120-150%
保守性:      Python 100%  vs  Node.js 110-130%
学習コスト:  Python 0%    vs  Node.js 20-40%
```

**結論: Python選択で30-50%の開発効率向上が期待できる**
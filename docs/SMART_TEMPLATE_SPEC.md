# スマートテンプレート機能仕様（Python版）

## 機能概要
出張・旅行の条件を入力すると、基本テンプレートを自動でカスタマイズしたチェックリストを生成

## Python実装における設計思想

### データクラス活用
```python
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import date

@dataclass
class TripConditions:
    destination: str
    start_date: date
    end_date: date
    purpose: str  # "business" | "leisure"
    transport_method: Optional[str] = None
    accommodation_type: Optional[str] = None
    special_requirements: List[str] = None

@dataclass
class ChecklistItem:
    name: str
    category: str
    priority: int  # 1-5 (5が最重要)
    auto_added: bool = False
    reason: Optional[str] = None
    checked: bool = False
```

## 入力条件とバリデーション

### Discord Slash Command定義
```python
@bot.slash_command(description="スマートチェックリスト生成")
async def trip_smart(
    ctx: discord.ApplicationContext,
    destination: discord.Option(str, "目的地", max_length=50),
    start_date: discord.Option(str, "開始日 (YYYY-MM-DD)"),
    end_date: discord.Option(str, "終了日 (YYYY-MM-DD)"),
    purpose: discord.Option(str, "目的", choices=["business", "leisure"]),
    transport: discord.Option(
        str, 
        "交通手段", 
        choices=["airplane", "train", "car"], 
        required=False
    ),
    accommodation: discord.Option(
        str,
        "宿泊先タイプ",
        choices=["hotel", "ryokan", "guest_house"],
        required=False
    )
):
```

### Pydanticによる入力バリデーション
```python
from pydantic import BaseModel, validator, Field
from datetime import date, datetime

class TripRequest(BaseModel):
    destination: str = Field(..., min_length=1, max_length=50)
    start_date: date
    end_date: date
    purpose: str = Field(..., regex="^(business|leisure)$")
    transport_method: Optional[str] = Field(None, regex="^(airplane|train|car)$")
    
    @validator('end_date')
    def end_date_must_be_after_start_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('終了日は開始日より後である必要があります')
        return v
    
    @validator('start_date')
    def start_date_must_be_future(cls, v):
        if v < date.today():
            raise ValueError('開始日は今日以降である必要があります')
        return v
    
    @property
    def duration(self) -> int:
        return (self.end_date - self.start_date).days
```

## テンプレート調整エンジン

### 調整ルールの階層構造
```python
from abc import ABC, abstractmethod
from typing import Protocol

class AdjustmentRule(Protocol):
    def apply(self, base_items: List[ChecklistItem], conditions: TripConditions) -> List[ChecklistItem]:
        """調整ルールを適用してアイテムリストを返す"""
        ...

class WeatherAdjustment:
    def __init__(self, weather_service: WeatherService):
        self.weather_service = weather_service
    
    async def apply(self, base_items: List[ChecklistItem], conditions: TripConditions) -> List[ChecklistItem]:
        weather_data = await self.weather_service.get_forecast(
            conditions.destination, 
            conditions.start_date, 
            conditions.end_date
        )
        
        additional_items = []
        
        if weather_data.rain_probability > 0.5:
            additional_items.extend([
                ChecklistItem(
                    name="折り畳み傘",
                    category="天気対応",
                    priority=4,
                    auto_added=True,
                    reason=f"降水確率{weather_data.rain_probability*100:.0f}%"
                ),
                ChecklistItem(
                    name="レインコート",
                    category="天気対応",
                    priority=3,
                    auto_added=True,
                    reason="雨予報のため"
                )
            ])
        
        return base_items + additional_items

class RegionalAdjustment:
    def __init__(self):
        self.regional_rules = {
            "北海道": {
                "months": {
                    (6, 7, 8): ["薄手の長袖", "ライトジャケット"],
                    (12, 1, 2): ["防寒コート", "手袋", "マフラー", "雪対応靴"],
                },
                "always": ["折り畳み傘"]
            },
            "沖縄": {
                "always": ["日焼け止め", "薄着", "虫除けスプレー"]
            }
        }
    
    def apply(self, base_items: List[ChecklistItem], conditions: TripConditions) -> List[ChecklistItem]:
        additional_items = []
        
        # 地域マッチング（部分一致）
        matched_region = None
        for region in self.regional_rules:
            if region in conditions.destination:
                matched_region = region
                break
        
        if not matched_region:
            return base_items
        
        rules = self.regional_rules[matched_region]
        month = conditions.start_date.month
        
        # 月別アイテム追加
        if "months" in rules:
            for month_range, items in rules["months"].items():
                if month in month_range:
                    for item_name in items:
                        additional_items.append(ChecklistItem(
                            name=item_name,
                            category="地域特性",
                            priority=3,
                            auto_added=True,
                            reason=f"{matched_region}の{month}月対応"
                        ))
        
        # 常時アイテム追加
        if "always" in rules:
            for item_name in rules["always"]:
                additional_items.append(ChecklistItem(
                    name=item_name,
                    category="地域特性",
                    priority=2,
                    auto_added=True,
                    reason=f"{matched_region}特有"
                ))
        
        return base_items + additional_items
```

## スマートテンプレートエンジン本体

### メインエンジンクラス
```python
import asyncio
from typing import List
import logging

logger = logging.getLogger(__name__)

class SmartTemplateEngine:
    def __init__(self):
        self.template_loader = MarkdownTemplateLoader()
        self.adjustments = [
            WeatherAdjustment(WeatherService()),
            RegionalAdjustment(),
            DurationAdjustment(),
            TransportAdjustment(),
            PersonalHistoryAdjustment()
        ]
    
    async def generate_checklist(self, request: TripRequest, user_id: str) -> TripChecklist:
        """メイン生成処理"""
        logger.info(f"Generating checklist for {request.destination}, user: {user_id}")
        
        try:
            # 1. ベーステンプレート選択
            base_template = await self._select_base_template(request)
            
            # 2. 基本アイテムリスト作成
            base_items = self._parse_template_items(base_template)
            
            # 3. 調整ルール並列適用
            adjusted_items = await self._apply_adjustments(base_items, request, user_id)
            
            # 4. 重複排除・優先度ソート
            final_items = self._deduplicate_and_sort(adjusted_items)
            
            # 5. チェックリストオブジェクト作成
            checklist = TripChecklist(
                id=self._generate_id(request, user_id),
                conditions=request,
                items=final_items,
                created_at=datetime.now(),
                user_id=user_id
            )
            
            logger.info(f"Generated checklist with {len(final_items)} items")
            return checklist
            
        except Exception as e:
            logger.error(f"Error generating checklist: {e}")
            raise SmartTemplateError(f"チェックリスト生成エラー: {e}")
    
    async def _select_base_template(self, request: TripRequest) -> str:
        """ベーステンプレート選択ロジック"""
        template_map = {
            ("business", "札幌"): "sapporo_business.md",
            ("business", "*"): "domestic_business.md",
            ("leisure", "*"): "leisure_domestic.md"
        }
        
        # 具体的マッチング優先
        for (purpose, location), template_name in template_map.items():
            if purpose == request.purpose:
                if location == "*" or location in request.destination:
                    return await self.template_loader.load(template_name)
        
        # デフォルト
        return await self.template_loader.load("domestic_business.md")
    
    async def _apply_adjustments(
        self, 
        base_items: List[ChecklistItem], 
        request: TripRequest, 
        user_id: str
    ) -> List[ChecklistItem]:
        """調整ルール並列適用"""
        
        conditions = TripConditions(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            purpose=request.purpose,
            transport_method=request.transport_method
        )
        
        # 並列で調整適用
        adjustment_tasks = [
            adjustment.apply(base_items.copy(), conditions)
            for adjustment in self.adjustments
        ]
        
        adjustment_results = await asyncio.gather(*adjustment_tasks, return_exceptions=True)
        
        # 結果統合（例外は無視）
        all_items = base_items.copy()
        for result in adjustment_results:
            if isinstance(result, Exception):
                logger.warning(f"Adjustment failed: {result}")
                continue
            all_items.extend([item for item in result if item not in base_items])
        
        return all_items
    
    def _deduplicate_and_sort(self, items: List[ChecklistItem]) -> List[ChecklistItem]:
        """重複排除と優先度ソート"""
        # 名前による重複排除（後勝ち）
        unique_items = {}
        for item in items:
            unique_items[item.name] = item
        
        # 優先度でソート（高い順）→カテゴリでグループ化
        sorted_items = sorted(
            unique_items.values(),
            key=lambda x: (-x.priority, x.category, x.name)
        )
        
        return sorted_items
```

## Discord UI統合

### 生成結果の表示
```python
class ChecklistView(discord.ui.View):
    def __init__(self, checklist: TripChecklist):
        super().__init__(timeout=300)
        self.checklist = checklist
    
    @discord.ui.button(label="✅ チェック", style=discord.ButtonStyle.green)
    async def toggle_items(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = CheckItemModal(self.checklist)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📊 進捗詳細", style=discord.ButtonStyle.blue)
    async def show_progress(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = self._create_progress_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="💾 GitHub保存", style=discord.ButtonStyle.gray)
    async def save_to_github(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            github_sync = GitHubSync()
            url = await github_sync.save_checklist(self.checklist)
            await interaction.followup.send(f"✅ GitHubに保存しました: {url}")
        except Exception as e:
            await interaction.followup.send(f"❌ 保存エラー: {e}")

def create_checklist_embed(checklist: TripChecklist) -> discord.Embed:
    """チェックリスト用Discord Embed作成"""
    embed = discord.Embed(
        title=f"🧳 {checklist.conditions.destination} チェックリスト",
        description=f"期間: {checklist.conditions.start_date} ～ {checklist.conditions.end_date}",
        color=discord.Color.blue()
    )
    
    # カテゴリ別グループ化
    items_by_category = {}
    for item in checklist.items:
        if item.category not in items_by_category:
            items_by_category[item.category] = []
        items_by_category[item.category].append(item)
    
    # カテゴリ別フィールド追加
    for category, items in items_by_category.items():
        # 最初の5項目のみ表示
        displayed_items = items[:5]
        
        value_lines = []
        for item in displayed_items:
            status = "☑️" if item.checked else "⬜"
            line = f"{status} {item.name}"
            if item.auto_added and item.reason:
                line += f" *(自動追加: {item.reason})*"
            value_lines.append(line)
        
        if len(items) > 5:
            value_lines.append(f"... 他{len(items)-5}項目")
        
        embed.add_field(
            name=f"📋 {category}",
            value="\\n".join(value_lines) or "なし",
            inline=False
        )
    
    # 統計情報
    total_items = len(checklist.items)
    completed_items = sum(1 for item in checklist.items if item.checked)
    auto_added_count = sum(1 for item in checklist.items if item.auto_added)
    
    embed.add_field(
        name="📊 統計",
        value=f"総数: {total_items}項目\\n完了: {completed_items}項目\\n自動追加: {auto_added_count}項目",
        inline=True
    )
    
    progress_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
    embed.add_field(
        name="🎯 進捗",
        value=f"{progress_percentage:.1f}%",
        inline=True
    )
    
    return embed
```

## エラーハンドリングと品質保証

### カスタム例外クラス
```python
class SmartTemplateError(Exception):
    """スマートテンプレート関連のエラー"""
    pass

class TemplateNotFoundError(SmartTemplateError):
    """テンプレートが見つからない"""
    pass

class WeatherAPIError(SmartTemplateError):
    """天気API接続エラー"""
    pass
```

### 非同期処理でのタイムアウト管理
```python
import asyncio
from typing import Union

async def with_timeout(coro, timeout_seconds: float = 10.0) -> Union[any, None]:
    """タイムアウト付き非同期実行"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout_seconds}s")
        return None
```

## 設定管理

### 環境別設定
```python
# src/config/settings.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Discord
    discord_token: str
    discord_guild_id: Optional[int] = None
    
    # GitHub
    github_token: str
    github_repo: str = "travel-records"
    github_owner: str
    
    # External APIs
    openweather_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    
    # Feature flags
    enable_weather_integration: bool = True
    enable_ai_suggestions: bool = False
    enable_personal_learning: bool = False
    
    # Performance
    max_concurrent_adjustments: int = 5
    api_timeout_seconds: float = 10.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# グローバル設定インスタンス
settings = Settings()
```

## 段階的機能拡張

### Phase 1実装範囲
- ✅ 基本テンプレート選択
- ✅ 地域・天気・期間調整
- ✅ Discord UI統合
- ❌ AI学習機能（Phase 3まで延期）

### Phase 2拡張予定
- 個人履歴による調整
- より詳細な天気予報連携
- 交通手段特化調整

### Phase 3 AI統合
- Claude APIによる高度な予測
- 学習データに基づく個人最適化
- プロアクティブな提案機能
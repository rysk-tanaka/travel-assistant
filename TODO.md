# TravelAssistant 開発TODO

## 🚀 Phase 1: MVP構築（基本機能）

### 🔥 High Priority（今すぐ実装） ✅ 完了

- [x] **環境設定準備**
  - [x] `.env.example` ファイル作成
  - [x] 必要な環境変数の定義（DISCORD_TOKEN, GITHUB_TOKEN等）
  - [x] 環境変数の説明ドキュメント作成

- [x] **Discord Bot セットアップ**
  - [x] Discord Developer Portal でアプリケーション作成
  - [x] Bot Token 取得
  - [x] Bot の基本権限設定（Send Messages, Use Slash Commands等）
  - [x] テストサーバーへのBot招待

- [x] **基本テンプレートファイル作成**
  - [x] `src/templates/domestic_business.md` - 国内出張用
  - [x] `src/templates/leisure_domestic.md` - レジャー旅行用
  - [x] `src/templates/base_travel.md` - ベーステンプレート
  - [x] `src/templates/business_long_distance.md` - 長距離出張用
  - [x] `src/templates/business_short_distance.md` - 短距離出張用
  - [x] テンプレートのYAML Front Matter設計
  - [x] モジュール化されたテンプレート（modules/）

### ⚡ Medium Priority（基本機能実装）

- [x] **データモデル実装**
  - [x] `src/models.py` にPydanticモデル作成
    - [x] `TripRequest` - 旅行リクエスト
    - [x] `ChecklistItem` - チェックリスト項目
    - [x] `TripChecklist` - チェックリスト全体
  - [x] バリデーション機能の実装

- [x] **基本Discord コマンド実装**
  - [x] `/trip smart` スラッシュコマンド実装
  - [x] 基本的な引数検証
  - [x] シンプルなチェックリスト生成
  - [x] Discord Embed での結果表示
  - [x] スマートエンジン（`src/core/smart_engine.py`）実装

- [x] **テンプレート処理機能**
  - [x] `src/utils/markdown_utils.py` 作成
  - [x] Markdownファイル読み込み機能
  - [x] Front Matter解析機能
  - [x] テンプレート変数置換機能

- [x] **GitHub連携基礎** ✅ 実装済み
  - [x] `src/core/github_sync.py` 作成
  - [x] GitHub API認証
  - [x] ファイル作成・更新機能
  - [x] リポジトリ操作の基本機能

- [x] **Discord UI改善** ✅ 実装済み
  - [x] インタラクティブボタン実装
  - [x] チェックリスト項目の選択・更新UI（`checklist_check.py`）
  - [x] チェックリスト詳細表示機能（`checklist_detail.py`）
  - [x] 進捗表示機能
  - [x] エラーメッセージの改善

### 🔧 Low Priority（品質向上）

- [x] **エラーハンドリング・ログ** ✅ 実装済み
  - [x] structlog設定（`src/utils/logging_config.py`）
  - [ ] カスタム例外クラス作成
  - [x] 適切なエラーメッセージ表示
  - [x] デバッグ用ログ出力

- [x] **テスト実装** ✅ 実装済み
  - [x] 基本機能の単体テスト
  - [x] Pydanticモデルのテスト（`test_models.py`）
  - [x] スマートエンジンのテスト（`test_smart_engine.py`）
  - [x] Markdownユーティリティのテスト（`test_markdown_utils.py`）
  - [x] 設定のテスト（`test_settings.py`）

- [x] **GitHub履歴表示機能** ✅ 実装済み（2025-07-01）
  - [x] GitHubからのチェックリスト読み込み機能
  - [x] Markdownパース機能（`_parse_markdown_to_checklist`）
  - [x] 履歴選択UI（ドロップダウンメニュー）
  - [x] `/trip_history`コマンドの拡張

## 🌟 Phase 2: スマート機能拡張

### 🌤️ 外部API連携

- [x] **天気予報連携** ✅ 実装済み
  - [x] OpenWeatherMap API設定
  - [x] 天気データ取得機能
  - [x] 天気に基づく持ち物調整
  - [x] キャッシュ機能実装

### 🧠 自動調整機能

- [ ] **地域特性調整**
  - [ ] 地域別ルールデータベース作成
  - [ ] 季節・月別調整ロジック
  - [ ] 地域マッチング機能

- [x] **交通手段別調整** ✅ 実装済み
  - [x] 飛行機利用時の特別項目
  - [x] 新幹線・電車利用時の調整
  - [x] 車移動時の特別準備
  - [x] バス・その他交通手段対応
  - [x] 季節別・条件別の詳細調整

- [ ] **期間別最適化**
  - [ ] 短期・長期滞在の調整
  - [ ] 宿泊数に応じた持ち物計算
  - [ ] 洗濯・補給タイミング考慮

## 🚀 Phase 3: AI機能統合

### ✈️ 移動スケジュール連携機能（新規追加）

- [ ] **Phase 3-A: 基礎実装**
  - [ ] データモデル定義（FlightInfo, AccommodationInfo, TripItinerary）
  - [ ] モデルのテスト作成
  - [ ] 基本的なDiscordコマンド実装（/schedule）
  - [ ] 手動でのフライト・ホテル情報入力機能
  - [ ] タイムライン表示機能

- [ ] **Phase 3-B: 連携強化**
  - [ ] スマートチェックリストとの統合
  - [ ] スケジュールベースの持ち物調整
  - [ ] 早朝便・長時間フライト対応

- [ ] **Phase 3-C: 自動化**
  - [ ] JAL予約確認メールパーサー
  - [ ] ANA予約確認メールパーサー
  - [ ] 主要ホテルサイトのメールパーサー
  - [ ] エラーハンドリング・フォールバック

- [ ] **Phase 3-D: リマインダー機能**
  - [ ] APScheduler導入
  - [ ] オンラインチェックイン通知
  - [ ] 移動時間の自動計算
  - [ ] チェックアウト時刻通知

### 🤖 Claude API連携

- [ ] **学習型最適化**
  - [ ] 過去データ蓄積機能
  - [ ] 個人パターン分析
  - [ ] 忘れ物予測機能

- [ ] **プロアクティブ提案**
  - [ ] 天気変化の事前通知
  - [ ] 交通情報連携
  - [ ] イベント・状況に応じた提案

## 📝 継続的改善・メンテナンス

### 📊 品質管理

- [ ] **コード品質**
  - [ ] カバレッジ80%以上維持
  - [ ] 型チェック100%通過
  - [ ] リンターエラー0件維持

- [ ] **ドキュメント更新**
  - [ ] 実装に応じたREADME更新
  - [ ] API仕様書の更新
  - [ ] 使用方法ガイドの改善

### 🔒 セキュリティ・運用

- [ ] **セキュリティ強化**
  - [ ] 環境変数の適切な管理
  - [ ] APIキーの定期ローテーション
  - [ ] プライベートデータの保護

- [ ] **パフォーマンス最適化**
  - [ ] レスポンス時間の計測・改善
  - [ ] メモリ使用量の最適化
  - [ ] API呼び出し回数の最小化

## 📅 現在の目標

### 🎯 Phase 1完了とPhase 2準備（今週）

#### ✅ Phase 1 達成事項

1. **環境設定完了** ✅ Discord Bot Token取得・設定済み
2. **テンプレート作成** ✅ 5つのテンプレート＋モジュール化実装
3. **データモデル実装** ✅ Pydanticモデル完成
4. **コマンド実装** ✅ `/trip smart`動作中・UI実装済み
5. **テスト実装** ✅ 主要機能のテスト作成済み

#### ✅ Phase 1 完了

🎉 **Phase 1の全タスクが完了しました！**

- GitHub連携実装済み（PyGitHub導入、保存・読み込み機能）

#### 🌟 Phase 2 準備

1. **天気予報API調査**
   - [ ] OpenWeatherMap API キー取得
   - [ ] API仕様確認・実装計画
2. **地域特性データ設計**
   - [ ] 地域別ルールのデータ構造設計
   - [ ] YAMLまたはJSONでの管理方法検討

### ✅ 完了判定基準（Phase 1）

- [x] Discord Botが起動し、基本コマンドに応答する
- [x] テンプレートから基本的なチェックリストが生成される
- [x] Discord Embedで結果が表示される
- [x] インタラクティブなUI（ボタン・セレクト）が動作する
- [x] エラーが発生せずに動作する
- [x] GitHubにチェックリストが保存される

---

## 🛠️ 開発フロー

### 毎回の作業開始時

1. `make check` でコード品質確認
2. 現在のTODO確認・優先度調整
3. 実装→テスト→コミットのサイクル

### 定期チェック（週次）

- [ ] TODOの進捗確認・優先度見直し
- [ ] 設計書との乖離確認
- [ ] 新しい要求事項の整理

---

*最終更新: 2025-07-01*
*次回レビュー予定: Phase 2開始時*

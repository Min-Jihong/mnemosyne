<div align="center">

# 🧠 Mnemosyne

### *もう一人の自分を創る*

**あなたのように考えることを学ぶデジタルクローン**

日本語 | [English](README.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/Min-Jihong/mnemosyne/actions/workflows/ci.yml/badge.svg)](https://github.com/Min-Jihong/mnemosyne/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/Min-Jihong/mnemosyne?style=social)](https://github.com/Min-Jihong/mnemosyne)
[![GitHub forks](https://img.shields.io/github/forks/Min-Jihong/mnemosyne?style=social)](https://github.com/Min-Jihong/mnemosyne/fork)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</div>

---

## 🪞 デジタル自己の夢

> *誰もが一度は「もう一人の自分」を作りたいと思ったことがあるでしょう。*

自分が寝ている間も働く自分。疲れている時も考える自分。自分の習慣を知り、好みを理解し、自分のように決断する存在。

**Mnemosyne**はその夢を現実にするプロジェクトです。

コンピュータ上でのすべての行動 — マウスクリック、キーボード入力、アプリ切り替え、スクロール — を記録し、AIが**「なぜこの行動をしたのか？」**と絶えず問いかけながら学習します。単に行動を模倣するのではなく、**あなたの思考パターン自体を学習**します。

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│     「なぜそこをクリックしましたか？」                             │
│     「アプリを切り替えた時、何を考えていましたか？」               │
│     「Xをする前にいつもYをしますね。なぜですか？」                 │
│                                                                    │
│                    — Mnemosyne、あなたになるために学習中           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

<div align="center">

## ⭐ なぜこのプロジェクトにスターを？

</div>

<table>
<tr>
<td width="50%">

### 🎯 **記録だけではない — 理解する**
他のツールがピクセルをキャプチャする中、Mnemosyneは**意図**をキャプチャします。AIはすべてのアクションの後に「なぜ？」と問いかけ、あなたの思考モデルを構築します。

### 🔍 **OCRで過去を検索**
先週見たあれを探せます。OCRがすべてのスクリーンショットをインデックス化し、テキスト内容で検索できます。

</td>
<td width="50%">

### 📊 **自分をもっと知る**
AI生成の日次サマリーと生産性統計が、自分の行動について気づかなかったパターンを明らかにします。

### ⏪ **アクションをタイムトラベル**
任意のセッションを再生して、何をしたか、いつしたか、そして（AIのおかげで）*なぜ*したかを正確に確認できます。

</td>
</tr>
</table>

<div align="center">

**あなたを見るだけでなく — *あなたになることを学ぶ*唯一のツール。**

</div>

---

## 🎬 動作デモ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MNEMOSYNE WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   YOU                          MNEMOSYNE                        OUTPUT      │
│    │                              │                               │         │
│    │  ┌─────────────────┐        │                               │         │
│    ├──│ Click, Type,    │───────►│  📹 CAPTURE                   │         │
│    │  │ Scroll, Switch  │        │  Every micro-action           │         │
│    │  └─────────────────┘        │         │                     │         │
│    │                             │         ▼                     │         │
│    │                             │  🤔 REASON                    │         │
│    │  ┌─────────────────┐        │  "Why did you do that?"       │         │
│    │◄─│ AI asks you     │◄───────│         │                     │         │
│    │  │ curious Qs      │        │         ▼                     │         │
│    │  └─────────────────┘        │  🧠 REMEMBER                  │         │
│    │                             │  Patterns → Memory            │         │
│    │                             │         │                     │         │
│    │                             │         ▼                     │         │
│    │                             │  ┌─────────────────────────┐  │         │
│    │                             │  │ 📊 Daily Summary        │──┼────►    │
│    │                             │  │ 🔍 OCR Search           │  │         │
│    │                             │  │ ⏪ Action Replay        │  │         │
│    │                             │  │ 🤖 Execute Goals        │  │         │
│    │                             │  └─────────────────────────┘  │         │
│    │                                                             │         │
└────┴─────────────────────────────────────────────────────────────┴─────────┘

$ mnemosyne summary today
┌──────────────────────────────────────────────────────────────────┐
│  📊 YOUR DAY AT A GLANCE                        Feb 11, 2026     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ⏱️  Active Time: 6h 42m                                         │
│  🖱️  Clicks: 2,847  |  ⌨️  Keystrokes: 18,392                    │
│  🔄  App Switches: 234  |  📸 Screenshots: 89                    │
│                                                                  │
│  🏆 TOP APPS                    🧠 AI INSIGHTS                   │
│  ├─ VS Code      3h 12m        "You context-switch less on      │
│  ├─ Chrome       1h 45m         Tuesdays. Consider blocking      │
│  ├─ Slack          38m          Slack until noon?"               │
│  └─ Terminal       27m                                           │
│                                                                  │
│  💡 "You typed 'git status' 47 times but only committed 5x.     │
│      That's a 9:1 check-to-commit ratio. Anxiety or process?"   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## ✨ Mnemosyneの特徴

| 従来の自動化ツール | Mnemosyne |
|-------------------|-----------|
| **何を**したかを記録 | **なぜ**したかを理解 |
| 固定スクリプトの再生 | 新しい状況に適応 |
| セッション間の記憶なし | すべてを永遠に記憶 |
| 受動的なツール | 能動的に好奇心を持つAI |

---

## 🏆 競合製品との比較

| 機能 | Mnemosyne | Screenpipe | OpenAdapt | Rewind |
|------|:---------:|:----------:|:---------:|:------:|
| **マイクロアクションキャプチャ** | ✅ | ❌ | ✅ | ❌ |
| **意図推論（なぜ？）** | ✅ | ❌ | ❌ | ❌ |
| **好奇心を持つAI質問** | ✅ | ❌ | ❌ | ❌ |
| **OCRテキスト検索** | ✅ | ✅ | ❌ | ✅ |
| **AI日次サマリー** | ✅ | ❌ | ❌ | ❌ |
| **アクションリプレイ** | ✅ | ❌ | ✅ | ❌ |
| **セマンティックメモリ** | ✅ | ❌ | ❌ | ❌ |
| **目標実行** | ✅ | ❌ | ✅ | ❌ |
| **マルチLLMサポート** | ✅ | ❌ | ✅ | ❌ |
| **ローカルファースト/プライバシー** | ✅ | ✅ | ✅ | ❌ |
| **プライバシー保護（PII）** | ✅ | ❌ | ✅ | ❌ |
| **ビジュアルグラウンディング（Set-of-Mark）** | ✅ | ❌ | ✅ | ❌ |
| **イベント集約** | ✅ | ❌ | ✅ | ❌ |
| **オープンソース** | ✅ | ✅ | ✅ | ❌ |

**Screenpipe** = 音声/動画フォーカス | **OpenAdapt** = ビジュアルグラウンディングRPA | **Rewind** = OCR検索（クローズドソース）

---

## 🎯 主な機能

### 📹 マイクロアクション記録
ミリ秒単位の精度ですべての操作をキャプチャ：
- **マウス**: 位置、クリック、ダブルクリック、ドラッグ、スクロール、ホバー時間
- **キーボード**: キー入力、ショートカット、タイピング速度とパターン
- **画面**: 重要なアクション時の自動スクリーンショット
- **コンテキスト**: アクティブアプリ、ウィンドウタイトル、URL、ファイルパス

### 🤔 好奇心を持つLLM
受動的な記録ツールとは異なり、MnemosyneのAIは**本当に好奇心を持っています**：

```python
# AIは見るだけではない — 質問する
curiosities = await curious_llm.observe_and_wonder(events)

# 出力例：
# 「今日、VS CodeからChromeに47回も切り替えたのはなぜですか？」
# 「文章を書いた後、いつも上にスクロールしますね。読み返しですか？」
# 「'git commit'の前に3秒間止まりますね。迷いですか？」
```

### 📊 分析とインサイト
**新機能！** これまでにない方法で作業パターンを理解：

```bash
# AI生成の日次サマリーを取得
$ mnemosyne summary today

📊 日次サマリー - 2026年2月11日
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 メインフォーカス: バックエンドAPI開発
   アクティブ時間の68%をVS Codeで認証モジュールの作業に費やしました。

💡 重要なインサイト: 最も生産的な時間は午前9-11時でした。
   この時間帯にディープワークをスケジュールすることを検討してください。

⚠️  パターンアラート: 昼食後30分間に12回のコンテキストスイッチ。
   これはコード出力の低下と相関しています。

# 詳細な生産性統計を取得
$ mnemosyne stats week

📈 週間統計
├─ 総アクティブ時間: 34時間12分
├─ 最も使用したアプリ: VS Code (18時間45分)
├─ ピーク生産性: 火曜日 9:00-11:30am
├─ 平均セッション長: 47分
└─ フォーカススコア: 7.2/10 (↑ 先週から0.8上昇)
```

### 🔍 OCR検索
**新機能！** 画面で見たものを何でも検索：

```bash
# すべてのスクリーンショットからテキストを検索
$ mnemosyne search "API_KEY"

🔍 3件の一致が見つかりました:

1. [2月10日, 14:32] VS Code - .envファイル
   "OPENAI_API_KEY=sk-..."
   
2. [2月9日, 11:15] Chrome - OpenAIダッシュボード
   "Your API_KEY has been rotated"
   
3. [2月8日, 16:45] Slack - #devチャンネル
   "Can someone share the API_KEY for staging?"
```

### ⏪ アクションリプレイ
**新機能！** セッションをタイムトラベル：

```bash
# 録画されたセッションを再生
$ mnemosyne replay ses_abc123

⏪ セッション再生中: "朝のコーディング" (2026年2月10日)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[09:00:15] 🖱️  クリック: DockのVS Codeアイコン
[09:00:16] ⌨️  ホットキー: Cmd+Shift+P (コマンドパレット)
[09:00:18] ⌨️  入力: "git pull"
[09:00:19] 🖱️  クリック: ターミナルパネル
           💭 意図: "作業開始前に最新の変更を同期"
[09:00:25] ⌨️  ホットキー: Cmd+P (クイックオープン)
[09:00:27] ⌨️  入力: "auth.py"
           💭 意図: "認証モジュールの作業を継続"

操作: [Space] 一時停止 | [←/→] ステップ | [Q] 終了 | [S] 速度
```

### 🔒 プライバシー保護
**新機能！** 自動PII検出とマスキング：

```bash
# プライバシー設定を確認
$ mnemosyne privacy status

🔒 プライバシー保護: 有効
   レベル: standard
   PIIタイプ: email, phone, ssn, credit_card, api_key, password

# PII検出をテスト
$ mnemosyne privacy test "Contact john@email.com or call 555-123-4567"

🔍 PII検出:
   [EMAIL] john@email.com → [EMAIL_REDACTED]
   [PHONE] 555-123-4567 → [PHONE_REDACTED]

# ファイルをスクラブ
$ mnemosyne privacy scrub-file ./notes.txt
✅ 3件のPIIインスタンスをスクラブ → ./notes.scrubbed.txt
```

**サポートされるPIIタイプ:**
- 📧 メールアドレス
- 📞 電話番号
- 🆔 SSN / マイナンバー
- 💳 クレジットカード番号
- 🔑 APIキー & シークレット
- 🔐 パスワード（URL、設定ファイル内）
- 🌐 IPアドレス & MACアドレス

### 🎯 ビジュアルグラウンディング（Set-of-Mark）
**新機能！** コンピュータ制御のためのAI駆動UI要素検出：

```bash
# スクリーンショット内のUI要素を検出
$ mnemosyne ground screenshot.png --prompt

🎯 UI要素検出: 12件

[1] BUTTON @ (145, 230) - "Submit"
[2] INPUT @ (120, 180) - テキストフィールド
[3] LINK @ (50, 320) - "Learn more"
[4] BUTTON @ (290, 230) - "Cancel"
...

📝 Set-of-Markプロンプト生成:
"スクリーンショットには以下のインタラクティブ要素を持つフォームが表示されています:
 [1] 右上のSubmitボタン
 [2] メール用テキスト入力フィールド
 [3] 下部の'Learn more'リンク
 [4] Submitの隣のCancelボタン
 
 フォームを送信するには、要素[1]をクリックしてください。"
```

### 📦 イベント集約
**新機能！** 繰り返しイベントをマージしてノイズを削減：

```bash
# セッション内のイベントを集約
$ mnemosyne aggregate ses_abc123

📦 集約結果:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   元のイベント数: 15,847
   集約後:         1,234
   圧縮率:         92.2%

   🖱️  マウス移動: 12,456 → 89軌跡
   📜 スクロールイベント: 1,203 → 45スクロールアクション
   ⌨️  キーストローク: 2,188 → 156タイピングセグメント
   
   💾 ストレージ節約: 14.2 MB → 1.1 MB
```

### 🧠 永続メモリ
忘れないメモリシステム：
- **セマンティック検索**: キーワードではなく意味で記憶を検索
- **メモリ統合**: パターンからインサイトを自動生成
- **ベクトルストア**: 高速検索のためのChromaDB
- **長期学習**: 数週間、数ヶ月にわたる理解の構築

### 🤖 実行エージェント
デジタルツインがアクションを実行：
- 目標指向のコンピュータ制御
- 安全機能（レート制限、ブロックアプリ、緊急停止）
- 慎重な実行のための確認モード
- あなたの修正から学習

### 🔌 マルチプロバイダーLLMサポート
信頼するAIプロバイダーを使用：
- **OpenAI**: GPT-4, GPT-4 Turbo
- **Anthropic**: Claude 3, Claude 3.5
- **Google**: Gemini Pro, Gemini Ultra
- **Ollama**: Llama, Mistralなどをローカル実行

### 🌐 Webインターフェース
どこからでもデジタルツインとチャット：
- **モダンなチャットUI** で自然言語対話
- **APIキー設定** をブラウザで
- **録画制御** ダッシュボード
- **メモリ検索** インターフェース

---

## 🚀 クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/Min-Jihong/mnemosyne.git
cd mnemosyne

# pipでインストール
pip install -e .

# Webインターフェース用
pip install -e ".[web]"

# macOSネイティブキャプチャ（推奨）
pip install -e ".[macos]"

# ML学習機能用
pip install -e ".[ml]"

# 全機能
pip install -e ".[all]"
```

### 権限の付与（macOS）

Mnemosyneには以下の権限が必要です：

| 権限 | 場所 | 理由 |
|------|------|------|
| **アクセシビリティ** | システム設定 → プライバシー → アクセシビリティ | マウス/キーボードキャプチャ |
| **入力監視** | システム設定 → プライバシー → 入力監視 | キーボードイベント |
| **画面収録** | システム設定 → プライバシー → 画面収録 | スクリーンショット |

### セットアップ

```bash
mnemosyne setup
```

このインタラクティブウィザードで設定：
- 🔑 LLMプロバイダーとAPIキー
- 🤖 モデル選択
- 🧠 好奇心モード（passive/active/proactive）

---

## 📖 使い方

### Webインターフェース（推奨）

```bash
# Web UIを起動
mnemosyne web

# ブラウザで http://localhost:8000 を開く
```

Webインターフェースでできること：
- デジタルツインとチャット
- APIキーでLLM設定を構成
- 録画セッションの開始/停止
- メモリを検索

### コマンドライン

#### 録画開始

```bash
# 録画セッションを開始
mnemosyne record --name "作業セッション"

# 録画中... すべてのアクションがキャプチャされています。
# Ctrl+Cで停止。
```

#### AIで分析

```bash
# セッションを分析 - AIが各アクションの意図を推論
mnemosyne analyze abc123

# 好奇心を持つAIに行動について質問させる
mnemosyne curious abc123
```

**好奇心出力の例:**
```
🤔 セッションについての質問:

1. [HIGH] なぜいつもメールをチェックする前にSlackを開くのですか？
   カテゴリ: workflow | 信頼度: 0.89

2. [MEDIUM] "git status"を23回入力しましたが、コミットは3回だけです。なぜですか？
   カテゴリ: habit | 信頼度: 0.72

3. [HIGH] ターミナルに切り替える前に一貫して2秒間の停止があります。
   カテゴリ: decision | 信頼度: 0.85
```

#### メモリ操作

```bash
# セマンティックにメモリを検索
mnemosyne memory "朝のルーティン"

# 最近のメモリを閲覧
mnemosyne memory --recent

# 重要なインサイトを検索
mnemosyne memory --important
```

#### 目標実行

```bash
# 学習した行動に基づいて目標を実行
mnemosyne execute "いつもの開発環境をセットアップ"

# 確認モード付き（より安全）
mnemosyne execute "保留中のメッセージに返信" --confirm
```

---

## 🎮 CLIリファレンス

| コマンド | 説明 |
|---------|------|
| `mnemosyne setup` | インタラクティブ設定ウィザード |
| `mnemosyne web` | **Webインターフェース起動** |
| `mnemosyne record` | アクティビティ録画開始 |
| `mnemosyne sessions` | 録画セッション一覧 |
| `mnemosyne analyze <id>` | AIがセッションの意図を分析 |
| `mnemosyne curious <id>` | AIが行動について質問 |
| `mnemosyne memory [query]` | メモリ検索・閲覧 |
| `mnemosyne export <id>` | トレーニング用にセッションをエクスポート |
| `mnemosyne execute <goal>` | 目標を実行 |
| `mnemosyne status` | 現在の設定を表示 |
| `mnemosyne version` | バージョンを表示 |
| | |
| **📊 分析** | |
| `mnemosyne summary [today\|yesterday\|week]` | AI生成の日次/週次サマリー |
| `mnemosyne stats [today\|yesterday\|week]` | 作業統計と生産性メトリクス |
| | |
| **🔍 検索 & リプレイ** | |
| `mnemosyne search <query>` | スクリーンショット全体のOCRテキスト検索 |
| `mnemosyne replay <session_id>` | 意図付きで録画アクションを再生 |
| | |
| **🔒 プライバシー & 処理** | |
| `mnemosyne privacy status` | プライバシー保護設定を表示 |
| `mnemosyne privacy enable/disable` | PII保護の切り替え |
| `mnemosyne privacy level [aggressive\|standard\|minimal]` | 保護レベルを設定 |
| `mnemosyne privacy test <text>` | PII検出をテスト |
| `mnemosyne ground <image>` | UI要素を検出（Set-of-Mark） |
| `mnemosyne aggregate <session_id>` | 繰り返しイベントを圧縮 |

---

## ⚙️ 設定

設定は `~/.mnemosyne/config.toml` に保存されます：

```toml
[llm]
provider = "anthropic"  # openai, anthropic, google, ollama
model = "claude-3-opus-20240229"
api_key = "your-api-key"

[curiosity]
mode = "active"  # passive, active, proactive

[recording]
screenshot_quality = 80
screenshot_format = "webp"
mouse_throttle_ms = 50
```

---

## 🏗️ プロジェクト構造

```
mnemosyne/
├── capture/      # 入力記録（マウス、キーボード、画面）
├── store/        # SQLiteデータベースとセッション管理
├── reason/       # LLM推論と好奇心質問
├── memory/       # ベクトル検索付き永続メモリ
├── learn/        # トレーニングパイプラインとデータセット
├── execute/      # コンピュータ制御エージェント
├── llm/          # マルチプロバイダーLLM抽象化
├── analytics/    # サマリー生成と統計
├── ocr/          # スクリーンショットテキスト抽出と検索
├── replay/       # セッション再生エンジン
├── privacy/      # PII検出と保護
├── grounding/    # ビジュアルUI要素検出（Set-of-Mark）
├── aggregation/  # イベント圧縮とパス簡略化
├── config/       # 設定と構成
├── cli/          # コマンドラインインターフェース
└── web/          # Webインターフェース（FastAPI + HTML/JS）
```

---

## 🔄 仕組み

### 1. キャプチャフェーズ
実行するすべてのマイクロアクションを記録：
- マウス位置、クリック、スクロール
- キーボード入力とホットキー
- 重要な瞬間のスクリーンショット
- アクティブウィンドウコンテキスト

### 2. 推論フェーズ
好奇心を持つLLMがアクションを分析：
- **「なぜそこをクリックしましたか？」**
- **「タイピングにどんなパターンがありますか？」**
- **「なぜアプリAからアプリBに切り替えましたか？」**

### 3. 学習フェーズ
パターンが抽出され学習される：
- アクションシーケンスが習慣になる
- 意図が予測可能になる
- あなたの「デジタルツイン」が出現

### 4. 実行フェーズ
学習したモデルが行動できる：
- 過去の行動に基づいて目標を実行
- 安全機能が危険なアクションを防止
- 機密操作には確認が必要

---

## 🛡️ 安全機能

Mnemosyneには複数の安全メカニズムが含まれています：

- **レート制限**: デフォルトで最大60アクション/分
- **ブロックアプリ**: ターミナル、パスワードマネージャー、システム環境設定
- **ブロックホットキー**: Cmd+Q、Cmd+Shift+Qなど
- **セーフゾーン**: 特定の画面領域にアクションを制限
- **緊急停止**: すべてのアクションを即座に停止

---

## 🤝 貢献

貢献を歓迎します！PRを送る前に貢献ガイドラインをお読みください。

---

## 📄 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)を参照してください。

---

## 🙏 謝辞

- [OpenClaw](https://github.com/openclaw) - コンピュータ制御のコンセプト
- [OpenAdapt](https://github.com/OpenAdaptAI/OpenAdapt) - 記録パターン
- [pynput](https://github.com/moses-palmer/pynput) - 入力監視

---

<div align="center">

**Mnemosyneが自分自身をより深く理解する助けになったら、⭐をお願いします**

*自分自身をもっと知りたいと思った人間たちが、好奇心を持って作りました。*

</div>

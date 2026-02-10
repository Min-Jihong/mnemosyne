<div align="center">

# 🧠 Mnemosyne

### *もう一人の自分を創る*

**あなたのように考えることを学ぶデジタルクローン**

日本語 | [English](README.md) | [한국어](README.ko.md) | [中文](README.zh-CN.md)

[![CI](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/mnemosyne/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos)

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

## ✨ Mnemosyneの特徴

| 従来の自動化ツール | Mnemosyne |
|-------------------|-----------|
| **何を**したかを記録 | **なぜ**したかを理解 |
| 固定スクリプトの再生 | 新しい状況に適応 |
| セッション間の記憶なし | すべてを永遠に記憶 |
| 受動的なツール | 能動的に好奇心を持つAI |

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
git clone https://github.com/yourusername/mnemosyne.git
cd mnemosyne

# pipでインストール
pip install -e .

# Webインターフェース用
pip install -e ".[web]"

# TUI用
pip install -e ".[tui]"

# macOSネイティブキャプチャ（推奨）
pip install -e ".[macos]"

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

---

## 📖 使い方

### Webインターフェース（推奨）

```bash
# Web UIを起動
mnemosyne web

# ブラウザで http://localhost:8000 を開く
```

### TUI（ターミナルUI）

```bash
# Textual TUIを起動
mnemosyne tui
```

### コマンドライン

```bash
# 録画開始
mnemosyne record --name "作業セッション"

# セッション分析
mnemosyne analyze abc123

# メモリ検索
mnemosyne memory "朝のルーティン"

# 目標実行
mnemosyne execute "開発環境をセットアップ"
```

---

## 🎮 CLIリファレンス

| コマンド | 説明 |
|---------|------|
| `mnemosyne setup` | インタラクティブ設定ウィザード |
| `mnemosyne web` | Webインターフェース起動 |
| `mnemosyne tui` | ターミナルUI起動 |
| `mnemosyne record` | アクティビティ録画開始 |
| `mnemosyne sessions` | 録画セッション一覧 |
| `mnemosyne analyze <id>` | AIがセッションを分析 |
| `mnemosyne memory [query]` | メモリ検索・閲覧 |
| `mnemosyne execute <goal>` | 目標を実行 |
| `mnemosyne status` | 設定状態を表示 |

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

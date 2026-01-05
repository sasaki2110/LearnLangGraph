# ex99_sns_post_editor - SNS投稿エディターエージェント

このプロジェクトは、Human-in-the-loopの練習として、LangGraphの中断（Interrupt）と再開機能を使用したSNS投稿エディターエージェントです。
LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
ex99_sns_post_editor/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（ログ付き）
├── tests/                # テストファイル
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## 機能

このエージェントは、以下の4つのノードで処理を行います：

1. **テーマ取得ノード（extract_theme）**: ユーザー入力をthemeへ格納する
2. **投稿作成ノード（create_draft_post）**: themeをもとに、SNSへの投稿を生成し、draft_postへ格納
3. **中断ノード（request_approval）**: interruptを発行し、処理継続をユーザーへ問い合わせる。draft_postをユーザーへ提示し、y/nを入力してもらう
4. **最終投稿生成ノード（refine_final_post）**: draft_postをリファインし最終ポストfinal_postを作成する

## グラフ構造

```
start
  ↓
テーマ取得ノード（extract_theme）
  ↓
投稿作成ノード（create_draft_post）
  ↓
中断ノード（request_approval）
  ↓
  ├─ approved=true → 最終投稿生成ノード（refine_final_post） → end
  └─ approved=false → end
```

## 状態

- **messages**: メッセージ履歴
- **theme**: ユーザーが指定した投稿のテーマ
- **draft_post**: 投稿下書き（承認前）
- **final_post**: 最終投稿
- **approved**: 承認状態

## セットアップ

### 1. 依存関係のインストール

以下の依存関係が必要です：
- langchain
- langchain-openai
- langgraph
- python-dotenv (オプション)

親フォルダで実行済みの場合、それらを使用できます。

### 2. 環境変数の設定

親フォルダで実行済み。

### 3. LangGraph Studioで実行

```bash
cd /root/LearnLangGraph/archives/ex99_sns_post_editor
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **LangGraph Studio**: `http://127.0.0.1:8123`

## 使用方法

### 基本的な使用例

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

# テーマを指定して投稿を作成
result = graph.invoke({
    "messages": [HumanMessage(content="今日の天気について")]
})

print("テーマ:", result["theme"])
print("下書き:", result["draft_post"])
print("承認状態:", result["approved"])
if result.get("final_post"):
    print("最終投稿:", result["final_post"])
```

### ストリーミング使用例

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

# ストリーミングで実行
for chunk in graph.stream({
    "messages": [HumanMessage(content="今日の天気について")]
}, stream_mode="updates"):
    node_name = list(chunk.keys())[0]
    print(f"\nノード: {node_name}")
    update = chunk[node_name]
    if "theme" in update:
        print(f"  テーマ: {update['theme']}")
    if "draft_post" in update:
        print(f"  下書き: {update['draft_post'][:100]}...")
    if "approved" in update:
        print(f"  承認状態: {update['approved']}")
    if "final_post" in update:
        print(f"  最終投稿: {update['final_post'][:100]}...")
```

### 中断（Interrupt）の使い方

このエージェントは、投稿作成後に中断（interrupt）を発行します。
LangGraph StudioやLangSmith Studioでは、中断時にユーザーが承認/拒否を選択できます。

1. **投稿作成**: LLMが投稿下書きを作成
2. **中断**: ユーザーに承認を求める中断が発生
3. **承認/拒否**: ユーザーが 'y' または 'n' を入力
4. **再開**: 承認された場合、最終投稿を生成

## ロギング機能

このエージェントは、p30_loggingを参考にした日本語ログを出力します。

### ログレベル

環境変数 `LOG_LEVEL` で設定可能：
- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 一般的な情報（デフォルト）
- `WARNING`: 警告メッセージ
- `ERROR`: エラーメッセージ

### ログの種類

- **📝 [EXTRACT_THEME]**: テーマ取得ノードのログ
- **✍️ [CREATE_DRAFT_POST]**: 投稿作成ノードのログ
- **⏸️ [REQUEST_APPROVAL]**: 承認要求ノードのログ（中断・再開を含む）
- **✨ [REFINE_FINAL_POST]**: 最終投稿生成ノードのログ
- **🚀 [AGENT]**: エージェント初期化のログ
- **🔀 [ROUTING]**: ルーティング判定のログ
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `ex99_sns_post_editor.log` ファイルを確認
3. **エラーログ**: `ex99_sns_post_editor_error.log` ファイルでエラーのみを確認

## 特徴

- **Human-in-the-loop**: LangGraphの中断（Interrupt）と再開機能を使用
- **ストリーミング対応**: p31_streaming相当のストリーミング機能を実装
- **構造化**: p30_loggingとp31_streamingの構造に従った実装
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: 日本語ログを追加
- **4段階処理**: テーマ取得→投稿作成→承認→最終投稿生成

## テスト

### 基本的な動作確認

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

# テストケース
test_theme = "新しいプログラミング言語の学習について"

result = graph.invoke({
    "messages": [HumanMessage(content=test_theme)]
})

print("=" * 60)
print("テーマ:", result.get("theme"))
print("下書き:", result.get("draft_post"))
print("承認状態:", result.get("approved"))
if result.get("final_post"):
    print("最終投稿:", result.get("final_post"))
print("=" * 60)
```

### ストリーミングテスト

```bash
cd /root/LearnLangGraph/archives/ex99_sns_post_editor
python tests/test_stream.py
```

ストリーミングテストでは、各ノードの実行状況をリアルタイムで確認できます。
注意: 中断（interrupt）機能を使用するため、完全なストリーミングテストはLangGraph Studioで実行することを推奨します。

## 注意事項

- このエージェントは中断（interrupt）機能を使用するため、LangGraph StudioやLangSmith Studioで実行することを推奨します
- 中断時にユーザーが承認/拒否を選択する必要があります
- 承認されなかった場合、最終投稿は生成されません


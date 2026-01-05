# ex04_calculator - 計算機ツールエージェント

このプロジェクトは、p31_streaming相当のロギングとストリーミングを実装した計算機ツールエージェントです。
LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
ex04_calculator/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
│   │   ├── tools.py       # ツール定義（add, mul, sub, div）
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（ログ付き）
├── tests/                # テストファイル（オプション）
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## 機能

このエージェントは、以下の処理を行います：

1. **リクエストに対処するノード（LLM_steps）**: ユーザーリクエストをmodel_with_toolsへ渡します
2. **ツール実行ノード（Action steps）**: 指定のツールを実行します（複数指定された場合は全部実行）
3. **回答整形ノード（LLM steps）**: ツール（あるいはLLM）の回答を整形して、ユーザーへのリザルトに追加します

### 利用可能なツール

- **add(a, b)**: a + b した値を返す
- **mul(a, b)**: a * b した値を返す
- **sub(a, b)**: a - b した値を返す
- **div(a, b)**: a / b した値を返す

## グラフ構造

```
start
  ↓
リクエストに対処するノード（LLM_steps）
  ↓
  ├─ ツール呼び出しあり → ツール実行ノード（Action steps）
  │                        ↓
  └─ ツール呼び出しなし → 回答整形ノード（LLM_format_steps）
                          ↓
                        end
```

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
cd /root/LearnLangGraph/archives/ex04_calculator
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

# 計算リクエスト
result = graph.invoke({
    "messages": [HumanMessage(content="5 + 3 を計算してください")]
})

print(result["messages"][-1].content)
```

### ストリーミング使用例

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

# ストリーミングで実行
for chunk in graph.stream({
    "messages": [HumanMessage(content="10 * 7 を計算してください")]
}, stream_mode="updates"):
    print(chunk)
```

## ロギング機能

このエージェントは、p30_loggingとp31_streamingを参考にした日本語ログを出力します。

### ログレベル

環境変数 `LOG_LEVEL` で設定可能：
- `DEBUG`: 詳細なデバッグ情報
- `INFO`: 一般的な情報（デフォルト）
- `WARNING`: 警告メッセージ
- `ERROR`: エラーメッセージ

### ログの種類

- **🤖 [LLM_STEPS]**: リクエストに対処するノードのログ
- **🔧 [ACTION_STEPS]**: ツール実行ノードのログ
- **📝 [LLM_FORMAT_STEPS]**: 回答整形ノードのログ
- **🔀 [ROUTING]**: ルーティング判定のログ
- **🔢 [TOOL]**: ツール実行のログ
- **エラー**: エラー発生時の詳細情報

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `ex04_calculator.log` ファイルを確認
3. **エラーログ**: `ex04_calculator_error.log` ファイルでエラーのみを確認

## 特徴

- **構造化**: p30_loggingとp31_streamingの構造に従った実装
- **ストリーミング対応**: LangGraphの標準ストリーミング機能を使用
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: 日本語ログを追加
- **ツール使用**: add, mul, sub, divの4つの計算ツールを実装

## テスト

基本的な動作確認：

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

# テストケース1: 加算
result1 = graph.invoke({
    "messages": [HumanMessage(content="5 + 3 を計算してください")]
})
print("加算結果:", result1["messages"][-1].content)

# テストケース2: 乗算
result2 = graph.invoke({
    "messages": [HumanMessage(content="10 * 7 を計算してください")]
})
print("乗算結果:", result2["messages"][-1].content)

# テストケース3: 減算
result3 = graph.invoke({
    "messages": [HumanMessage(content="20 - 8 を計算してください")]
})
print("減算結果:", result3["messages"][-1].content)

# テストケース4: 除算
result4 = graph.invoke({
    "messages": [HumanMessage(content="15 / 3 を計算してください")]
})
print("除算結果:", result4["messages"][-1].content)
```


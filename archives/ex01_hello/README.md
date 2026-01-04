# ex01_hello - 挨拶エージェント

このプロジェクトは、入力された言語（日本語/英語）を判定し、適切な言語で挨拶を返すLangGraphエージェントです。
基本的な Conditional Edge の練習として実装されています。
Vercel AI SDKのチャットから呼び出せるストリーミング対応で、LangGraph Studio（`langgraph dev`）で使用できます。

## 構造

```
ex01_hello/
├── my_agent/              # プロジェクトコード
│   ├── utils/             # グラフ用のユーティリティ
│   │   ├── __init__.py
│   │   ├── state.py       # グラフの状態定義
│   │   ├── nodes.py       # グラフ用のノード関数（ログ付き）
│   │   └── logging_config.py  # ロギング設定
│   ├── __init__.py
│   └── agent.py          # グラフを構築するコード（ログ付き）
├── tests/                # テストファイル
│   ├── __init__.py
│   └── test_invoke.py    # invokeのテスト
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## 機能

このエージェントは、以下の処理を行います：

1. **言語判定**: メッセージから言語（日本語/英語/終了）を判定します
2. **条件分岐**: 判定された言語に基づいて、適切な挨拶ノードにルーティングします
3. **挨拶生成**: 日本語または英語で挨拶を生成します

## グラフ構造

```
start
  ↓
言語を判定するLLMノード
  ↓ (条件エッジ)
  ├─ japanese → 日本語で挨拶を返すLLMノード → end
  ├─ english → 英語で挨拶を返すLLMノード → end
  └─ quit → end
```

### 状態

- `messages`: `Annotated[list[AnyMessage], operator.add]` - メッセージのリスト
- `language`: `Optional[Literal["japanese", "english", "quit"]]` - 判定された言語

### ノード

1. **detect_language**: 言語を判定するLLMノード
   - LLMに英語か日本語か、それとも終了を表すかを判定してもらう
   - メッセージと判定結果で、状態を更新する

2. **greet_in_english**: 英語で挨拶を返すLLMノード
   - LLMに英語で、最新メッセージに返す挨拶を作成してもらい、messages へ追加する

3. **greet_in_japanese**: 日本語で挨拶を返すLLMノード
   - LLMに日本語で、最新メッセージに返す挨拶を作成してもらい、messages へ追加する

### エッジ

- `start` → `detect_language`
- `detect_language` → 条件エッジ（`route_by_language`関数）
  - `japanese` → `greet_in_japanese`
  - `english` → `greet_in_english`
  - `quit` → `end`
- `greet_in_english` → `end`
- `greet_in_japanese` → `end`

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
cd /root/LearnLangGraph/archives/ex01_hello
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`

## テスト

### invokeのテスト

```bash
cd /root/LearnLangGraph/archives/ex01_hello
python tests/test_invoke.py
```

または、pytestを使用：

```bash
pytest tests/test_invoke.py -v
```

## ロギング

このプロジェクトは、p31_streamingのロギング実装を参考にした日本語ログを出力します。

### ログファイル

- `ex01_hello.log`: すべてのログ
- `ex01_hello_error.log`: エラーログのみ

### ログレベル

環境変数 `LOG_LEVEL` で設定可能（デフォルト: `INFO`）

### ログの確認方法

1. **コンソール出力**: 実行時にコンソールにログが表示されます
2. **ログファイル**: `ex01_hello.log` ファイルを確認
3. **エラーログ**: `ex01_hello_error.log` ファイルでエラーのみを確認

## 使用例

### 日本語メッセージ

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

result = graph.invoke({
    "messages": [HumanMessage(content="こんにちは")],
    "language": None
})

print(result["messages"][-1].content)  # 日本語での挨拶が表示される
```

### 英語メッセージ

```python
from langchain.messages import HumanMessage
from my_agent.agent import graph

result = graph.invoke({
    "messages": [HumanMessage(content="Hello")],
    "language": None
})

print(result["messages"][-1].content)  # 英語での挨拶が表示される
```

## 構成の参考

このプロジェクトは、以下の構成に従って実装されています：
- **構造**: p31_streamingの構造に従った実装
- **ストリーミング対応**: Vercel AI SDKのチャットから呼び出し可能
- **Studio対応**: `langgraph dev`で使用可能
- **ロギング機能**: p30_loggingを参考にした日本語ログを追加
- **テスト**: invokeの動作を確認するテストを含む


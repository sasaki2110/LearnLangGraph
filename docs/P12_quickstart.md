# LangGraph クイックスタート解説

## 概要

このドキュメントは、LangGraphのクイックスタート（`p12_quickstart.py`）の詳細な解説です。  
公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/quickstart

このサンプルでは、**Graph API**を使用して計算エージェントを構築します。エージェントは加算、乗算、除算のツールを使用して、ユーザーの質問に答えることができます。

## 実行方法

### 前提条件

1. 仮想環境が有効化されていること
2. 依存関係がインストールされていること（`pip install -r requirements.txt`）
3. Claude APIキーが環境変数に設定されていること

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### 実行コマンド

```bash
python p12_quickstart.py
```

## アーキテクチャの概要

このエージェントは以下のようなフローで動作します：

```
START → llm_call → [ツール呼び出しあり？] → tool_node → llm_call → END
                      ↓
                    [ツール呼び出しなし]
                      ↓
                     END
```

1. **START**: エージェントの開始
2. **llm_call**: LLMがユーザーの質問を分析し、ツールを呼び出すかどうかを決定
3. **should_continue**: 条件分岐ロジック
   - ツール呼び出しあり → `tool_node`へ
   - ツール呼び出しなし → `END`へ
4. **tool_node**: ツールを実行し、結果を返す
5. **llm_call**: ツールの結果を受け取り、最終的な回答を生成
6. **END**: エージェントの終了

## コードの詳細解説

### 1. ツールとモデルの定義

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "claude-sonnet-4-5-20250929",
    temperature=0
)
```

- **`init_chat_model`**: Claude Sonnet 4.5モデルを初期化
- **`temperature=0`**: 一貫性のある出力のため、ランダム性を最小化

#### ツールの定義

```python
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`."""
    return a * b
```

- **`@tool`デコレータ**: 関数をLangChainのツールとして登録
- ツールの説明文（docstring）は、LLMがツールを選択する際の重要な情報となります

#### ツールのバインド

```python
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)
```

- **`bind_tools`**: LLMにツールをバインドし、LLMがツールを呼び出せるようにする
- **`tools_by_name`**: ツール名からツールオブジェクトを取得するための辞書

### 2. 状態の定義

```python
from typing_extensions import TypedDict, Annotated
import operator

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
```

- **`MessagesState`**: エージェントの状態を定義するTypedDict
- **`messages`**: メッセージのリスト
  - `Annotated[list[AnyMessage], operator.add]`: 新しいメッセージが既存のリストに**追加**されることを示す
  - これにより、メッセージ履歴が保持されます
- **`llm_calls`**: LLMの呼び出し回数をカウント

**重要**: `operator.add`を使用することで、状態の更新時にメッセージが置き換えられるのではなく、追加されることが保証されます。

### 3. モデルノードの定義

```python
def llm_call(state: dict):
    """LLMがツールを呼び出すかどうかを決定します。"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant..."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }
```

- **`llm_call`**: LLMを呼び出すノード関数
- **`SystemMessage`**: エージェントの役割を定義するシステムメッセージ
- **`state["messages"]`**: これまでの会話履歴を含む
- **`model_with_tools.invoke`**: ツールがバインドされたモデルを呼び出し
  - LLMは、必要に応じてツールを呼び出すか、直接回答を返すかを決定します
- **`llm_calls`**: 呼び出し回数をインクリメント

### 4. ツールノードの定義

```python
def tool_node(state: dict):
    """ツール呼び出しを実行します。"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}
```

- **`tool_node`**: ツールを実行するノード関数
- **`state["messages"][-1].tool_calls`**: 最後のメッセージからツール呼び出しを取得
- **`tool.invoke(tool_call["args"])`**: ツールを実行
- **`ToolMessage`**: ツールの実行結果をメッセージとして返す
  - `tool_call_id`: どのツール呼び出しに対する結果かを識別

### 5. 終了ロジックの定義

```python
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """LLMがツールを呼び出したかどうかを確認します。"""
    messages = state["messages"]
    last_message = messages[-1]
    
    if last_message.tool_calls:
        return "tool_node"
    return END
```

- **`should_continue`**: 条件付きエッジ関数
- **`last_message.tool_calls`**: 最後のメッセージにツール呼び出しが含まれているかチェック
- ツール呼び出しあり → `"tool_node"`にルーティング
- ツール呼び出しなし → `END`にルーティング（エージェント終了）

### 6. エージェントの構築とコンパイル

```python
from langgraph.graph import StateGraph, START, END

agent_builder = StateGraph(MessagesState)

# ノードの追加
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# エッジの追加
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

agent = agent_builder.compile()
```

#### グラフの構築手順

1. **`StateGraph(MessagesState)`**: 状態グラフを作成
2. **`add_node`**: ノードを追加
   - `"llm_call"`: LLM呼び出しノード
   - `"tool_node"`: ツール実行ノード
3. **`add_edge(START, "llm_call")`**: 開始からLLM呼び出しノードへ
4. **`add_conditional_edges`**: 条件付きエッジ
   - `"llm_call"`から`should_continue`関数の結果に基づいて分岐
   - 可能な遷移先: `["tool_node", END]`
5. **`add_edge("tool_node", "llm_call")`**: ツール実行後、再度LLM呼び出しへ
6. **`compile()`**: グラフをコンパイルして実行可能なエージェントを作成

#### グラフの構造

```
START
  ↓
llm_call ──[ツール呼び出しあり]──→ tool_node ──→ llm_call
  │                                        ↑         │
  │                                        │         │
  └──[ツール呼び出しなし]───────────────┘         │
                                                    │
  ──────────────────────────────────────────────────┘
  (最終回答が生成されたらEND)
```

### 7. エージェントの実行

```python
messages = [HumanMessage(content="Add 3 and 4.")]
result = agent.invoke({"messages": messages, "llm_calls": 0})
```

- **`HumanMessage`**: ユーザーの入力メッセージ
- **`agent.invoke`**: エージェントを実行
  - 入力: 初期状態（メッセージとLLM呼び出し回数）
  - 出力: 最終状態（すべてのメッセージとLLM呼び出し回数）

## 実行フローの例

### 例: "Add 3 and 4." の処理

1. **START → llm_call**
   - 入力: `[HumanMessage("Add 3 and 4.")]`
   - LLMが分析し、`add`ツールを呼び出すことを決定
   - 出力: `AIMessage(tool_calls=[{"name": "add", "args": {"a": 3, "b": 4}}])`

2. **llm_call → tool_node** (should_continueが"tool_node"を返す)
   - `add(3, 4)`を実行
   - 出力: `ToolMessage(content="7", tool_call_id="...")`

3. **tool_node → llm_call**
   - ツールの結果を受け取り、最終回答を生成
   - 出力: `AIMessage(content="3 + 4 = 7")`

4. **llm_call → END** (should_continueがENDを返す)
   - ツール呼び出しがないため、エージェント終了

## 重要な概念

### 状態の永続性

LangGraphでは、状態がエージェントの実行中に保持されます。`operator.add`を使用することで、メッセージが追加され、会話履歴が維持されます。

### 条件付きエッジ

`add_conditional_edges`を使用することで、実行時に動的に次のノードを決定できます。これにより、複雑な分岐ロジックを実装できます。

### ツールの統合

LLMにツールをバインドすることで、LLMは必要に応じてツールを呼び出すことができます。これは、LLMの能力を拡張する強力な方法です。

## トラブルシューティング

### エラー: APIキーが見つからない

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### エラー: モジュールが見つからない

依存関係がインストールされているか確認してください：

```bash
pip install -r requirements.txt
```

### 実行が遅い

LLMの呼び出しには時間がかかります。特に初回実行時は、モデルのロードに時間がかかる場合があります。

## 次のステップ

- [Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph): LangGraphの設計思想を学ぶ
- [Functional API](https://docs.langchain.com/oss/python/langgraph/functional-api): 関数型APIを使用した実装方法
- [Streaming](https://docs.langchain.com/oss/python/langgraph/streaming): ストリーミング出力の実装
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence): 状態の永続化

## 参考資料

- [公式クイックスタート](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)


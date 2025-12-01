# Streaming

このドキュメントでは、LangGraphにおけるストリーミング出力の実装方法について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/streaming

## 概要

ストリーミングは、エージェントの実行結果を**リアルタイムで段階的に返す**機能です。これにより、ユーザーは処理の完了を待たずに、結果を順次確認できます。

### ストリーミングの利点

1. **ユーザー体験の向上**: 結果を待たずに確認できる
2. **応答性の向上**: 処理が完了する前に結果を表示できる
3. **進行状況の可視化**: 処理の進行状況を把握できる

## 基本的なストリーミング

### `stream()`メソッドの使用

`invoke()`の代わりに`stream()`を使用することで、ストリーミング出力が可能になります。

```python
from langgraph.graph import StateGraph, START, END

# エージェントの構築（既存のコード）
agent = agent_builder.compile()

# ストリーミング実行
for chunk in agent.stream({"messages": [HumanMessage(content="Add 3 and 4.")], "llm_calls": 0}):
    print(chunk)
```

### ストリーミングの出力形式

`stream()`は、各ノードの実行結果を順次返します。

```python
# 出力例
{
    "llm_call": {
        "messages": [AIMessage(tool_calls=[...])],
        "llm_calls": 1
    }
}
{
    "tool_node": {
        "messages": [ToolMessage(content="7", ...)]
    }
}
{
    "llm_call": {
        "messages": [AIMessage(content="3 + 4 = 7")],
        "llm_calls": 2
    }
}
```

## ストリーミングの種類

### 1. ノードレベルのストリーミング

各ノードの実行結果をストリーミングします。

```python
for chunk in agent.stream(initial_state):
    node_name = list(chunk.keys())[0]
    state_update = chunk[node_name]
    print(f"Node: {node_name}, Update: {state_update}")
```

### 2. LLMレベルのストリーミング

LLMの出力をトークン単位でストリーミングします。

```python
from langchain_core.runnables import RunnableConfig

# LLMレベルのストリーミングを有効化
config = RunnableConfig(stream_mode="values")

for chunk in agent.stream(initial_state, config=config):
    # LLMの出力をトークン単位で取得
    if "messages" in chunk:
        last_message = chunk["messages"][-1]
        if hasattr(last_message, "content"):
            print(last_message.content, end="", flush=True)
```

## 実装例

### 例1: 基本的なストリーミング

```python
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage

# エージェントの構築（P12のコードを参照）
agent = agent_builder.compile()

# ストリーミング実行
print("エージェントの実行開始...\n")

for chunk in agent.stream(
    {"messages": [HumanMessage(content="Add 3 and 4.")], "llm_calls": 0}
):
    node_name = list(chunk.keys())[0]
    state_update = chunk[node_name]
    
    print(f"【{node_name}】実行完了")
    
    if "messages" in state_update:
        last_message = state_update["messages"][-1]
        if hasattr(last_message, "content"):
            print(f"  内容: {last_message.content}")
        elif hasattr(last_message, "tool_calls"):
            print(f"  ツール呼び出し: {[tc['name'] for tc in last_message.tool_calls]}")
    
    print()

print("エージェントの実行完了")
```

### 例2: LLMレベルのストリーミング

```python
from langchain_core.runnables import RunnableConfig

# ストリーミングモードの設定
config = RunnableConfig(
    stream_mode="values",  # 値のストリーミング
    recursion_limit=50     # 再帰制限
)

print("エージェントの実行開始（LLMストリーミング）...\n")

for chunk in agent.stream(
    {"messages": [HumanMessage(content="Add 3 and 4.")], "llm_calls": 0},
    config=config
):
    # メッセージの更新を確認
    if "messages" in chunk:
        messages = chunk["messages"]
        if messages:
            last_message = messages[-1]
            
            # AIMessageの内容をストリーミング
            if hasattr(last_message, "content") and last_message.content:
                print(last_message.content, end="", flush=True)
            
            # ツール呼び出しの表示
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                print(f"\n[ツール呼び出し: {[tc['name'] for tc in last_message.tool_calls]}]")

print("\n\nエージェントの実行完了")
```

### 例3: カスタムストリーミングハンドラー

```python
class StreamingHandler:
    """カスタムストリーミングハンドラー"""
    
    def __init__(self):
        self.node_count = 0
        self.total_llm_calls = 0
    
    def handle_chunk(self, chunk: dict):
        """チャンクを処理"""
        node_name = list(chunk.keys())[0]
        state_update = chunk[node_name]
        
        self.node_count += 1
        print(f"[{self.node_count}] {node_name} 実行")
        
        if "llm_calls" in state_update:
            self.total_llm_calls = state_update["llm_calls"]
            print(f"  LLM呼び出し回数: {self.total_llm_calls}")
        
        if "messages" in state_update:
            messages = state_update["messages"]
            if messages:
                last_message = messages[-1]
                self._display_message(last_message)
    
    def _display_message(self, message):
        """メッセージを表示"""
        if hasattr(message, "content") and message.content:
            print(f"  → {message.content}")
        elif hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                print(f"  → ツール: {tc['name']}({tc['args']})")

# 使用例
handler = StreamingHandler()

for chunk in agent.stream(
    {"messages": [HumanMessage(content="Add 3 and 4.")], "llm_calls": 0}
):
    handler.handle_chunk(chunk)

print(f"\n総ノード実行数: {handler.node_count}")
print(f"総LLM呼び出し回数: {handler.total_llm_calls}")
```

## ストリーミングモード

### `stream_mode`のオプション

`RunnableConfig`の`stream_mode`には、以下のオプションがあります：

1. **`"values"`**: 各ノードの状態更新をストリーミング
2. **`"updates"`**: 状態の差分のみをストリーミング
3. **`"messages"`**: メッセージのみをストリーミング

```python
# 値のストリーミング（推奨）
config = RunnableConfig(stream_mode="values")

# 更新のストリーミング
config = RunnableConfig(stream_mode="updates")

# メッセージのストリーミング
config = RunnableConfig(stream_mode="messages")
```

## ストリーミングのベストプラクティス

### 1. 適切なストリーミングモードの選択

用途に応じて適切なストリーミングモードを選択します：

- **ユーザー向け**: `"values"`で全体の進行状況を表示
- **デバッグ**: `"updates"`で状態の変化を確認
- **チャットUI**: `"messages"`でメッセージのみを表示

### 2. エラーハンドリング

ストリーミング中にエラーが発生する可能性があるため、適切にエラーハンドリングします。

```python
try:
    for chunk in agent.stream(initial_state):
        # チャンクの処理
        process_chunk(chunk)
except Exception as e:
    print(f"エラーが発生しました: {e}")
    # エラー処理
```

### 3. パフォーマンスの考慮

ストリーミングはオーバーヘッドが発生するため、必要な場合のみ使用します：

- **短い処理**: ストリーミング不要
- **長い処理**: ストリーミング推奨
- **ユーザー体験**: リアルタイム表示が必要な場合に使用

## ストリーミングと`invoke()`の比較

| 特徴 | `invoke()` | `stream()` |
|------|-----------|-----------|
| **戻り値** | 最終状態のみ | 各ノードの状態更新 |
| **待機時間** | 処理完了まで待機 | リアルタイムで結果を返す |
| **ユーザー体験** | 結果を待つ必要がある | 進行状況を確認できる |
| **パフォーマンス** | オーバーヘッドが少ない | オーバーヘッドがある |
| **用途** | バッチ処理、テスト | インタラクティブなアプリケーション |

## 実践的な使用例

### Webアプリケーションでのストリーミング

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """チャットのストリーミングエンドポイント"""
    
    def generate():
        initial_state = {
            "messages": [HumanMessage(content=request.message)],
            "llm_calls": 0
        }
        
        for chunk in agent.stream(initial_state):
            # JSON形式でストリーミング
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## まとめ

ストリーミングにより、以下のことが可能になります：

1. **リアルタイムでの結果表示**: 処理の完了を待たずに結果を確認
2. **ユーザー体験の向上**: 進行状況を可視化
3. **インタラクティブなアプリケーション**: チャットUIなどでの活用

適切にストリーミングを実装することで、より良いユーザー体験を提供できます。

## 次のステップ

- [P16: Persistence](./P16_persistence.md): 状態の永続化
- [P17: Functional API](./P17_functional_api.md): 関数型APIの使用方法
- [P18: Interrupts](./P18_interrupts.md): 人間の介入（Human-in-the-loop）


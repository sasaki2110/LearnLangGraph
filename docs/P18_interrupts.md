# Interrupts

このドキュメントでは、LangGraphにおける中断（Interrupts）と人間の介入（Human-in-the-loop）について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/interrupts

## 概要

中断（Interrupts）は、エージェントの実行を**一時的に停止**し、**人間の介入**を可能にする機能です。これにより、以下のことが可能になります：

1. **承認フロー**: 重要な操作の前に人間の承認を求める
2. **入力の要求**: 実行中にユーザーからの追加情報を要求
3. **エラーの処理**: エラー発生時に人間の判断を求める
4. **デバッグ**: 実行中の状態を確認し、必要に応じて修正

## 中断の基本概念

### 中断ポイント（Interrupt Point）

**中断ポイント**は、エージェントの実行が一時停止される場所です。

- 特定のノードの実行前後に設定できる
- 人間の介入を待つ
- 介入後、実行を再開できる

### 中断の種類

1. **事前中断**: ノードの実行前に中断
2. **事後中断**: ノードの実行後に中断
3. **条件付き中断**: 特定の条件で中断

## 基本的な使用方法

### 中断の設定

`interrupt_before`または`interrupt_after`を使用して、中断ポイントを設定します。

```python
from langgraph.graph import StateGraph, START, END

# グラフの構築
graph = StateGraph(MessagesState)
graph.add_node("llm_call", llm_call)
graph.add_node("tool_node", tool_node)
graph.add_node("approval_node", approval_node)

# 中断の設定
graph.add_edge(START, "llm_call")
graph.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
graph.add_edge("tool_node", "approval_node")  # 承認ノード
graph.add_edge("approval_node", "llm_call")

# 承認ノードの前に中断を設定
agent = graph.compile(interrupt_before=["approval_node"])
```

### 中断後の再開

中断後、`update_state`を使用して状態を更新し、実行を再開します。

```python
from langgraph.graph import StateGraph

# エージェントの実行（中断される）
config = {"configurable": {"thread_id": "thread-1"}}
result = agent.invoke(
    {"messages": [HumanMessage(content="Delete all files")]},
    config=config
)

# 中断された状態を確認
state = agent.get_state(config)
print(f"中断されたノード: {state.next}")

# 人間の承認
approval = input("承認しますか？ (y/n): ")

if approval == "y":
    # 状態を更新して再開
    agent.update_state(
        config,
        {"approved": True}
    )
    # 実行を再開
    result = agent.invoke(None, config=config)
else:
    # キャンセル
    agent.update_state(
        config,
        {"approved": False, "cancelled": True}
    )
```

## 実装例

### 例1: 基本的な承認フロー

```python
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage

class ApprovalState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    approved: bool
    cancelled: bool

def llm_call(state: ApprovalState) -> dict:
    """LLM呼び出し"""
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

def approval_node(state: ApprovalState) -> dict:
    """承認ノード（中断される）"""
    # このノードの実行前に中断される
    return {"approved": True}

def tool_node(state: ApprovalState) -> dict:
    """ツール実行（承認後）"""
    if not state.get("approved", False):
        return {"cancelled": True}
    
    # ツールを実行
    result = execute_tool(state)
    return {"messages": [ToolMessage(content=result)]}

# グラフの構築
graph = StateGraph(ApprovalState)
graph.add_node("llm_call", llm_call)
graph.add_node("approval_node", approval_node)
graph.add_node("tool_node", tool_node)

graph.add_edge(START, "llm_call")
graph.add_edge("llm_call", "approval_node")
graph.add_edge("approval_node", "tool_node")
graph.add_edge("tool_node", END)

# 承認ノードの前に中断を設定
agent = graph.compile(interrupt_before=["approval_node"])

# 実行（中断される）
config = {"configurable": {"thread_id": "thread-1"}}
result = agent.invoke(
    {"messages": [HumanMessage(content="Delete file.txt")], "approved": False, "cancelled": False},
    config=config
)

# 中断された状態を確認
state = agent.get_state(config)
print(f"中断されたノード: {state.next}")

# 人間の承認を待つ
approval = input("ファイルを削除しますか？ (y/n): ")

if approval.lower() == "y":
    # 承認して再開
    agent.update_state(config, {"approved": True})
    result = agent.invoke(None, config=config)
    print("ファイルが削除されました")
else:
    # キャンセル
    agent.update_state(config, {"approved": False, "cancelled": True})
    print("操作がキャンセルされました")
```

### 例2: 条件付き中断

```python
def should_interrupt(state: ApprovalState) -> bool:
    """中断すべきかどうかを判定"""
    last_message = state["messages"][-1]
    
    # 危険な操作が含まれている場合
    dangerous_keywords = ["delete", "remove", "drop", "truncate"]
    if any(keyword in last_message.content.lower() for keyword in dangerous_keywords):
        return True
    
    return False

# 条件付き中断の設定
def conditional_interrupt(state: ApprovalState):
    """条件付き中断関数"""
    if should_interrupt(state):
        return "approval_node"  # 承認ノードで中断
    return "tool_node"  # 通常の処理

graph.add_conditional_edges(
    "llm_call",
    conditional_interrupt,
    ["approval_node", "tool_node"]
)
```

### 例3: ユーザー入力の要求

```python
def input_request_node(state: ApprovalState) -> dict:
    """ユーザー入力要求ノード（中断される）"""
    # このノードで中断し、ユーザーからの入力を待つ
    return {"waiting_for_input": True}

def process_with_input(state: ApprovalState) -> dict:
    """ユーザー入力を受け取って処理"""
    user_input = state.get("user_input", "")
    # ユーザー入力を使用して処理
    result = process(state, user_input)
    return {"messages": [AIMessage(content=result)]}

# グラフの構築
graph = StateGraph(ApprovalState)
graph.add_node("llm_call", llm_call)
graph.add_node("input_request_node", input_request_node)
graph.add_node("process_with_input", process_with_input)

graph.add_edge(START, "llm_call")
graph.add_edge("llm_call", "input_request_node")
graph.add_edge("input_request_node", "process_with_input")
graph.add_edge("process_with_input", END)

# 入力要求ノードの後に中断を設定
agent = graph.compile(interrupt_after=["input_request_node"])

# 実行（中断される）
config = {"configurable": {"thread_id": "thread-1"}
result = agent.invoke(
    {"messages": [HumanMessage(content="What is your name?")]},
    config=config
)

# 中断された状態を確認
state = agent.get_state(config)
print("ユーザー入力が必要です")

# ユーザーからの入力を取得
user_input = input("名前を入力してください: ")

# 状態を更新して再開
agent.update_state(config, {"user_input": user_input})
result = agent.invoke(None, config=config)
```

## 中断のベストプラクティス

### 1. 適切な中断ポイントの選択

中断ポイントは、以下のような場合に設定します：

- **重要な操作の前**: データの削除、変更など
- **外部システムへのアクセス**: API呼び出し、データベース操作など
- **コストが高い操作**: 高額なAPI呼び出しなど
- **不確実な操作**: LLMの判断が不確実な場合

### 2. 明確なメッセージの提供

中断時には、ユーザーに明確なメッセージを提供します。

```python
def approval_node(state: ApprovalState) -> dict:
    """承認ノード"""
    last_message = state["messages"][-1]
    
    # 明確なメッセージを生成
    message = f"""
    以下の操作を実行しようとしています:
    {last_message.content}
    
    この操作を承認しますか？
    """
    
    print(message)
    return {"waiting_for_approval": True}
```

### 3. タイムアウトの設定

長時間待機する場合は、タイムアウトを設定します。

```python
import time

def wait_for_approval(config, timeout=300):
    """承認を待つ（タイムアウト付き）"""
    start_time = time.time()
    
    while True:
        state = agent.get_state(config)
        
        if state.values.get("approved") is not None:
            return state.values["approved"]
        
        if time.time() - start_time > timeout:
            # タイムアウト
            agent.update_state(config, {"approved": False, "timeout": True})
            return False
        
        time.sleep(1)  # 1秒待機
```

### 4. エラーハンドリング

中断中のエラーを適切に処理します。

```python
try:
    result = agent.invoke(initial_state, config=config)
except InterruptedError:
    # 中断された場合
    state = agent.get_state(config)
    # 中断処理
    handle_interrupt(state)
except Exception as e:
    # その他のエラー
    print(f"エラーが発生しました: {e}")
```

## 中断と永続化の組み合わせ

中断は、永続化と組み合わせることで、より強力になります。

```python
from langgraph.checkpoint.memory import MemorySaver

# 永続化の設定
memory = MemorySaver()

# 中断付きエージェントの構築
agent = graph.compile(
    checkpointer=memory,
    interrupt_before=["approval_node"]
)

# 実行（中断される）
config = {"configurable": {"thread_id": "thread-1"}}
result = agent.invoke(initial_state, config=config)

# 状態は永続化されているため、後で再開可能
# （サーバー再起動後も可能）
state = agent.get_state(config)
if state.next:  # 中断されている場合
    # 承認して再開
    agent.update_state(config, {"approved": True})
    result = agent.invoke(None, config=config)
```

## まとめ

中断（Interrupts）により、以下のことが可能になります：

1. **承認フロー**: 重要な操作の前に人間の承認を求める
2. **入力の要求**: 実行中にユーザーからの追加情報を要求
3. **エラーの処理**: エラー発生時に人間の判断を求める
4. **デバッグ**: 実行中の状態を確認し、必要に応じて修正

適切に中断を実装することで、より安全で制御可能なエージェントシステムを構築できます。

## 次のステップ

- [P19: Subgraphs](./P19_subgraphs.md): サブグラフの概念
- [P20: Memory](./P20_memory.md): メモリ管理
- [P21: Durable Execution](./P21_durable_execution.md): 長時間実行の管理


# Durable Execution

このドキュメントでは、LangGraphにおける耐久性のある実行（Durable Execution）について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/durable-execution

## 概要

耐久性のある実行（Durable Execution）は、エージェントが**長時間実行され、エラーから復旧できる**ようにする機能です。これにより、以下のことが可能になります：

1. **エラーからの復旧**: エラー発生時に状態を復元して再開
2. **長時間実行**: 数時間や数日にわたる実行が可能
3. **チェックポイント**: 定期的に状態を保存
4. **再開機能**: 任意の時点から実行を再開

## 耐久性のある実行の基本概念

### チェックポイント

**チェックポイント**は、エージェントの状態のスナップショットです。

- 各ノードの実行後に自動的に作成される
- 状態の完全なコピーが保存される
- 任意のチェックポイントから実行を再開できる

### 再開機能

**再開機能**は、エラー発生時や中断時に、最後のチェックポイントから実行を再開します。

- 状態が自動的に復元される
- エラーが発生したノードから再実行される
- ユーザーの介入なしに自動的に復旧

## 基本的な使用方法

### 永続化の設定

耐久性のある実行には、**永続化（Persistence）**が必要です。

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 永続化の設定
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# エージェントに永続化を設定
agent = graph.compile(checkpointer=checkpointer)
```

### エラーからの自動復旧

永続化が設定されている場合、エラー発生時に自動的に復旧を試みます。

```python
# エージェントの実行
config = {"configurable": {"thread_id": "thread-1"}}

try:
    result = agent.invoke(initial_state, config=config)
except Exception as e:
    # エラーが発生した場合、状態は保存されている
    print(f"エラーが発生しました: {e}")
    
    # 状態を確認
    state = agent.get_state(config)
    print(f"最後のチェックポイント: {state.checkpoint_id}")
    
    # 状態を修正して再実行
    fixed_state = fix_state(state.values)
    result = agent.invoke(fixed_state, config=config)
```

## 実装例

### 例1: 基本的な耐久性のある実行

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END

class DurableState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    step_count: int
    last_error: str

def process_step(state: DurableState) -> dict:
    """処理ステップ（エラーが発生する可能性がある）"""
    try:
        # 処理を実行
        result = perform_operation(state)
        return {
            "messages": [AIMessage(content=result)],
            "step_count": state.get("step_count", 0) + 1,
            "last_error": ""
        }
    except Exception as e:
        # エラーを記録
        return {
            "last_error": str(e),
            "step_count": state.get("step_count", 0)
        }

def error_handler(state: DurableState) -> dict:
    """エラーハンドラー"""
    if state.get("last_error"):
        # エラーを処理
        error_message = f"エラーが発生しました: {state['last_error']}"
        return {
            "messages": [AIMessage(content=error_message)],
            "last_error": ""
        }
    return {}

# グラフの構築
graph = StateGraph(DurableState)
graph.add_node("process_step", process_step)
graph.add_node("error_handler", error_handler)

graph.add_edge(START, "process_step")
graph.add_conditional_edges(
    "process_step",
    lambda s: "error_handler" if s.get("last_error") else END,
    ["error_handler", END]
)
graph.add_edge("error_handler", END)

# 永続化の設定
checkpointer = SqliteSaver.from_conn_string("durable.db")
agent = graph.compile(checkpointer=checkpointer)

# 実行（エラーが発生しても状態は保存される）
config = {"configurable": {"thread_id": "thread-1"}}
result = agent.invoke(
    {"messages": [], "step_count": 0, "last_error": ""},
    config=config
)
```

### 例2: 長時間実行の管理

```python
from langgraph.checkpoint.sqlite import SqliteSaver
import time

class LongRunningState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    current_task: str
    completed_tasks: list
    remaining_tasks: list

def execute_task(state: LongRunningState) -> dict:
    """タスクを実行"""
    if not state.get("remaining_tasks"):
        return {"current_task": "完了"}
    
    # 次のタスクを取得
    current_task = state["remaining_tasks"][0]
    remaining_tasks = state["remaining_tasks"][1:]
    
    # タスクを実行（時間がかかる可能性がある）
    result = perform_long_task(current_task)
    
    return {
        "current_task": current_task,
        "completed_tasks": state.get("completed_tasks", []) + [current_task],
        "remaining_tasks": remaining_tasks,
        "messages": [AIMessage(content=f"タスク '{current_task}' を完了しました")]
    }

def check_completion(state: LongRunningState) -> Literal["continue", END]:
    """完了チェック"""
    if state.get("remaining_tasks"):
        return "continue"
    return END

# グラフの構築
graph = StateGraph(LongRunningState)
graph.add_node("execute_task", execute_task)

graph.add_edge(START, "execute_task")
graph.add_conditional_edges(
    "execute_task",
    check_completion,
    ["execute_task", END]  # ループして継続
)

# 永続化の設定
checkpointer = SqliteSaver.from_conn_string("long_running.db")
agent = graph.compile(checkpointer=checkpointer)

# 長時間実行（途中で中断されても再開可能）
config = {"configurable": {"thread_id": "long-task-1"}}

initial_state = {
    "messages": [],
    "current_task": "",
    "completed_tasks": [],
    "remaining_tasks": ["task1", "task2", "task3", "task4", "task5"]
}

# 実行（各タスクの後にチェックポイントが作成される）
result = agent.invoke(initial_state, config=config)

# 途中で中断された場合、状態を確認して再開
state = agent.get_state(config)
if state.next:  # まだ実行中の場合
    # 再開
    result = agent.invoke(None, config=config)
```

### 例3: エラーからの復旧

```python
from langgraph.checkpoint.sqlite import SqliteSaver

class RecoveryState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    retry_count: int
    max_retries: int
    last_error: str

def risky_operation(state: RecoveryState) -> dict:
    """リスクのある操作（エラーが発生する可能性がある）"""
    try:
        # リスクのある操作を実行
        result = perform_risky_operation(state)
        return {
            "messages": [AIMessage(content=result)],
            "last_error": "",
            "retry_count": 0
        }
    except Exception as e:
        # エラーを記録
        return {
            "last_error": str(e),
            "retry_count": state.get("retry_count", 0) + 1
        }

def retry_logic(state: RecoveryState) -> Literal["retry", "give_up", END]:
    """リトライロジック"""
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if state.get("last_error"):
        if retry_count < max_retries:
            return "retry"
        else:
            return "give_up"
    
    return END

def give_up_handler(state: RecoveryState) -> dict:
    """諦める処理"""
    error_message = f"最大リトライ回数に達しました: {state.get('last_error')}"
    return {
        "messages": [AIMessage(content=error_message)],
        "last_error": ""
    }

# グラフの構築
graph = StateGraph(RecoveryState)
graph.add_node("risky_operation", risky_operation)
graph.add_node("give_up_handler", give_up_handler)

graph.add_edge(START, "risky_operation")
graph.add_conditional_edges(
    "risky_operation",
    retry_logic,
    ["risky_operation", "give_up_handler", END]  # retry, give_up, END
)
graph.add_edge("give_up_handler", END)

# 永続化の設定
checkpointer = SqliteSaver.from_conn_string("recovery.db")
agent = graph.compile(checkpointer=checkpointer)

# 実行（エラーが発生しても自動的にリトライ）
config = {"configurable": {"thread_id": "recovery-1"}}

result = agent.invoke(
    {
        "messages": [],
        "retry_count": 0,
        "max_retries": 3,
        "last_error": ""
    },
    config=config
)
```

## チェックポイントの管理

### チェックポイントの確認

```python
# 状態の確認
state = agent.get_state(config)

# チェックポイントの履歴
history = agent.get_state_history(config)

for checkpoint in history:
    print(f"チェックポイントID: {checkpoint.id}")
    print(f"タイムスタンプ: {checkpoint.ts}")
    print(f"状態: {checkpoint.values}")
```

### 特定のチェックポイントから再開

```python
# 特定のチェックポイントを取得
checkpoint_id = "checkpoint-123"
state = agent.get_state(config, as_of=checkpoint_id)

# その状態から再実行
result = agent.invoke(state.values, config=config)
```

## ベストプラクティス

### 1. 適切なチェックポイント頻度

チェックポイントは、各ノードの実行後に自動的に作成されますが、必要に応じて手動で作成することも可能です。

```python
def important_step(state: State) -> dict:
    """重要なステップ（明示的にチェックポイントを作成）"""
    # 重要な処理
    result = perform_important_operation(state)
    
    # 状態を更新（チェックポイントが自動的に作成される）
    return {"result": result}
```

### 2. エラーハンドリング

各ノードで適切にエラーを処理し、状態に記録します。

```python
def robust_node(state: State) -> dict:
    """堅牢なノード（エラーハンドリング付き）"""
    try:
        result = perform_operation(state)
        return {"result": result, "error": None}
    except Exception as e:
        # エラーを記録して続行
        return {"error": str(e), "result": None}
```

### 3. 状態の検証

実行前に状態を検証し、整合性を保ちます。

```python
def validate_state(state: State) -> bool:
    """状態の検証"""
    # 必要なフィールドが存在するか確認
    required_fields = ["messages", "step_count"]
    return all(field in state for field in required_fields)

def validated_node(state: State) -> dict:
    """検証済みノード"""
    if not validate_state(state):
        raise ValueError("状態が無効です")
    
    # 処理を実行
    return process(state)
```

## まとめ

耐久性のある実行により、以下のことが可能になります：

1. **エラーからの復旧**: エラー発生時に状態を復元して再開
2. **長時間実行**: 数時間や数日にわたる実行が可能
3. **チェックポイント**: 定期的に状態を保存
4. **再開機能**: 任意の時点から実行を再開

適切に耐久性のある実行を実装することで、より堅牢で信頼性の高いエージェントシステムを構築できます。

## 次のステップ

- [P16: Persistence](./P16_persistence.md): 状態の永続化の詳細
- [P18: Interrupts](./P18_interrupts.md): 人間の介入（Human-in-the-loop）
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る


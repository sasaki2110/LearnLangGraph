# Time Travel

このドキュメントでは、LangGraphにおけるタイムトラベル（Time Travel）機能について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/use-time-travel

## 概要

タイムトラベル（Time Travel）は、**過去のチェックポイントに戻って実行を再開する**機能です。LLMベースのエージェントのような非決定論的なシステムでは、意思決定プロセスを詳細に検証することが重要です。タイムトラベルにより、以下のことが可能になります：

1. **推論の理解**: 成功した結果に至ったステップを分析
2. **エラーのデバッグ**: エラーが発生した場所と理由を特定
3. **代替案の探索**: 異なるパスを試して、より良い解決策を見つける

タイムトラベルを使用すると、過去のチェックポイントから実行を再開できます。同じ状態を再現するか、状態を変更して代替案を探索することも可能です。いずれの場合も、過去の実行から再開すると、履歴に新しいフォーク（分岐）が作成されます。

## タイムトラベルの基本概念

### チェックポイントからの再開

タイムトラベルの核心は、**任意のチェックポイントから実行を再開できる**ことです。

- 過去のチェックポイントを特定
- その時点の状態を取得
- 必要に応じて状態を変更
- そのチェックポイントから実行を再開

### フォーク（分岐）

過去のチェックポイントから実行を再開すると、**新しいフォーク**が作成されます。

- 元の実行履歴は保持される
- 新しい実行は別のパスとして記録される
- 複数の代替案を並行して探索可能

## 使用方法

タイムトラベルを使用するには、以下の4つのステップを実行します：

### 1. グラフを実行する

初期入力を使用して、`invoke`または`stream`メソッドでグラフを実行します。

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver

# グラフの構築とコンパイル
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# グラフの実行
config = {"configurable": {"thread_id": "thread-1"}}
result = graph.invoke(initial_state, config=config)
```

### 2. チェックポイントを特定する

既存のスレッド内のチェックポイントを特定します。`get_state_history`メソッドを使用して、特定の`thread_id`の実行履歴を取得し、目的の`checkpoint_id`を見つけます。

```python
# 実行履歴を取得（時系列の逆順で返される）
states = list(graph.get_state_history(config))

# 各チェックポイントを確認
for state in states:
    print(f"Next: {state.next}")
    print(f"Checkpoint ID: {state.config['configurable']['checkpoint_id']}")
    print(f"Values: {state.values}")
    print()
```

または、[中断（Interrupts）](./P18_interrupts.md)を使用して、特定のノードの前に実行を一時停止し、その時点の最新のチェックポイントを見つけることもできます。

### 3. 状態を更新する（オプション）

`update_state`メソッドを使用して、チェックポイント時点のグラフの状態を変更し、代替状態から実行を再開できます。

```python
# 特定のチェックポイントの状態を取得
selected_state = states[1]  # 例：2番目のチェックポイント

# 状態を更新（新しいチェックポイントが作成される）
new_config = graph.update_state(
    selected_state.config,
    values={"topic": "chickens"}  # 状態を変更
)

print(new_config)
# {'configurable': {'thread_id': '...', 'checkpoint_id': '...'}}
```

`update_state`は新しいチェックポイントを作成します。この新しいチェックポイントは同じスレッドに関連付けられますが、新しいチェックポイントIDが割り当てられます。

### 4. チェックポイントから実行を再開する

`invoke`または`stream`メソッドを使用し、入力として`None`を渡し、適切な`thread_id`と`checkpoint_id`を含む設定を指定して、チェックポイントから実行を再開します。

```python
# チェックポイントから実行を再開
result = graph.invoke(None, new_config)

# または、状態を変更せずに再実行
original_config = {
    "configurable": {
        "thread_id": "thread-1",
        "checkpoint_id": "checkpoint-id-here"
    }
}
result = graph.invoke(None, original_config)
```

## 実装例

### 例1: 基本的なタイムトラベル

以下は、ジョーク生成ワークフローでのタイムトラベルの使用例です。

```python
import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

# 状態の定義
class State(TypedDict):
    topic: NotRequired[str]
    joke: NotRequired[str]

# LLMの初期化
model = init_chat_model("claude-sonnet-4-5-20250929", temperature=0)

def generate_topic(state: State):
    """ジョークのトピックを生成"""
    msg = model.invoke("Give me a funny topic for a joke")
    return {"topic": msg.content}

def write_joke(state: State):
    """トピックに基づいてジョークを書く"""
    msg = model.invoke(f"Write a short joke about {state['topic']}")
    return {"joke": msg.content}

# ワークフローの構築
workflow = StateGraph(State)
workflow.add_node("generate_topic", generate_topic)
workflow.add_node("write_joke", write_joke)
workflow.add_edge(START, "generate_topic")
workflow.add_edge("generate_topic", "write_joke")
workflow.add_edge("write_joke", END)

# コンパイル
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

# 1. グラフを実行
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
state = graph.invoke({}, config)

print("Topic:", state["topic"])
print("Joke:", state["joke"])

# 2. チェックポイントを特定
states = list(graph.get_state_history(config))
print("\n実行履歴:")
for i, state in enumerate(states):
    print(f"Checkpoint {i}:")
    print(f"  Next: {state.next}")
    print(f"  Checkpoint ID: {state.config['configurable']['checkpoint_id']}")
    print(f"  Values: {state.values}")
    print()

# 3. 状態を更新（トピックを変更）
selected_state = states[1]  # トピック生成後の状態
new_config = graph.update_state(
    selected_state.config,
    values={"topic": "chickens"}
)

# 4. チェックポイントから実行を再開
new_result = graph.invoke(None, new_config)
print("New Topic:", new_result["topic"])
print("New Joke:", new_result["joke"])
```

### 例2: エラーデバッグでの使用

エラーが発生した場合、タイムトラベルを使用して問題を特定し、修正できます。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class ProcessingState(TypedDict):
    input_data: str
    processed_data: str
    error: NotRequired[str]

def process_data(state: ProcessingState):
    """データを処理（エラーが発生する可能性がある）"""
    try:
        # 処理を実行
        result = complex_processing(state["input_data"])
        return {"processed_data": result, "error": ""}
    except Exception as e:
        return {"error": str(e)}

# グラフの構築
workflow = StateGraph(ProcessingState)
workflow.add_node("process", process_data)
workflow.add_edge(START, "process")
workflow.add_edge("process", END)

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

# 実行
config = {"configurable": {"thread_id": "debug-1"}}
try:
    result = graph.invoke({"input_data": "test"}, config=config)
except Exception as e:
    print(f"エラーが発生しました: {e}")

# 実行履歴を確認
states = list(graph.get_state_history(config))
for state in states:
    if state.values.get("error"):
        print(f"エラーが発生したチェックポイント: {state.config['configurable']['checkpoint_id']}")
        print(f"エラー内容: {state.values['error']}")
        
        # エラーが発生した時点の状態を確認
        print(f"状態: {state.values}")
        
        # 状態を修正して再実行
        fixed_config = graph.update_state(
            state.config,
            values={"input_data": "fixed-input", "error": ""}
        )
        
        # 修正した状態から再実行
        fixed_result = graph.invoke(None, fixed_config)
        print(f"修正後の結果: {fixed_result}")
```

### 例3: 代替案の探索

複数のパスを試して、最適な結果を見つけます。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class DecisionState(TypedDict):
    question: str
    answer: NotRequired[str]
    approach: NotRequired[str]

def approach_a(state: DecisionState):
    """アプローチAで回答"""
    answer = model_a.invoke(state["question"])
    return {"answer": answer.content, "approach": "A"}

def approach_b(state: DecisionState):
    """アプローチBで回答"""
    answer = model_b.invoke(state["question"])
    return {"answer": answer.content, "approach": "B"}

# グラフの構築
workflow = StateGraph(DecisionState)
workflow.add_node("approach_a", approach_a)
workflow.add_node("approach_b", approach_b)
workflow.add_edge(START, "approach_a")
workflow.add_edge("approach_a", END)

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

# 最初の実行
config = {"configurable": {"thread_id": "explore-1"}}
result_a = graph.invoke({"question": "What is AI?"}, config=config)

# アプローチAの結果を確認
print("Approach A:", result_a["answer"])

# チェックポイントを取得して、アプローチBを試す
states = list(graph.get_state_history(config))
initial_state = states[-1]  # 最初の状態

# アプローチBで再実行
new_config = graph.update_state(
    initial_state.config,
    values={"approach": "B"}
)

# アプローチBのノードを実行
result_b = graph.invoke(None, new_config)

print("Approach B:", result_b["answer"])

# 両方の結果を比較
print("\n比較:")
print(f"Approach A: {result_a['answer']}")
print(f"Approach B: {result_b['answer']}")
```

## ベストプラクティス

### 1. チェックポイントの選択

適切なチェックポイントを選択することが重要です。

```python
# 実行履歴を確認
states = list(graph.get_state_history(config))

# 特定のノードの実行前の状態を取得
def find_checkpoint_before_node(states, node_name):
    """指定されたノードの実行前のチェックポイントを検索"""
    for state in states:
        if node_name in state.next:
            return state
    return None

# 使用例
checkpoint = find_checkpoint_before_node(states, "write_joke")
if checkpoint:
    # このチェックポイントから再実行
    new_config = graph.update_state(checkpoint.config, values={...})
    result = graph.invoke(None, new_config)
```

### 2. 状態の検証

状態を更新する前に、その状態が有効であることを確認します。

```python
def validate_state(state_values, required_fields):
    """状態の検証"""
    for field in required_fields:
        if field not in state_values:
            raise ValueError(f"必須フィールド '{field}' が存在しません")
    return True

# 使用例
selected_state = states[1]
if validate_state(selected_state.values, ["topic"]):
    new_config = graph.update_state(
        selected_state.config,
        values={"topic": "new-topic"}
    )
```

### 3. フォークの管理

複数のフォークを作成する場合、それぞれを追跡します。

```python
# フォークを管理
forks = {}

# 元の実行
config = {"configurable": {"thread_id": "main-1"}}
result = graph.invoke(initial_state, config=config)
forks["original"] = result

# フォーク1
states = list(graph.get_state_history(config))
fork1_config = graph.update_state(states[1].config, values={...})
forks["fork1"] = graph.invoke(None, fork1_config)

# フォーク2
fork2_config = graph.update_state(states[1].config, values={...})
forks["fork2"] = graph.invoke(None, fork2_config)

# 結果を比較
for name, result in forks.items():
    print(f"{name}: {result}")
```

### 4. デバッグ時の使用

エラーデバッグでは、エラーが発生した直前の状態を確認します。

```python
# エラーが発生した実行
try:
    result = graph.invoke(state, config=config)
except Exception as e:
    # 実行履歴を確認
    states = list(graph.get_state_history(config))
    
    # エラーが発生した直前の状態を確認
    error_state = states[0]  # 最新の状態
    print(f"エラー直前の状態: {error_state.values}")
    print(f"次に実行されるノード: {error_state.next}")
    
    # 状態を修正して再実行
    fixed_config = graph.update_state(
        error_state.config,
        values={...}  # 修正した状態
    )
    fixed_result = graph.invoke(None, fixed_config)
```

## まとめ

タイムトラベルにより、以下のことが可能になります：

1. **推論の理解**: 成功した結果に至ったステップを分析
2. **エラーのデバッグ**: エラーが発生した場所と理由を特定
3. **代替案の探索**: 異なるパスを試して、より良い解決策を見つける
4. **状態の修正**: 過去の状態を変更して、新しい結果を生成

適切にタイムトラベルを使用することで、LLMベースのエージェントの動作をより深く理解し、デバッグや最適化を効率的に行えます。

## 次のステップ

- [P16: Persistence](./P16_persistence.md): 状態の永続化の詳細
- [P18: Interrupts](./P18_interrupts.md): 人間の介入（Human-in-the-loop）
- [P21: Durable Execution](./P21_durable_execution.md): 耐久性のある実行
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る

# タスクリスト提案機能の実装プラン

このドキュメントでは、LangGraphを使用してAIエージェントが自律的にタスクリスト（ToDos）を作成し、それを実行する機能の実装プランを説明します。

## 概要

AIエージェントがユーザーの要求を受け取り、以下の流れで動作する機能を実装します：

1. **タスクプランニング**: ユーザーの要求を分析し、実行すべきタスクリストを生成
2. **タスク実行**: 生成されたタスクリストを順次または並列で実行
3. **結果統合**: 各タスクの実行結果を統合して最終結果を生成

この機能は、LangGraphの**Orchestrator-Workerパターン**をベースに実装します。

## なぜこの機能が必要か？

### 従来のアプローチの問題点

従来のエージェント実装では、以下のような問題がありました：

1. **固定されたワークフロー**: タスクの順序や内容が事前に定義されている
2. **柔軟性の欠如**: 異なる要求に対して同じワークフローを適用する必要がある
3. **拡張性の低さ**: 新しいタスクタイプを追加する際に、グラフ全体の修正が必要

### タスクリスト提案機能の利点

1. **自律的な計画**: LLMが要求を分析し、適切なタスクリストを生成
2. **動的な実行**: タスク数や内容が実行時に決定される
3. **柔軟性**: 異なる要求に対して適応的なタスクリストを生成
4. **拡張性**: 新しいタスクタイプを追加しやすい

## アーキテクチャ

### 全体の流れ

```
ユーザー要求
    ↓
[タスクプランナー] → タスクリスト生成
    ↓
[タスク割り当て] → 各タスクをワーカーに割り当て
    ↓
[ワーカー1] [ワーカー2] [ワーカー3] ... (並列実行)
    ↓
[結果統合] → 最終結果を生成
    ↓
ユーザーに結果を返す
```

### ノード構成

1. **`task_planner`（タスクプランナー）**
   - ユーザーの要求を分析
   - LLMを使用してタスクリストを生成
   - 構造化出力（Pydantic）を使用してタスクを定義

2. **`task_executor`（タスク実行ワーカー）**
   - 個別のタスクを実行
   - タスクタイプに応じた処理を実行
   - 結果を状態に保存

3. **`result_synthesizer`（結果統合）**
   - すべてのタスクの実行結果を統合
   - 最終的な結果を生成

4. **`assign_tasks`（タスク割り当て関数）**
   - タスクリストを各ワーカーに割り当て
   - Send APIを使用して並列実行を開始

## 実装詳細

### 1. 状態の定義

```python
from typing import Annotated, List, NotRequired
from typing_extensions import TypedDict
import operator
from pydantic import BaseModel, Field

# タスクの定義
class Task(BaseModel):
    id: str = Field(description="タスクの一意な識別子")
    title: str = Field(description="タスクのタイトル")
    description: str = Field(description="タスクの詳細説明")
    task_type: str = Field(description="タスクのタイプ（例: 'research', 'analysis', 'generation'）")
    dependencies: List[str] = Field(default=[], description="依存するタスクのIDリスト")
    priority: int = Field(default=1, description="タスクの優先度（1-5）")

class TaskList(BaseModel):
    tasks: List[Task] = Field(description="タスクのリスト")

# メインの状態
class State(TypedDict):
    user_request: str  # ユーザーの要求
    task_list: NotRequired[List[Task]]  # 生成されたタスクリスト
    completed_tasks: Annotated[List[dict], operator.add]  # 完了したタスクの結果
    final_result: NotRequired[str]  # 最終結果

# ワーカーの状態
class WorkerState(TypedDict):
    task: Task  # 実行するタスク
    completed_tasks: Annotated[List[dict], operator.add]  # 完了したタスクの結果
```

### 2. タスクプランナーの実装

```python
from langchain.messages import SystemMessage, HumanMessage

# 構造化出力スキーマでLLMを拡張
planner = llm.with_structured_output(TaskList)

def task_planner(state: State) -> dict:
    """ユーザーの要求からタスクリストを生成する"""
    # LLMにタスクリストの生成を依頼
    task_list = planner.invoke([
        SystemMessage(content="""ユーザーの要求を分析し、実行すべきタスクリストを生成してください。
各タスクは明確で実行可能なものにしてください。
タスク間の依存関係も考慮してください。"""),
        HumanMessage(content=f"ユーザーの要求: {state['user_request']}"),
    ])
    
    return {"task_list": task_list.tasks}
```

### 3. タスク実行ワーカーの実装

```python
def task_executor(state: WorkerState) -> dict:
    """個別のタスクを実行するワーカー"""
    task = state['task']
    
    # タスクタイプに応じた処理を実行
    if task.task_type == "research":
        result = execute_research_task(task)
    elif task.task_type == "analysis":
        result = execute_analysis_task(task)
    elif task.task_type == "generation":
        result = execute_generation_task(task)
    else:
        result = execute_default_task(task)
    
    # 結果を保存
    return {
        "completed_tasks": [{
            "task_id": task.id,
            "title": task.title,
            "result": result,
            "status": "completed"
        }]
    }

def execute_research_task(task: Task) -> str:
    """リサーチタスクを実行"""
    # 実際の実装では、Web検索やデータベース検索などを行う
    return f"リサーチ結果: {task.description}について調査しました。"

def execute_analysis_task(task: Task) -> str:
    """分析タスクを実行"""
    # 実際の実装では、データ分析やLLMによる分析などを行う
    return f"分析結果: {task.description}について分析しました。"

def execute_generation_task(task: Task) -> str:
    """生成タスクを実行"""
    # 実際の実装では、LLMによるコンテンツ生成などを行う
    return f"生成結果: {task.description}についてコンテンツを生成しました。"

def execute_default_task(task: Task) -> str:
    """デフォルトのタスク実行"""
    return f"タスク '{task.title}' を実行しました。"
```

### 4. 結果統合の実装

```python
def result_synthesizer(state: State) -> dict:
    """すべてのタスクの実行結果を統合"""
    completed_tasks = state.get("completed_tasks", [])
    
    # タスクの結果を整理
    task_results = {}
    for task_result in completed_tasks:
        task_results[task_result["task_id"]] = task_result
    
    # 最終結果を生成（LLMを使用）
    results_summary = "\n\n".join([
        f"タスク: {tr['title']}\n結果: {tr['result']}"
        for tr in completed_tasks
    ])
    
    # LLMに最終結果の統合を依頼
    final_result = llm.invoke([
        SystemMessage(content="タスクの実行結果を統合し、ユーザーに提示する形式で最終結果を生成してください。"),
        HumanMessage(content=f"ユーザーの要求: {state['user_request']}\n\n実行結果:\n{results_summary}"),
    ])
    
    return {"final_result": final_result.content}
```

### 5. タスク割り当て関数の実装

```python
from langgraph.types import Send

def assign_tasks(state: State):
    """タスクリストを各ワーカーに割り当てる"""
    task_list = state.get("task_list", [])
    
    # 依存関係を考慮してタスクをソート（簡易版）
    # 実際の実装では、より高度な依存関係解決が必要
    sorted_tasks = sort_tasks_by_dependencies(task_list)
    
    # 各タスクに対してSendオブジェクトを作成
    return [Send("task_executor", {"task": task}) for task in sorted_tasks]

def sort_tasks_by_dependencies(tasks: List[Task]) -> List[Task]:
    """依存関係に基づいてタスクをソート"""
    # 簡易的な実装（トポロジカルソートなどが必要な場合もある）
    # ここでは優先度順にソート
    return sorted(tasks, key=lambda t: t.priority, reverse=True)
```

### 6. グラフの構築

```python
from langgraph.graph import StateGraph, START, END

# グラフの構築
builder = StateGraph(State)

# ノードの追加
builder.add_node("task_planner", task_planner)
builder.add_node("task_executor", task_executor)
builder.add_node("result_synthesizer", result_synthesizer)

# エッジの追加
builder.add_edge(START, "task_planner")
builder.add_conditional_edges(
    "task_planner",
    assign_tasks,
    ["task_executor"]
)
builder.add_edge("task_executor", "result_synthesizer")
builder.add_edge("result_synthesizer", END)

# グラフをコンパイル
graph = builder.compile()
```

## 実装の拡張

### 依存関係の考慮

現在の実装では、依存関係の処理が簡易的です。より高度な実装では：

1. **トポロジカルソート**: 依存関係に基づいてタスクを正しい順序で実行
2. **並列実行の最適化**: 依存関係がないタスクは並列実行
3. **依存関係の検証**: 循環依存の検出とエラーハンドリング

### タスクタイプの拡張

新しいタスクタイプを追加するには：

1. `Task`モデルに新しいタスクタイプを定義
2. `task_executor`に新しい処理ロジックを追加
3. 必要に応じて専用のノードを作成

### エラーハンドリング

タスク実行時のエラーを処理するには：

1. **リトライ機能**: 失敗したタスクを再試行
2. **エラー報告**: 失敗したタスクを結果に含める
3. **部分的な完了**: 一部のタスクが失敗しても、成功したタスクの結果を返す

### 中断と再開

`interrupt`を使用して、タスクリストの承認を求める：

```python
from langgraph.types import interrupt

def task_planner(state: State) -> dict:
    """タスクリストを生成し、ユーザーの承認を求める"""
    task_list = planner.invoke([...])
    
    # 中断してユーザーの承認を求める
    user_response = interrupt({
        "message": "以下のタスクリストで実行を開始しますか？",
        "task_list": task_list.tasks
    })
    
    # ユーザーの応答を確認
    if not user_response.get("approved", False):
        return {"task_list": []}  # タスクリストを空にして終了
    
    return {"task_list": task_list.tasks}
```

## 実装のベストプラクティス

### 1. タスクの粒度

- **細かすぎる**: 単純な操作を個別のタスクにする必要はない
- **粗すぎる**: 複雑な操作を1つのタスクにまとめない
- **適切**: 各タスクが明確で、独立して実行可能なものにする

### 2. タスクの説明

タスクの説明は明確で、実行可能な内容にする：

- ❌ 悪い例: "データを分析する"
- ✅ 良い例: "過去3年間の売上データを分析し、トレンドを特定する"

### 3. 依存関係の管理

依存関係は最小限にし、並列実行の機会を最大化する：

- 可能な限り独立したタスクに分割
- 必要な場合のみ依存関係を定義

### 4. エラーハンドリング

各タスクで適切にエラーを処理する：

```python
def task_executor(state: WorkerState) -> dict:
    """個別のタスクを実行するワーカー"""
    task = state['task']
    
    try:
        result = execute_task(task)
        return {
            "completed_tasks": [{
                "task_id": task.id,
                "title": task.title,
                "result": result,
                "status": "completed"
            }]
        }
    except Exception as e:
        return {
            "completed_tasks": [{
                "task_id": task.id,
                "title": task.title,
                "result": None,
                "status": "failed",
                "error": str(e)
            }]
        }
```

## 実装手順

### ステップ1: プロジェクト構造の作成

```
archives/p21_tasks_list/
├── my_agent/
│   ├── __init__.py
│   ├── agent.py              # グラフの定義
│   └── utils/
│       ├── __init__.py
│       ├── state.py          # 状態の定義
│       ├── nodes.py          # ノード関数の実装
│       └── tasks.py          # タスク実行ロジック
├── tests/
│   ├── __init__.py
│   └── test_invoke.py        # テストコード
├── langgraph.json            # LangGraph設定
└── README.md                  # プロジェクト説明
```

### ステップ2: 状態とモデルの定義

`my_agent/utils/state.py`に状態とPydanticモデルを定義

### ステップ3: ノード関数の実装

`my_agent/utils/nodes.py`に各ノード関数を実装

### ステップ4: グラフの構築

`my_agent/agent.py`にグラフを構築

### ステップ5: テストの作成

`tests/test_invoke.py`にテストコードを作成

### ステップ6: ドキュメントの作成

`README.md`に使用方法と説明を記載

## 使用例

### 基本的な使用例

```python
# グラフの実行
state = graph.invoke({
    "user_request": "PythonのLangGraphについて調査し、簡単なサンプルコードを生成してください。"
})

print(state["final_result"])
```

### 中断を使用した例

```python
# タスクリストの承認を求める
config = {"configurable": {"thread_id": "test-thread"}}
state = graph.invoke(
    {"user_request": "..."},
    config=config
)

# 中断された場合、ユーザーの承認を待つ
# 承認後、同じconfigで再開
```

## まとめ

タスクリスト提案機能の実装により、以下のことが実現できます：

1. **自律的な計画**: LLMが要求を分析し、適切なタスクリストを生成
2. **動的な実行**: タスク数や内容が実行時に決定される
3. **柔軟性**: 異なる要求に対して適応的なタスクリストを生成
4. **拡張性**: 新しいタスクタイプを追加しやすい

この実装は、Orchestrator-Workerパターンをベースにしており、LangGraphの強力な機能を活用しています。

## 関連ドキュメント

- [P21: Tasks（タスク）](./P21_tasks.md): タスクの詳細な説明
- [P14: Workflows + Agents](./P14_workflows_agents.md): Orchestrator-Workerパターンの詳細
- [P14: Orchestrator-Workerパターンの詳細解説](./P14_workflows_orchestrator_worker_details.md): Send APIの詳細
- [P18: Interrupts](./P18_interrupts.md): 中断と再開のメカニズム
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る


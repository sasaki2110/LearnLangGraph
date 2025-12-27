# p21_tasks_list - タスクリスト提案機能の実装例

このプロジェクトは、LangGraphを使用してAIエージェントが自律的にタスクリスト（ToDos）を作成し、それを実行する機能を実装したものです。

## 概要

このエージェントは、ユーザーの要求を受け取り、以下の流れで動作します：

1. **タスクプランニング**: ユーザーの要求を分析し、実行すべきタスクリストを生成
2. **タスク実行**: 生成されたタスクリストを並列で実行
3. **結果統合**: 各タスクの実行結果を統合して最終結果を生成

この実装は、LangGraphの**Orchestrator-Workerパターン**をベースにしています。

## 構造

```
p21_tasks_list/
├── my_agent/              # プロジェクトコード
│   ├── __init__.py
│   ├── agent.py           # グラフを構築するコード
│   └── utils/             # グラフ用のユーティリティ
│       ├── __init__.py
│       ├── state.py       # グラフの状態定義とPydanticモデル
│       └── nodes.py       # グラフ用のノード関数
├── tests/                 # テストコード
│   ├── __init__.py
│   ├── conftest.py        # テストフィクスチャ
│   └── test_invoke.py     # invokeを確認するテスト
├── langgraph.json         # LangGraph設定ファイル
└── README.md             # このファイル
```

## セットアップ

### 1. 依存関係のインストール

親フォルダで実行済み。

### 2. 環境変数の設定

親フォルダで実行済み。

### 3. LangGraph Studioで実行

```bash
cd archives/p21_tasks_list
langgraph dev
```

サーバーが起動すると、以下のURLでアクセスできます：
- **APIエンドポイント**: `http://127.0.0.1:2024`
- **Studio UI**: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

## 機能

このエージェントは、以下の機能を提供します：

1. **タスクリストの自動生成**: ユーザーの要求を分析し、適切なタスクリストを生成
2. **並列タスク実行**: 生成されたタスクを並列で実行
3. **結果統合**: すべてのタスクの実行結果を統合して最終結果を生成
4. **柔軟なタスクタイプ**: リサーチ、分析、生成など、異なるタイプのタスクに対応

## 実装の詳細

### タスクの定義

`my_agent/utils/state.py`で、タスクを定義しています：

```python
class Task(BaseModel):
    id: str  # タスクの一意な識別子
    title: str  # タスクのタイトル
    description: str  # タスクの詳細説明
    task_type: str  # タスクのタイプ（'research', 'analysis', 'generation'）
    dependencies: List[str]  # 依存するタスクのIDリスト
    priority: int  # タスクの優先度（1-5）
```

### タスクプランナー

`task_planner`ノードは、LLMを使用してユーザーの要求からタスクリストを生成します：

```python
def task_planner(state: State) -> dict:
    """ユーザーの要求からタスクリストを生成する"""
    task_list = planner.invoke([...])
    return {"task_list": task_list.tasks}
```

### タスク実行ワーカー

`task_executor`ノードは、個別のタスクを実行します。タスクタイプに応じて、異なる処理を実行します：

- **research**: リサーチタスクを実行
- **analysis**: 分析タスクを実行
- **generation**: 生成タスクを実行

### 結果統合

`result_synthesizer`ノードは、すべてのタスクの実行結果を統合して最終結果を生成します。

### グラフの構築

`my_agent/agent.py`で、グラフを構築しています：

```python
builder = StateGraph(State)
builder.add_node("task_planner", task_planner)
builder.add_node("task_executor", task_executor)
builder.add_node("result_synthesizer", result_synthesizer)

builder.add_edge(START, "task_planner")
builder.add_conditional_edges(
    "task_planner",
    assign_tasks,
    ["task_executor"]
)
builder.add_edge("task_executor", "result_synthesizer")
builder.add_edge("result_synthesizer", END)

graph = builder.compile()
```

## テストの実行

**注意**: テストを実行する前に、親ディレクトリで仮想環境を有効化してください。

```bash
# 親ディレクトリで仮想環境を有効化
cd /root/LearnLangGraph
source venv/bin/activate  # Linux/macOS

# p21_tasks_listディレクトリに移動
cd archives/p21_tasks_list

# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/test_invoke.py

# 詳細な出力で実行
pytest -v
```

### 実装されているテスト

- **test_graph_invoke**: グラフをinvokeして結果を確認
- **test_graph_invoke_with_checkpointer**: チェックポインタ付きグラフをinvokeして結果を確認
- **test_graph_invoke_task_structure**: タスクの構造を確認
- **test_graph_invoke_multiple_requests**: 複数の異なる要求でグラフを実行
- **test_graph_invoke_empty_request**: 空の要求でグラフを実行

## 使用例

### 基本的な使用例

```python
from my_agent.agent import graph

# グラフの実行
result = graph.invoke({
    "user_request": "PythonのLangGraphについて簡単に説明してください。"
})

print(result["final_result"])
```

### チェックポインタを使用した例

```python
import uuid
from my_agent.agent import graph
from langgraph.checkpoint.memory import MemorySaver

# チェックポインタを作成
checkpointer = MemorySaver()

# グラフを再コンパイル（チェックポインタ付き）
# （実際の実装では、conftest.pyのfixtureを使用）

# スレッドIDを含む設定を定義
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# グラフの実行
result = graph.invoke(
    {"user_request": "PythonのLangGraphについて簡単に説明してください。"},
    config=config
)
```

## タスクリスト提案機能の利点

1. **自律的な計画**: LLMが要求を分析し、適切なタスクリストを生成
2. **動的な実行**: タスク数や内容が実行時に決定される
3. **柔軟性**: 異なる要求に対して適応的なタスクリストを生成
4. **拡張性**: 新しいタスクタイプを追加しやすい

## 関連ドキュメント

- [P21: タスクリスト提案機能の実装プラン](../../docs/p21_tasks_list.md): 実装プランの詳細な説明
- [P21: Tasks（タスク）](../../docs/P21_tasks.md): タスクの詳細な説明
- [P14: Workflows + Agents](../../docs/P14_workflows_agents.md): Orchestrator-Workerパターンの詳細
- [P14: Orchestrator-Workerパターンの詳細解説](../../docs/P14_workflows_orchestrator_worker_details.md): Send APIの詳細


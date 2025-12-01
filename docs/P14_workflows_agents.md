# Workflows + Agents

このドキュメントでは、LangGraphにおけるワークフロー型とエージェント型の違い、それぞれの特徴、使い分けについて解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/workflows-agents

## 概要

LangGraphでは、グラフベースのシステムを大きく2つのタイプに分類できます：

1. **ワークフロー型（Workflows）**: 予測可能な処理フローを持つシステム
2. **エージェント型（Agents）**: LLMが動的に次の行動を決定するシステム

それぞれに適した用途があり、適切に使い分けることで、効率的で保守性の高いシステムを構築できます。

## ワークフロー型（Workflows）

### 特徴

ワークフロー型は、**予測可能な処理フロー**を持つシステムです。

- **固定されたフロー**: 処理の順序が事前に定義されている
- **決定論的**: 同じ入力に対して同じ処理が実行される
- **制御可能**: 開発者が完全に制御できる

### 適用例

- データ処理パイプライン
- ETL（Extract, Transform, Load）処理
- 定型業務の自動化
- バッチ処理

### 実装例

```python
from langgraph.graph import StateGraph, START, END

class WorkflowState(TypedDict):
    data: list
    processed_data: list
    result: str

def extract(state: WorkflowState) -> dict:
    """データ抽出"""
    # データを抽出
    data = fetch_data()
    return {"data": data}

def transform(state: WorkflowState) -> dict:
    """データ変換"""
    # データを変換
    processed = [process(item) for item in state["data"]]
    return {"processed_data": processed}

def load(state: WorkflowState) -> dict:
    """データロード"""
    # データをロード
    result = save_data(state["processed_data"])
    return {"result": result}

# ワークフローの構築
workflow = StateGraph(WorkflowState)
workflow.add_node("extract", extract)
workflow.add_node("transform", transform)
workflow.add_node("load", load)

# 固定されたフロー
workflow.add_edge(START, "extract")
workflow.add_edge("extract", "transform")
workflow.add_edge("transform", "load")
workflow.add_edge("load", END)

compiled_workflow = workflow.compile()
```

### ワークフロー型の利点

1. **予測可能性**: 処理フローが明確で、動作が予測しやすい
2. **デバッグの容易さ**: 各ステップが独立しており、問題の特定が容易
3. **パフォーマンス**: 不要な処理を避けられるため、効率的
4. **テストの容易さ**: 各ステップを個別にテストできる

### ワークフロー型の制限

1. **柔軟性の欠如**: 予期しない状況に対応しにくい
2. **複雑な分岐**: 複雑な条件分岐を実装するのが困難
3. **動的な判断**: LLMによる動的な判断が必要な場合には不向き

## エージェント型（Agents）

### 特徴

エージェント型は、**LLMが動的に次の行動を決定**するシステムです。

- **動的なフロー**: LLMが状態に基づいて次の行動を決定
- **非決定論的**: 同じ入力でも異なる処理が実行される可能性がある
- **柔軟性**: 予期しない状況にも対応できる

### 適用例

- チャットボット
- 質問応答システム
- 複雑なタスクの自動化
- ツールを使用するエージェント

### 実装例

```python
from langgraph.graph import StateGraph, START, END
from typing import Literal

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

def llm_call(state: AgentState) -> dict:
    """LLMが次の行動を決定"""
    messages = state["messages"]
    response = model_with_tools.invoke(messages)
    return {"messages": [response]}

def tool_node(state: AgentState) -> dict:
    """ツールを実行"""
    tool_calls = state["messages"][-1].tool_calls
    results = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        results.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))
    return {"messages": results}

def should_continue(state: AgentState) -> Literal["tool_node", END]:
    """LLMの判断に基づいて次のステップを決定"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return END

# エージェントの構築
agent = StateGraph(AgentState)
agent.add_node("llm_call", llm_call)
agent.add_node("tool_node", tool_node)

# 動的なフロー（LLMが決定）
agent.add_edge(START, "llm_call")
agent.add_conditional_edges(
    "llm_call",
    should_continue,  # LLMの判断に基づく
    ["tool_node", END]
)
agent.add_edge("tool_node", "llm_call")  # ループ可能

compiled_agent = agent.compile()
```

### エージェント型の利点

1. **柔軟性**: 予期しない状況にも対応できる
2. **自然な対話**: LLMによる自然な判断が可能
3. **複雑なタスク**: 複雑で多様なタスクに対応できる
4. **拡張性**: 新しいツールや機能を追加しやすい

### エージェント型の制限

1. **予測困難性**: 処理フローが予測しにくい
2. **デバッグの難しさ**: LLMの判断が複雑で、問題の特定が困難
3. **コスト**: LLMの呼び出しが多く、コストが高い
4. **パフォーマンス**: 不要な処理が実行される可能性がある

## ワークフロー型とエージェント型の比較

| 特徴 | ワークフロー型 | エージェント型 |
|------|--------------|--------------|
| **処理フロー** | 固定 | 動的 |
| **決定論的** | はい | いいえ |
| **柔軟性** | 低い | 高い |
| **予測可能性** | 高い | 低い |
| **デバッグ** | 容易 | 困難 |
| **コスト** | 低い | 高い |
| **適用例** | データ処理、定型業務 | チャットボット、複雑なタスク |

## 使い分けの指針

### ワークフロー型を選ぶべき場合

1. **処理フローが明確**: 処理の順序が事前に決まっている
2. **決定論的である必要がある**: 同じ入力に対して同じ結果が必要
3. **コストを抑えたい**: LLMの呼び出しを最小限にしたい
4. **パフォーマンスが重要**: 効率的な処理が必要

**例**: データ処理パイプライン、レポート生成、バッチ処理

### エージェント型を選ぶべき場合

1. **柔軟性が必要**: 予期しない状況に対応する必要がある
2. **自然な対話**: ユーザーとの自然な対話が必要
3. **複雑なタスク**: 複雑で多様なタスクに対応する必要がある
4. **ツールの使用**: 複数のツールを動的に選択する必要がある

**例**: チャットボット、質問応答システム、複雑なタスクの自動化

## ハイブリッドアプローチ

実際のシステムでは、**ワークフロー型とエージェント型を組み合わせる**ことがよくあります。

### 例: ハイブリッドシステム

```python
# ワークフロー部分: データの前処理
def preprocess(state: State) -> dict:
    """固定された前処理"""
    data = clean_data(state["input"])
    return {"cleaned_data": data}

# エージェント部分: LLMによる処理
def llm_process(state: State) -> dict:
    """LLMによる動的な処理"""
    response = model.invoke(state["cleaned_data"])
    return {"result": response}

# ワークフロー部分: 結果の後処理
def postprocess(state: State) -> dict:
    """固定された後処理"""
    formatted = format_result(state["result"])
    return {"output": formatted}

# ハイブリッドグラフの構築
hybrid = StateGraph(State)
hybrid.add_node("preprocess", preprocess)  # ワークフロー
hybrid.add_node("llm_process", llm_process)  # エージェント
hybrid.add_node("postprocess", postprocess)  # ワークフロー

hybrid.add_edge(START, "preprocess")
hybrid.add_edge("preprocess", "llm_process")
hybrid.add_edge("llm_process", "postprocess")
hybrid.add_edge("postprocess", END)
```

このように、**固定された処理と動的な処理を組み合わせる**ことで、効率性と柔軟性の両立が可能になります。

## 実践的な設計指針

### 1. 処理を分類する

システムの各処理を、以下のように分類します：

- **固定処理**: ワークフロー型で実装
- **動的処理**: エージェント型で実装
- **境界処理**: ワークフローとエージェントの境界を明確にする

### 2. コストを考慮する

LLMの呼び出しはコストがかかるため、以下の点を考慮します：

- **必要な場合のみLLMを使用**: 固定処理はワークフローで実装
- **キャッシュの活用**: 同じ処理を繰り返さない
- **バッチ処理**: 可能な場合はバッチで処理

### 3. デバッグを容易にする

以下の点に注意して、デバッグを容易にします：

- **ログの記録**: 各ステップでログを記録
- **状態の可視化**: 状態の変化を可視化
- **テストの分離**: ワークフロー部分とエージェント部分を分離してテスト

## まとめ

- **ワークフロー型**: 予測可能な処理フロー、決定論的、コスト効率が良い
- **エージェント型**: 動的な処理フロー、柔軟性が高い、複雑なタスクに対応
- **使い分け**: 処理の性質に応じて適切に選択
- **ハイブリッド**: 両方を組み合わせることで、効率性と柔軟性を両立

適切に使い分けることで、効率的で保守性の高いシステムを構築できます。

## 次のステップ

- [P15: Streaming](./P15_streaming.md): ストリーミング出力の実装
- [P16: Persistence](./P16_persistence.md): 状態の永続化
- [P17: Functional API](./P17_functional_api.md): 関数型APIの使用方法


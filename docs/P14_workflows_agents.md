# Workflows + Agents

このドキュメントでは、LangGraphにおけるワークフロー型とエージェント型の違い、それぞれの特徴、使い分けについて解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/workflows-agents

## 概要

LangGraphでは、グラフベースのシステムを大きく2つのタイプに分類できます：

1. **ワークフロー型（Workflows）**: 予測可能な処理フローを持つシステム
2. **エージェント型（Agents）**: LLMが動的に次の行動を決定するシステム

それぞれに適した用途があり、適切に使い分けることで、効率的で保守性の高いシステムを構築できます。

## LLMの拡張機能（LLMs and Augmentations）

ワークフローとエージェントシステムは、LLMとその拡張機能に基づいています。LLMを拡張する主な方法には以下があります：

- **Tool calling（ツール呼び出し）**: LLMが外部ツールを呼び出すことができる
- **Structured outputs（構造化出力）**: LLMの出力を構造化された形式で取得
- **Short term memory（短期記憶）**: 会話の文脈を保持

### 構造化出力の例

```python
from pydantic import BaseModel, Field

# 構造化出力のスキーマ定義
class SearchQuery(BaseModel):
    search_query: str = Field(None, description="最適化されたWeb検索クエリ")
    justification: str = Field(None, description="このクエリがユーザーのリクエストに関連する理由")

# LLMに構造化出力スキーマを追加
structured_llm = llm.with_structured_output(SearchQuery)

# 拡張されたLLMを呼び出し
output = structured_llm.invoke("カルシウムCTスコアと高コレステロールの関係は？")
```

### ツール呼び出しの例

```python
# ツールの定義
def multiply(a: int, b: int) -> int:
    return a * b

# LLMにツールを追加
llm_with_tools = llm.bind_tools([multiply])

# ツール呼び出しをトリガーする入力でLLMを呼び出し
msg = llm_with_tools.invoke("2と3を掛けると？")

# ツール呼び出しを取得
msg.tool_calls
```

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

## ワークフローパターン

ワークフロー型には、いくつかの実践的なパターンがあります。以下に主要なパターンを紹介します。

### 1. Prompt Chaining（プロンプトチェイニング）

プロンプトチェイニングは、各LLM呼び出しが前の呼び出しの出力を処理するパターンです。明確に定義されたタスクを、小さな検証可能なステップに分解して実行する際によく使用されます。

**適用例**:
- ドキュメントを異なる言語に翻訳
- 生成されたコンテンツの一貫性を検証

**実装例**:

```python
from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END

# グラフの状態
class State(TypedDict):
    topic: str
    joke: str
    improved_joke: str
    final_joke: str

# ノード
def generate_joke(state: State):
    """最初のLLM呼び出しで初期ジョークを生成"""
    msg = llm.invoke(f"{state['topic']}について短いジョークを書いてください")
    return {"joke": msg.content}

def check_punchline(state: State):
    """ジョークにオチがあるかチェックするゲート関数"""
    # シンプルなチェック - ジョークに「?」や「!」が含まれているか
    if "?" in state["joke"] or "!" in state["joke"]:
        return "Pass"
    return "Fail"

def improve_joke(state: State):
    """2回目のLLM呼び出しでジョークを改善"""
    msg = llm.invoke(f"このジョークをより面白くするために言葉遊びを追加してください: {state['joke']}")
    return {"improved_joke": msg.content}

def polish_joke(state: State):
    """3回目のLLM呼び出しで最終的な仕上げ"""
    msg = llm.invoke(f"このジョークに驚きの展開を追加してください: {state['improved_joke']}")
    return {"final_joke": msg.content}

# ワークフローの構築
workflow = StateGraph(State)
workflow.add_node("generate_joke", generate_joke)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)

# ノードを接続するエッジを追加
workflow.add_edge(START, "generate_joke")
workflow.add_conditional_edges(
    "generate_joke", 
    check_punchline, 
    {"Fail": "improve_joke", "Pass": END}
)
workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)

# コンパイル
chain = workflow.compile()
```

### 2. Parallelization（並列化）

並列化では、LLMが同時にタスクに取り組みます。これは、複数の独立したサブタスクを同時に実行するか、同じタスクを複数回実行して異なる出力を確認する際に使用されます。

**適用例**:
- サブタスクを分割して並列実行し、速度を向上
- タスクを複数回実行して異なる出力を確認し、信頼性を向上

**実装例**:

```python
# グラフの状態
class State(TypedDict):
    topic: str
    joke: str
    story: str
    poem: str
    combined_output: str

# ノード
def call_llm_1(state: State):
    """最初のLLM呼び出しでジョークを生成"""
    msg = llm.invoke(f"{state['topic']}についてジョークを書いてください")
    return {"joke": msg.content}

def call_llm_2(state: State):
    """2回目のLLM呼び出しでストーリーを生成"""
    msg = llm.invoke(f"{state['topic']}についてストーリーを書いてください")
    return {"story": msg.content}

def call_llm_3(state: State):
    """3回目のLLM呼び出しで詩を生成"""
    msg = llm.invoke(f"{state['topic']}について詩を書いてください")
    return {"poem": msg.content}

def aggregator(state: State):
    """ジョークとストーリーを1つの出力に結合"""
    combined = f"{state['topic']}についてのストーリー、ジョーク、詩です！\n\n"
    combined += f"ストーリー:\n{state['story']}\n\n"
    combined += f"ジョーク:\n{state['joke']}\n\n"
    combined += f"詩:\n{state['poem']}"
    return {"combined_output": combined}

# ワークフローの構築
parallel_builder = StateGraph(State)
parallel_builder.add_node("call_llm_1", call_llm_1)
parallel_builder.add_node("call_llm_2", call_llm_2)
parallel_builder.add_node("call_llm_3", call_llm_3)
parallel_builder.add_node("aggregator", aggregator)

# ノードを接続するエッジを追加（並列実行）
parallel_builder.add_edge(START, "call_llm_1")
parallel_builder.add_edge(START, "call_llm_2")
parallel_builder.add_edge(START, "call_llm_3")
parallel_builder.add_edge("call_llm_1", "aggregator")
parallel_builder.add_edge("call_llm_2", "aggregator")
parallel_builder.add_edge("call_llm_3", "aggregator")
parallel_builder.add_edge("aggregator", END)

parallel_workflow = parallel_builder.compile()
```

### 3. Routing（ルーティング）

ルーティングワークフローは、入力を処理してから、コンテキスト固有のタスクにルーティングします。これにより、複雑なタスクに対して専門化されたフローを定義できます。

**実装例**:

```python
from typing_extensions import Literal
from langchain.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

# ルーティングロジックとして使用する構造化出力のスキーマ
class Route(BaseModel):
    step: Literal["poem", "story", "joke"] = Field(
        None, description="ルーティングプロセスの次のステップ"
    )

# 構造化出力スキーマでLLMを拡張
router = llm.with_structured_output(Route)

# 状態
class State(TypedDict):
    input: str
    decision: str
    output: str

# ノード
def llm_call_1(state: State):
    """ストーリーを書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_2(state: State):
    """ジョークを書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_3(state: State):
    """詩を書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_router(state: State):
    """入力を適切なノードにルーティング"""
    # ルーティングロジックとして機能する構造化出力で拡張LLMを実行
    decision = router.invoke([
        SystemMessage(content="ユーザーのリクエストに基づいて、ストーリー、ジョーク、または詩にルーティングしてください。"),
        HumanMessage(content=state["input"]),
    ])
    return {"decision": decision.step}

# 適切なノードにルーティングする条件付きエッジ関数
def route_decision(state: State):
    # 次に訪問したいノード名を返す
    if state["decision"] == "story":
        return "llm_call_1"
    elif state["decision"] == "joke":
        return "llm_call_2"
    elif state["decision"] == "poem":
        return "llm_call_3"

# ワークフローの構築
router_builder = StateGraph(State)
router_builder.add_node("llm_call_1", llm_call_1)
router_builder.add_node("llm_call_2", llm_call_2)
router_builder.add_node("llm_call_3", llm_call_3)
router_builder.add_node("llm_call_router", llm_call_router)

# ノードを接続するエッジを追加
router_builder.add_edge(START, "llm_call_router")
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {  # route_decisionが返す名前: 次に訪問するノード名
        "llm_call_1": "llm_call_1",
        "llm_call_2": "llm_call_2",
        "llm_call_3": "llm_call_3",
    },
)
router_builder.add_edge("llm_call_1", END)
router_builder.add_edge("llm_call_2", END)
router_builder.add_edge("llm_call_3", END)

# ワークフローをコンパイル
router_workflow = router_builder.compile()
```

### 4. Orchestrator-Worker（オーケストレーター-ワーカー）

オーケストレーター-ワーカー構成では、オーケストレーターが以下を行います：
- タスクをサブタスクに分解
- サブタスクをワーカーに委任
- ワーカーの出力を最終結果に統合

このパターンは、並列化よりも柔軟性が高く、サブタスクを事前に定義できない場合によく使用されます。

**実装例（Send APIを使用）**:

```python
from typing import Annotated, List
import operator
from langgraph.types import Send
from langchain.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

# 計画に使用する構造化出力のスキーマ
class Section(BaseModel):
    name: str = Field(description="レポートのこのセクションの名前")
    description: str = Field(description="このセクションでカバーされる主要なトピックと概念の概要")

class Sections(BaseModel):
    sections: List[Section] = Field(description="レポートのセクション")

# 構造化出力スキーマでLLMを拡張
planner = llm.with_structured_output(Sections)

# グラフの状態
class State(TypedDict):
    topic: str  # レポートのトピック
    sections: list[Section]  # レポートセクションのリスト
    completed_sections: Annotated[list, operator.add]  # すべてのワーカーが並列にこのキーに書き込む
    final_report: str  # 最終レポート

# ワーカーの状態
class WorkerState(TypedDict):
    section: Section
    completed_sections: Annotated[list, operator.add]

# ノード
def orchestrator(state: State):
    """レポートの計画を生成するオーケストレーター"""
    # クエリを生成
    report_sections = planner.invoke([
        SystemMessage(content="レポートの計画を生成してください。"),
        HumanMessage(content=f"レポートのトピックは次のとおりです: {state['topic']}"),
    ])
    return {"sections": report_sections.sections}

def llm_call(state: WorkerState):
    """ワーカーがレポートのセクションを書く"""
    # セクションを生成
    section = llm.invoke([
        SystemMessage(
            content="提供された名前と説明に従ってレポートセクションを書いてください。各セクションに前書きを含めないでください。マークダウン形式を使用してください。"
        ),
        HumanMessage(
            content=f"セクション名: {state['section'].name}、説明: {state['section'].description}"
        ),
    ])
    # 更新されたセクションを完了したセクションに書き込む
    return {"completed_sections": [section.content]}

def synthesizer(state: State):
    """セクションから完全なレポートを統合"""
    # 完了したセクションのリスト
    completed_sections = state["completed_sections"]
    # 完了したセクションを文字列にフォーマットして、最終セクションのコンテキストとして使用
    completed_report_sections = "\n\n---\n\n".join(completed_sections)
    return {"final_report": completed_report_sections}

# 各セクションにワーカーを割り当てる条件付きエッジ関数
def assign_workers(state: State):
    """計画の各セクションにワーカーを割り当てる"""
    # Send() API経由で並列にセクション書き込みを開始
    return [Send("llm_call", {"section": s}) for s in state["sections"]]

# ワークフローの構築
orchestrator_worker_builder = StateGraph(State)
orchestrator_worker_builder.add_node("orchestrator", orchestrator)
orchestrator_worker_builder.add_node("llm_call", llm_call)
orchestrator_worker_builder.add_node("synthesizer", synthesizer)

# ノードを接続するエッジを追加
orchestrator_worker_builder.add_edge(START, "orchestrator")
orchestrator_worker_builder.add_conditional_edges(
    "orchestrator", assign_workers, ["llm_call"]
)
orchestrator_worker_builder.add_edge("llm_call", "synthesizer")
orchestrator_worker_builder.add_edge("synthesizer", END)

# ワークフローをコンパイル
orchestrator_worker = orchestrator_worker_builder.compile()
```

### 5. Evaluator-Optimizer（評価者-最適化）

評価者-最適化ワークフローでは、1つのLLM呼び出しが応答を作成し、もう1つがその応答を評価します。評価者または人間が応答の改善が必要と判断した場合、フィードバックが提供され、応答が再作成されます。許容可能な応答が生成されるまで、このループが続きます。

**実装例**:

```python
from typing_extensions import Literal
from pydantic import BaseModel, Field

# グラフの状態
class State(TypedDict):
    joke: str
    topic: str
    feedback: str
    funny_or_not: str

# 評価に使用する構造化出力のスキーマ
class Feedback(BaseModel):
    grade: Literal["funny", "not funny"] = Field(
        description="ジョークが面白いかどうかを決定してください。"
    )
    feedback: str = Field(
        description="ジョークが面白くない場合、改善方法についてフィードバックを提供してください。"
    )

# 構造化出力スキーマでLLMを拡張
evaluator = llm.with_structured_output(Feedback)

# ノード
def llm_call_generator(state: State):
    """LLMがジョークを生成"""
    if state.get("feedback"):
        msg = llm.invoke(
            f"{state['topic']}についてジョークを書いてください。ただし、フィードバックを考慮してください: {state['feedback']}"
        )
    else:
        msg = llm.invoke(f"{state['topic']}についてジョークを書いてください")
    return {"joke": msg.content}

def llm_call_evaluator(state: State):
    """LLMがジョークを評価"""
    grade = evaluator.invoke(f"ジョークを評価してください {state['joke']}")
    return {"funny_or_not": grade.grade, "feedback": grade.feedback}

# 評価者のフィードバックに基づいてジョーク生成器にルーティングするか、終了する条件付きエッジ関数
def route_joke(state: State):
    """評価者のフィードバックに基づいてジョーク生成器にルーティングするか、終了する"""
    if state["funny_or_not"] == "funny":
        return "Accepted"
    elif state["funny_or_not"] == "not funny":
        return "Rejected + Feedback"

# ワークフローの構築
optimizer_builder = StateGraph(State)
optimizer_builder.add_node("llm_call_generator", llm_call_generator)
optimizer_builder.add_node("llm_call_evaluator", llm_call_evaluator)

# ノードを接続するエッジを追加
optimizer_builder.add_edge(START, "llm_call_generator")
optimizer_builder.add_edge("llm_call_generator", "llm_call_evaluator")
optimizer_builder.add_conditional_edges(
    "llm_call_evaluator",
    route_joke,
    {  # route_jokeが返す名前: 次に訪問するノード名
        "Accepted": END,
        "Rejected + Feedback": "llm_call_generator",
    },
)

# ワークフローをコンパイル
optimizer_workflow = optimizer_builder.compile()
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

エージェントは通常、**ツール**を使用してアクションを実行するLLMとして実装されます。以下は、ツールを使用するエージェントの実装例です。

#### ツールの定義

```python
from langchain.tools import tool

# ツールを定義
@tool
def multiply(a: int, b: int) -> int:
    """`a`と`b`を掛けます。
    
    Args:
        a: 最初の整数
        b: 2番目の整数
    """
    return a * b

@tool
def add(a: int, b: int) -> int:
    """`a`と`b`を足します。
    
    Args:
        a: 最初の整数
        b: 2番目の整数
    """
    return a + b

@tool
def divide(a: int, b: int) -> float:
    """`a`を`b`で割ります。
    
    Args:
        a: 最初の整数
        b: 2番目の整数
    """
    return a / b

# LLMにツールを追加
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)
```

#### エージェントの実装

```python
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from typing_extensions import Literal

# ノード
def llm_call(state: MessagesState):
    """LLMがツールを呼び出すかどうかを決定"""
    return {
        "messages": [
            llm_with_tools.invoke(
                [
                    SystemMessage(
                        content="あなたは、一連の入力に対して算術演算を実行するタスクを担当する親切なアシスタントです。"
                    )
                ]
                + state["messages"]
            )
        ]
    }

def tool_node(state: dict):
    """ツール呼び出しを実行"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

# LLMがツール呼び出しを行ったかどうかに基づいて、ツールノードにルーティングするか、終了する条件付きエッジ関数
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """LLMがツール呼び出しを行ったかどうかに基づいて、ループを続けるか停止するかを決定"""
    messages = state["messages"]
    last_message = messages[-1]
    # LLMがツール呼び出しを行う場合、アクションを実行
    if last_message.tool_calls:
        return "tool_node"
    # それ以外の場合は停止（ユーザーに返信）
    return END

# ワークフローの構築
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# ノードを接続するエッジを追加
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# エージェントをコンパイル
agent = agent_builder.compile()

# 実行例
messages = [HumanMessage(content="3と4を足してください。")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
```

### エージェントの特徴

エージェントは、**ツール**を使用してアクションを実行するLLMとして実装されることが一般的です。エージェントは継続的なフィードバックループで動作し、問題と解決策が予測不可能な状況で使用されます。

エージェントはワークフローよりも自律性が高く、使用するツールや問題の解決方法について決定を下すことができます。ただし、利用可能なツールセットとエージェントの動作に関するガイドラインは、開発者が定義できます。

**注意**: エージェントの詳細については、[Quickstart](../p12_quickstart.py)を参照するか、LangChainの[エージェントの動作方法](https://docs.langchain.com/oss/python/langchain/agents)についてのドキュメントを参照してください。

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
  - **主要なパターン**: Prompt chaining、Parallelization、Routing、Orchestrator-worker、Evaluator-optimizer
- **エージェント型**: 動的な処理フロー、柔軟性が高い、複雑なタスクに対応
  - **ツール使用**: エージェントはツールを使用してアクションを実行
- **LLMの拡張機能**: Tool calling、Structured outputs、Short term memory
- **使い分け**: 処理の性質に応じて適切に選択
- **ハイブリッド**: 両方を組み合わせることで、効率性と柔軟性を両立

適切に使い分けることで、効率的で保守性の高いシステムを構築できます。本ドキュメントで紹介したワークフローパターンは、実践的なシステム構築において非常に有用です。

## 次のステップ

- [P15: Streaming](./P15_streaming.md): ストリーミング出力の実装
- [P16: Persistence](./P16_persistence.md): 状態の永続化
- [P17: Functional API](./P17_functional_api.md): 関数型APIの使用方法


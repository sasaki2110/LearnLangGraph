# Supervisor

このドキュメントでは、LangGraphにおけるスーパーバイザー（Supervisor）の概念と使用方法について解説します。

公式リファレンス: https://reference.langchain.com/python/langgraph/supervisor/

## 概要

LangGraphにおける**スーパーバイザー（Supervisor）**は、複数のエージェントを管理し、全体のワークフローを調整する役割を持つコンポーネントです。各エージェントはスーパーバイザーと通信し、次にどのエージェントを呼び出すかの決定をスーパーバイザーが行います。

スーパーバイザーパターンは、以下のような場面で特に有効です：

- **複数の専門エージェント**: 異なる専門分野を持つ複数のエージェントを統括する
- **タスクの割り当て**: ユーザーの要求を解析し、適切なエージェントにタスクを割り当てる
- **結果の統合**: 各エージェントからの出力を統合し、一貫性のある応答を生成する
- **制御フロー**: エージェント間の通信やタスクの順序を制御する

## スーパーバイザーの基本概念

### スーパーバイザーとは

スーパーバイザーは、**複数のエージェントを統括し、タスクの割り当てや進行を制御する役割を持つエージェント**です。スーパーバイザーは、ユーザーからの入力を受け取り、適切なエージェントにタスクを割り振り、結果を統合してユーザーに返します。

### スーパーバイザーパターンのアーキテクチャ

典型的なスーパーバイザーパターンのアーキテクチャは以下のようになります：

```
ユーザー入力
    ↓
スーパーバイザー（タスクの解析と割り当て）
    ↓
    ├─→ エージェント1（専門分野1）
    ├─→ エージェント2（専門分野2）
    └─→ エージェント3（専門分野3）
    ↓
スーパーバイザー（結果の統合）
    ↓
ユーザーへの応答
```

### スーパーバイザーの動作フロー

1. **入力の受信**: ユーザーからの入力を受け取る
2. **タスクの解析**: 入力内容を解析し、どのエージェントにタスクを割り当てるかを決定
3. **エージェントの呼び出し**: 適切なエージェントを呼び出す
4. **結果の収集**: エージェントからの結果を収集
5. **結果の統合**: 複数のエージェントからの結果を統合
6. **応答の生成**: 統合された結果をユーザーに返す

## スーパーバイザーの実装方法

### 1. 基本的なスーパーバイザーの実装

スーパーバイザーは、`StateGraph`を使用して実装できます。以下は、基本的なスーパーバイザーの実装例です。

```python
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from typing_extensions import Literal
from typing import Annotated
import operator

# 状態の定義
class SupervisorState(TypedDict):
    messages: Annotated[list, operator.add]
    next_agent: str  # 次に呼び出すエージェント

# エージェントの定義（例）
def research_agent(state: MessagesState):
    """研究エージェント"""
    # 研究処理
    response = llm.invoke([
        SystemMessage(content="あなたは研究アシスタントです。"),
        *state["messages"]
    ])
    return {"messages": [response]}

def writing_agent(state: MessagesState):
    """執筆エージェント"""
    # 執筆処理
    response = llm.invoke([
        SystemMessage(content="あなたは執筆アシスタントです。"),
        *state["messages"]
    ])
    return {"messages": [response]}

def review_agent(state: MessagesState):
    """レビューエージェント"""
    # レビュー処理
    response = llm.invoke([
        SystemMessage(content="あなたはレビューアシスタントです。"),
        *state["messages"]
    ])
    return {"messages": [response]}

# スーパーバイザーの実装
def supervisor(state: SupervisorState):
    """スーパーバイザー: どのエージェントを呼び出すかを決定"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # LLMを使用して、次に呼び出すエージェントを決定
    response = llm.invoke([
        SystemMessage(content="""あなたはスーパーバイザーです。
        ユーザーの要求に基づいて、以下のエージェントのいずれかを選択してください:
        - research: 研究が必要な場合
        - writing: 執筆が必要な場合
        - review: レビューが必要な場合
        - finish: タスクが完了した場合
        
        応答は、選択したエージェント名のみを返してください。"""),
        last_message
    ])
    
    next_agent = response.content.strip().lower()
    return {"next_agent": next_agent}

# ルーティング関数
def route_to_agent(state: SupervisorState) -> Literal["research", "writing", "review", "finish"]:
    """スーパーバイザーの決定に基づいて、適切なエージェントにルーティング"""
    next_agent = state.get("next_agent", "finish")
    
    if next_agent == "research":
        return "research"
    elif next_agent == "writing":
        return "writing"
    elif next_agent == "review":
        return "review"
    else:
        return "finish"

# グラフの構築
graph = StateGraph(SupervisorState)
graph.add_node("supervisor", supervisor)
graph.add_node("research", research_agent)
graph.add_node("writing", writing_agent)
graph.add_node("review", review_agent)

# エッジの追加
graph.add_edge(START, "supervisor")
graph.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "research": "research",
        "writing": "writing",
        "review": "review",
        "finish": END
    }
)
graph.add_edge("research", "supervisor")
graph.add_edge("writing", "supervisor")
graph.add_edge("review", "supervisor")

supervisor_graph = graph.compile()
```

### 2. Prebuilt関数を使用する方法

LangGraphには、スーパーバイザーを簡単に作成するためのPrebuilt関数が用意されています。

#### `create_supervisor`（非推奨）

**注意**: `create_supervisor`は非推奨となっており、多くのユースケースでは、ツールを直接使用するスーパーバイザーパターンが推奨されています。

```python
# 非推奨
from langgraph.prebuilt import create_supervisor

# エージェントのリスト
agents = {
    "research": research_agent,
    "writing": writing_agent,
    "review": review_agent
}

# スーパーバイザーの作成（非推奨）
supervisor = create_supervisor(
    agents=agents,
    system_prompt="あなたはスーパーバイザーです。"
)
```

#### 推奨: ツールを使用するスーパーバイザーパターン

ツールを直接使用するスーパーバイザーパターンは、コンテキストの管理が容易になり、柔軟な設計が可能となります。

```python
from langchain.tools import tool
from langgraph.prebuilt import create_handoff_tool

# エージェント間でタスクを引き継ぐためのツール
def create_agent_tool(agent_name: str, agent_graph):
    """エージェントを呼び出すためのツールを作成"""
    @tool
    def agent_tool(input: str) -> str:
        """エージェントを呼び出します。"""
        result = agent_graph.invoke({"messages": [HumanMessage(content=input)]})
        return result["messages"][-1].content
    return agent_tool

# 各エージェントのツールを作成
research_tool = create_agent_tool("research", research_agent)
writing_tool = create_agent_tool("writing", writing_agent)
review_tool = create_agent_tool("review", review_agent)

# スーパーバイザーエージェントにツールを追加
supervisor_agent = create_react_agent(
    model=llm,
    tools=[research_tool, writing_tool, review_tool],
    system_prompt="あなたはスーパーバイザーです。適切なエージェントにタスクを割り当ててください。"
)
```

### 3. `create_handoff_tool`を使用する方法

`create_handoff_tool`は、エージェント間でタスクを引き継ぐためのツールを作成します。

```python
from langgraph.prebuilt import create_handoff_tool

# エージェント間でタスクを引き継ぐツールを作成
research_handoff = create_handoff_tool("research", research_agent)
writing_handoff = create_handoff_tool("writing", writing_agent)
review_handoff = create_handoff_tool("review", review_agent)

# スーパーバイザーエージェントにツールを追加
supervisor_agent = create_react_agent(
    model=llm,
    tools=[research_handoff, writing_handoff, review_handoff]
)
```

### 4. `create_forward_message_tool`を使用する方法

`create_forward_message_tool`は、メッセージを他のエージェントに転送するためのツールを作成します。

```python
from langgraph.prebuilt import create_forward_message_tool

# メッセージ転送ツールを作成
forward_to_research = create_forward_message_tool("research", research_agent)
forward_to_writing = create_forward_message_tool("writing", writing_agent)

# スーパーバイザーエージェントにツールを追加
supervisor_agent = create_react_agent(
    model=llm,
    tools=[forward_to_research, forward_to_writing]
)
```

## 実装例

### 例1: マルチエージェントシステム

複数の専門エージェントを統括するスーパーバイザーの実装例です。

```python
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.messages import SystemMessage, HumanMessage
from typing_extensions import Literal

# 専門エージェントの定義
agents = {
    "coder": StateGraph(MessagesState)
        .add_node("code", lambda s: {"messages": [llm.invoke([
            SystemMessage(content="あなたはプログラマーです。コードを書いてください。"),
            *s["messages"]
        ])]})
        .compile(),
    
    "writer": StateGraph(MessagesState)
        .add_node("write", lambda s: {"messages": [llm.invoke([
            SystemMessage(content="あなたはライターです。文章を書いてください。"),
            *s["messages"]
        ])]})
        .compile(),
    
    "analyst": StateGraph(MessagesState)
        .add_node("analyze", lambda s: {"messages": [llm.invoke([
            SystemMessage(content="あなたはアナリストです。データを分析してください。"),
            *s["messages"]
        ])]})
        .compile()
}

# スーパーバイザーの実装
def supervisor(state: MessagesState):
    """スーパーバイザー: どのエージェントを呼び出すかを決定"""
    response = llm.invoke([
        SystemMessage(content="""ユーザーの要求に基づいて、以下のエージェントのいずれかを選択:
        - coder: プログラミングが必要
        - writer: 執筆が必要
        - analyst: 分析が必要
        - finish: 完了
        
        応答は選択したエージェント名のみ。"""),
        state["messages"][-1]
    ])
    
    next_agent = response.content.strip().lower()
    return {"next_agent": next_agent, "messages": [response]}

def route(state: dict) -> Literal["coder", "writer", "analyst", "finish"]:
    next_agent = state.get("next_agent", "finish")
    if next_agent in ["coder", "writer", "analyst"]:
        return next_agent
    return "finish"

# メイングラフの構築
graph = StateGraph(MessagesState)
graph.add_node("supervisor", supervisor)
for name, agent in agents.items():
    graph.add_node(name, agent)

graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", route, {
    "coder": "coder",
    "writer": "writer",
    "analyst": "analyst",
    "finish": END
})
for name in agents.keys():
    graph.add_edge(name, "supervisor")

main_graph = graph.compile()
```

### 例2: 階層型スーパーバイザー

複数のスーパーバイザーを階層的に配置する実装例です。

```python
# レベル1: 専門分野別のスーパーバイザー
tech_supervisor = create_supervisor(["coder", "tester"])
content_supervisor = create_supervisor(["writer", "editor"])

# レベル2: トップレベルのスーパーバイザー
top_supervisor = create_supervisor([
    ("tech", tech_supervisor),
    ("content", content_supervisor)
])
```

## スーパーバイザーのベストプラクティス

### 1. 明確な責任の分離

各エージェントは、明確な責任を持つべきです。スーパーバイザーは、各エージェントの役割を理解し、適切にタスクを割り当てます。

```python
# 良い例: 明確な責任
agents = {
    "researcher": research_agent,  # 研究のみ
    "writer": writing_agent,        # 執筆のみ
    "reviewer": review_agent        # レビューのみ
}

# 悪い例: 責任が曖昧
agents = {
    "general": general_agent  # 何でもする（避けるべき）
}
```

### 2. コンテキストの管理

スーパーバイザーは、各エージェントに適切なコンテキストを渡す必要があります。

```python
def supervisor(state: SupervisorState):
    """スーパーバイザー: コンテキストを管理"""
    messages = state["messages"]
    context = extract_context(messages)  # コンテキストの抽出
    
    # 各エージェントに適切なコンテキストを渡す
    response = llm.invoke([
        SystemMessage(content=f"コンテキスト: {context}"),
        *messages
    ])
    
    return {"next_agent": determine_agent(response), "context": context}
```

### 3. エラーハンドリング

エージェントの実行エラーを適切に処理し、スーパーバイザーが継続できるようにします。

```python
def route_to_agent(state: SupervisorState):
    """エラーハンドリングを含むルーティング"""
    try:
        next_agent = state["next_agent"]
        if next_agent in available_agents:
            return next_agent
        else:
            # フォールバック
            return "default_agent"
    except Exception as e:
        # エラー処理
        return "error_handler"
```

### 4. 結果の統合

複数のエージェントからの結果を適切に統合します。

```python
def integrate_results(state: SupervisorState):
    """複数のエージェントからの結果を統合"""
    results = []
    for agent_name, agent_result in state.get("agent_results", {}).items():
        results.append(f"{agent_name}: {agent_result}")
    
    # 結果を統合
    integrated = llm.invoke([
        SystemMessage(content="以下の結果を統合してください。"),
        HumanMessage(content="\n".join(results))
    ])
    
    return {"final_result": integrated.content}
```

## スーパーバイザーと他のパターンの比較

| パターン | 特徴 | 適用例 |
|---------|------|--------|
| **スーパーバイザー** | 中央集権的な制御 | 複数の専門エージェントを統括 |
| **スワーム** | 分散的な協調 | エージェントが自律的に協調 |
| **オーケストレーター** | 固定されたワークフロー | 予測可能な処理フロー |

## まとめ

LangGraphにおけるスーパーバイザーは、以下の特徴を持ちます：

1. **エージェントの管理**: 複数のエージェントを統括し、タスクの割り当てや進行を制御します
2. **タスクの調整**: タスクの優先順位や依存関係を考慮し、エージェント間でのタスクの調整を行います
3. **結果の統合**: 各エージェントからの出力を統合し、一貫性のある応答を生成します
4. **制御フロー**: エージェント間の通信やタスクの順序を制御します

スーパーバイザーパターンは、複数の専門エージェントを統括する際に特に有効です。適切に設計することで、柔軟で強力なマルチエージェントシステムを構築できます。

## 次のステップ

- [P29: Agents](./p29_agents.md): エージェントの基本概念
- [P31: Swarm](./p31_swarm.md): 複数のエージェントが協調するスワーム
- [P19: Subgraphs](./P19_subgraphs.md): サブグラフの使用方法
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る

## 参考資料

- [公式リファレンス: Supervisor](https://reference.langchain.com/python/langgraph/supervisor/)
- [LangGraph Supervisor：スーパーバイジング・インテリジェンスを用いた多知能連携管理ツール](https://aisharenet.com/ja/langgraph-supervisor/)
- [LangGraph-supervisorで自作マルチAIエージェントを作る！](https://zenn.dev/rakushaking/articles/6cafbde87be5a5)
- [AIエージェント設計の課題解決：マルチエージェントのデザインパターン](https://zenn.dev/dxclab/articles/683ddbadf401f0)


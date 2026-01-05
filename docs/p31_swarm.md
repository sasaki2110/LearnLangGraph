# Swarm

このドキュメントでは、LangGraphにおけるスワーム（Swarm）の概念と使用方法について解説します。

公式リファレンス: https://reference.langchain.com/python/langgraph/swarm/

## 概要

LangGraphにおける**スワーム（Swarm）**は、複数のエージェントが協調してタスクを遂行するためのフレームワークです。各エージェントは独立して動作しつつ、全体として統一された目的に向かって協力します。

スワームパターンは、以下のような場面で特に有効です：

- **分散処理**: タスクを複数のエージェントに分散し、並列処理を行うことで効率を向上
- **自己組織化**: 各エージェントが中央の指示なしに相互に連携し、全体の目的を達成
- **適応性**: 環境の変化や新たなタスクに対して柔軟に対応
- **スケーラビリティ**: エージェントの数を増減させることで、システムの処理能力を容易に調整

## スワームの基本概念

### スワームとは

スワームは、**複数のエージェントが協調してタスクを遂行する分散型のアーキテクチャ**です。スーパーバイザーパターンが中央集権的な制御を行うのに対し、スワームパターンは分散的な協調を特徴とします。

### スワームパターンのアーキテクチャ

典型的なスワームパターンのアーキテクチャは以下のようになります：

```
タスク
    ↓
スワーム（複数のエージェント）
    ├─→ エージェント1（自律的に動作）
    ├─→ エージェント2（自律的に動作）
    └─→ エージェント3（自律的に動作）
    ↓
結果の統合
    ↓
最終結果
```

### スワームの動作フロー

1. **タスクの受信**: タスクを受け取る
2. **エージェントへの分散**: タスクを複数のエージェントに分散
3. **並列処理**: 各エージェントが独立して処理を実行
4. **結果の収集**: 各エージェントからの結果を収集
5. **結果の統合**: 複数のエージェントからの結果を統合
6. **最終結果の生成**: 統合された結果を返す

### スワームとスーパーバイザーの違い

| 特徴 | スワーム | スーパーバイザー |
|------|---------|----------------|
| **制御方式** | 分散的 | 中央集権的 |
| **エージェントの関係** | 対等 | 階層的 |
| **タスクの割り当て** | 自律的 | 中央で決定 |
| **適用例** | 並列処理、分散計算 | 専門エージェントの統括 |

## スワームの実装方法

### 1. 基本的なスワームの実装

スワームは、`StateGraph`と`Send` APIを使用して実装できます。以下は、基本的なスワームの実装例です。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain.messages import SystemMessage, HumanMessage
from typing import Annotated, List
import operator

# 状態の定義
class SwarmState(TypedDict):
    task: str  # タスク
    agent_results: Annotated[List[str], operator.add]  # エージェントの結果
    final_result: str  # 最終結果

# エージェントの定義
def agent_1(state: SwarmState):
    """エージェント1: タスクの一部を処理"""
    response = llm.invoke([
        SystemMessage(content="あなたはエージェント1です。タスクの一部を処理してください。"),
        HumanMessage(content=state["task"])
    ])
    return {"agent_results": [f"Agent 1: {response.content}"]}

def agent_2(state: SwarmState):
    """エージェント2: タスクの一部を処理"""
    response = llm.invoke([
        SystemMessage(content="あなたはエージェント2です。タスクの一部を処理してください。"),
        HumanMessage(content=state["task"])
    ])
    return {"agent_results": [f"Agent 2: {response.content}"]}

def agent_3(state: SwarmState):
    """エージェント3: タスクの一部を処理"""
    response = llm.invoke([
        SystemMessage(content="あなたはエージェント3です。タスクの一部を処理してください。"),
        HumanMessage(content=state["task"])
    ])
    return {"agent_results": [f"Agent 3: {response.content}"]}

# 結果の統合
def integrate_results(state: SwarmState):
    """複数のエージェントからの結果を統合"""
    results = "\n".join(state["agent_results"])
    response = llm.invoke([
        SystemMessage(content="以下の結果を統合してください。"),
        HumanMessage(content=results)
    ])
    return {"final_result": response.content}

# タスクの分散
def distribute_task(state: SwarmState):
    """タスクを複数のエージェントに分散"""
    return [
        Send("agent_1", {"task": state["task"]}),
        Send("agent_2", {"task": state["task"]}),
        Send("agent_3", {"task": state["task"]})
    ]

# グラフの構築
graph = StateGraph(SwarmState)
graph.add_node("distribute", distribute_task)
graph.add_node("agent_1", agent_1)
graph.add_node("agent_2", agent_2)
graph.add_node("agent_3", agent_3)
graph.add_node("integrate", integrate_results)

# エッジの追加
graph.add_edge(START, "distribute")
graph.add_conditional_edges("distribute", lambda s: ["agent_1", "agent_2", "agent_3"])
graph.add_edge("agent_1", "integrate")
graph.add_edge("agent_2", "integrate")
graph.add_edge("agent_3", "integrate")
graph.add_edge("integrate", END)

swarm = graph.compile()
```

### 2. Prebuilt関数を使用する方法

LangGraphには、スワームを簡単に作成するためのPrebuilt関数が用意されています。

#### `create_swarm`

`create_swarm`は、複数のエージェントからなるスワームを作成します。

```python
from langgraph.prebuilt import create_swarm

# エージェントのリスト
agents = {
    "agent_1": agent_1_graph,
    "agent_2": agent_2_graph,
    "agent_3": agent_3_graph
}

# スワームの作成
swarm = create_swarm(
    agents=agents,
    default_active_agent="agent_1"  # デフォルトのアクティブエージェント
)
```

#### `add_active_agent_router`

`add_active_agent_router`は、現在アクティブなエージェントへのルーティングを`StateGraph`に追加します。

```python
from langgraph.prebuilt import add_active_agent_router

# グラフの構築
graph = StateGraph(SwarmState)

# エージェントの追加
for name, agent in agents.items():
    graph.add_node(name, agent)

# アクティブエージェントルーターの追加
add_active_agent_router(
    graph,
    agents=list(agents.keys()),
    default_active_agent="agent_1"
)

swarm = graph.compile()
```

## 実装例

### 例1: 並列処理スワーム

複数のエージェントが並列にタスクを処理するスワームの実装例です。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import Annotated, List
import operator

class ParallelSwarmState(TypedDict):
    input_data: str
    processed_chunks: Annotated[List[str], operator.add]
    final_output: str

def process_chunk_1(state: ParallelSwarmState):
    """チャンク1を処理"""
    chunk = state["input_data"][:100]  # 最初の100文字
    result = process(chunk)
    return {"processed_chunks": [result]}

def process_chunk_2(state: ParallelSwarmState):
    """チャンク2を処理"""
    chunk = state["input_data"][100:200]  # 次の100文字
    result = process(chunk)
    return {"processed_chunks": [result]}

def process_chunk_3(state: ParallelSwarmState):
    """チャンク3を処理"""
    chunk = state["input_data"][200:]  # 残りの文字
    result = process(chunk)
    return {"processed_chunks": [result]}

def distribute_chunks(state: ParallelSwarmState):
    """チャンクを分散"""
    return [
        Send("process_chunk_1", {"input_data": state["input_data"]}),
        Send("process_chunk_2", {"input_data": state["input_data"]}),
        Send("process_chunk_3", {"input_data": state["input_data"]})
    ]

def merge_results(state: ParallelSwarmState):
    """結果をマージ"""
    merged = "\n".join(state["processed_chunks"])
    return {"final_output": merged}

# グラフの構築
graph = StateGraph(ParallelSwarmState)
graph.add_node("distribute", distribute_chunks)
graph.add_node("process_chunk_1", process_chunk_1)
graph.add_node("process_chunk_2", process_chunk_2)
graph.add_node("process_chunk_3", process_chunk_3)
graph.add_node("merge", merge_results)

graph.add_edge(START, "distribute")
graph.add_conditional_edges("distribute", lambda s: ["process_chunk_1", "process_chunk_2", "process_chunk_3"])
graph.add_edge("process_chunk_1", "merge")
graph.add_edge("process_chunk_2", "merge")
graph.add_edge("process_chunk_3", "merge")
graph.add_edge("merge", END)

parallel_swarm = graph.compile()
```

### 例2: 動的タスク割り当てスワーム

タスクの内容に応じて、動的にエージェントにタスクを割り当てるスワームの実装例です。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import Annotated, List
import operator

class DynamicSwarmState(TypedDict):
    task: str
    task_type: str
    agent_results: Annotated[List[str], operator.add]
    final_result: str

def classify_task(state: DynamicSwarmState):
    """タスクの種類を分類"""
    response = llm.invoke([
        SystemMessage(content="タスクの種類を分類してください: research, writing, analysis"),
        HumanMessage(content=state["task"])
    ])
    task_type = response.content.strip().lower()
    return {"task_type": task_type}

def route_to_agents(state: DynamicSwarmState):
    """タスクの種類に応じてエージェントにルーティング"""
    task_type = state["task_type"]
    sends = []
    
    if task_type == "research":
        sends.append(Send("research_agent", {"task": state["task"]}))
    elif task_type == "writing":
        sends.append(Send("writing_agent", {"task": state["task"]}))
    elif task_type == "analysis":
        sends.append(Send("analysis_agent", {"task": state["task"]}))
    else:
        # デフォルト: すべてのエージェントに送信
        sends = [
            Send("research_agent", {"task": state["task"]}),
            Send("writing_agent", {"task": state["task"]}),
            Send("analysis_agent", {"task": state["task"]})
        ]
    
    return sends

def research_agent(state: DynamicSwarmState):
    """研究エージェント"""
    response = llm.invoke([
        SystemMessage(content="あなたは研究アシスタントです。"),
        HumanMessage(content=state["task"])
    ])
    return {"agent_results": [f"Research: {response.content}"]}

def writing_agent(state: DynamicSwarmState):
    """執筆エージェント"""
    response = llm.invoke([
        SystemMessage(content="あなたは執筆アシスタントです。"),
        HumanMessage(content=state["task"])
    ])
    return {"agent_results": [f"Writing: {response.content}"]}

def analysis_agent(state: DynamicSwarmState):
    """分析エージェント"""
    response = llm.invoke([
        SystemMessage(content="あなたは分析アシスタントです。"),
        HumanMessage(content=state["task"])
    ])
    return {"agent_results": [f"Analysis: {response.content}"]}

def integrate_results(state: DynamicSwarmState):
    """結果を統合"""
    results = "\n".join(state["agent_results"])
    response = llm.invoke([
        SystemMessage(content="以下の結果を統合してください。"),
        HumanMessage(content=results)
    ])
    return {"final_result": response.content}

# グラフの構築
graph = StateGraph(DynamicSwarmState)
graph.add_node("classify", classify_task)
graph.add_node("route", route_to_agents)
graph.add_node("research_agent", research_agent)
graph.add_node("writing_agent", writing_agent)
graph.add_node("analysis_agent", analysis_agent)
graph.add_node("integrate", integrate_results)

graph.add_edge(START, "classify")
graph.add_edge("classify", "route")
graph.add_conditional_edges("route", lambda s: ["research_agent", "writing_agent", "analysis_agent"])
graph.add_edge("research_agent", "integrate")
graph.add_edge("writing_agent", "integrate")
graph.add_edge("analysis_agent", "integrate")
graph.add_edge("integrate", END)

dynamic_swarm = graph.compile()
```

### 例3: 自己組織化スワーム

各エージェントが自律的に協調するスワームの実装例です。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from typing import Annotated, List
import operator

class SelfOrganizingSwarmState(TypedDict):
    task: str
    agent_states: dict
    collaboration_results: Annotated[List[str], operator.add]
    final_result: str

def agent_1(state: SelfOrganizingSwarmState):
    """エージェント1: 自律的に動作"""
    # 他のエージェントの状態を確認
    other_states = {k: v for k, v in state["agent_states"].items() if k != "agent_1"}
    
    response = llm.invoke([
        SystemMessage(content="あなたはエージェント1です。他のエージェントと協調してください。"),
        HumanMessage(content=f"タスク: {state['task']}\n他のエージェントの状態: {other_states}")
    ])
    
    return {
        "agent_states": {"agent_1": response.content},
        "collaboration_results": [f"Agent 1: {response.content}"]
    }

def agent_2(state: SelfOrganizingSwarmState):
    """エージェント2: 自律的に動作"""
    other_states = {k: v for k, v in state["agent_states"].items() if k != "agent_2"}
    
    response = llm.invoke([
        SystemMessage(content="あなたはエージェント2です。他のエージェントと協調してください。"),
        HumanMessage(content=f"タスク: {state['task']}\n他のエージェントの状態: {other_states}")
    ])
    
    return {
        "agent_states": {"agent_2": response.content},
        "collaboration_results": [f"Agent 2: {response.content}"]
    }

def initialize_swarm(state: SelfOrganizingSwarmState):
    """スワームの初期化"""
    return {
        "agent_states": {},
        "collaboration_results": []
    }

def distribute_to_all(state: SelfOrganizingSwarmState):
    """すべてのエージェントにタスクを分散"""
    return [
        Send("agent_1", {"task": state["task"], "agent_states": state.get("agent_states", {})}),
        Send("agent_2", {"task": state["task"], "agent_states": state.get("agent_states", {})})
    ]

def finalize_results(state: SelfOrganizingSwarmState):
    """結果を最終化"""
    results = "\n".join(state["collaboration_results"])
    response = llm.invoke([
        SystemMessage(content="以下の結果を統合してください。"),
        HumanMessage(content=results)
    ])
    return {"final_result": response.content}

# グラフの構築
graph = StateGraph(SelfOrganizingSwarmState)
graph.add_node("initialize", initialize_swarm)
graph.add_node("distribute", distribute_to_all)
graph.add_node("agent_1", agent_1)
graph.add_node("agent_2", agent_2)
graph.add_node("finalize", finalize_results)

graph.add_edge(START, "initialize")
graph.add_edge("initialize", "distribute")
graph.add_conditional_edges("distribute", lambda s: ["agent_1", "agent_2"])
graph.add_edge("agent_1", "finalize")
graph.add_edge("agent_2", "finalize")
graph.add_edge("finalize", END)

self_organizing_swarm = graph.compile()
```

## スワームのベストプラクティス

### 1. タスクの適切な分散

タスクを適切に分散することで、並列処理の効率を最大化します。

```python
def distribute_task_efficiently(state: SwarmState):
    """タスクを効率的に分散"""
    task = state["task"]
    chunk_size = len(task) // num_agents
    
    sends = []
    for i, agent in enumerate(agents):
        chunk = task[i * chunk_size:(i + 1) * chunk_size]
        sends.append(Send(agent, {"task": chunk}))
    
    return sends
```

### 2. 結果の統合戦略

複数のエージェントからの結果を適切に統合する戦略を設計します。

```python
def integrate_with_strategy(state: SwarmState):
    """戦略に基づいて結果を統合"""
    results = state["agent_results"]
    
    # 戦略1: 単純な結合
    if strategy == "concatenate":
        return {"final_result": "\n".join(results)}
    
    # 戦略2: LLMによる統合
    elif strategy == "llm_integrate":
        response = llm.invoke([
            SystemMessage(content="以下の結果を統合してください。"),
            HumanMessage(content="\n".join(results))
        ])
        return {"final_result": response.content}
    
    # 戦略3: 投票による統合
    elif strategy == "voting":
        # 投票ロジック
        return {"final_result": vote(results)}
```

### 3. エラーハンドリング

エージェントの実行エラーを適切に処理し、スワームが継続できるようにします。

```python
def agent_with_error_handling(state: SwarmState):
    """エラーハンドリングを含むエージェント"""
    try:
        result = process_task(state["task"])
        return {"agent_results": [result]}
    except Exception as e:
        # エラーを記録し、デフォルト値を返す
        logger.error(f"エージェントエラー: {e}")
        return {"agent_results": [f"エラー: {str(e)}"]}
```

### 4. スケーラビリティの考慮

エージェントの数を動的に調整できるように設計します。

```python
def create_scalable_swarm(num_agents: int):
    """スケーラブルなスワームを作成"""
    agents = {}
    for i in range(num_agents):
        agents[f"agent_{i}"] = create_agent(f"Agent {i}")
    
    return create_swarm(agents=agents)
```

## スワームの応用例

### 1. 大規模データ処理

大規模なデータを複数のエージェントに分散して処理します。

```python
def process_large_dataset(dataset: List[str]):
    """大規模データセットを処理"""
    swarm = create_swarm(agents=processing_agents)
    
    # データをチャンクに分割
    chunks = [dataset[i:i+100] for i in range(0, len(dataset), 100)]
    
    # 各チャンクをエージェントに分散
    results = []
    for chunk in chunks:
        result = swarm.invoke({"task": chunk})
        results.append(result["final_result"])
    
    return results
```

### 2. 複雑な問題解決

複雑な問題を複数のエージェントに分散して解決します。

```python
def solve_complex_problem(problem: str):
    """複雑な問題を解決"""
    # 問題をサブ問題に分解
    sub_problems = decompose_problem(problem)
    
    # 各サブ問題をエージェントに割り当て
    swarm = create_swarm(agents=solving_agents)
    solutions = []
    
    for sub_problem in sub_problems:
        solution = swarm.invoke({"task": sub_problem})
        solutions.append(solution["final_result"])
    
    # 解決策を統合
    final_solution = integrate_solutions(solutions)
    return final_solution
```

## まとめ

LangGraphにおけるスワームは、以下の特徴を持ちます：

1. **分散処理**: タスクを複数のエージェントに分散し、並列処理を行うことで効率を向上
2. **自己組織化**: 各エージェントが中央の指示なしに相互に連携し、全体の目的を達成
3. **適応性**: 環境の変化や新たなタスクに対して柔軟に対応
4. **スケーラビリティ**: エージェントの数を増減させることで、システムの処理能力を容易に調整

スワームパターンは、並列処理や分散計算が必要な場面で特に有効です。適切に設計することで、効率的で柔軟なマルチエージェントシステムを構築できます。

## 次のステップ

- [P29: Agents](./p29_agents.md): エージェントの基本概念
- [P30: Supervisor](./p30_supervisor.md): 複数のエージェントを管理するスーパーバイザー
- [P19: Subgraphs](./P19_subgraphs.md): サブグラフの使用方法
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る

## 参考資料

- [公式リファレンス: Swarm](https://reference.langchain.com/python/langgraph/swarm/)
- [スワームがAIエージェントのダークホースとなった理由は？](https://www.gate.com/ja/learn/articles/how-swarms-became-the-ai-agent-dark-horse/6140)
- [マルチエージェントシステム：スワームアーキテクチャ徹底解説と活用事例](https://www.toolify.ai/ja/ai-news-jp/%E5%BE%B9%E5%BA%95%E8%A7%A3%E8%AA%AC%E6%B4%BB%E7%94%A8%E4%BA%8B%E4%BE%8B-3430818)
- [LangGraphのマルチエージェントシステム](https://qiita.com/taka_yayoi/items/f25835e123a251ab102a)


# Agents

このドキュメントでは、LangGraphにおけるエージェント（Agents）の概念と使用方法について解説します。

公式リファレンス: https://reference.langchain.com/python/langgraph/agents/

## 概要

LangGraphにおける**エージェント（Agents）**は、**ノード（機能単位）とエッジ（処理の流れ）で構成されたグラフ**です。このグラフ構造により、LLMがツールを呼び出してタスクを実行するシステムを構築できます。

### 重要な理解ポイント

**「エージェント」とは何か？**

1. **手動で構築したグラフ = エージェント**
   - `StateGraph`を使ってノードとエッジで構成したグラフは、そのままエージェントです
   - 例：`llm_call`ノード → `tool_node`ノード → 条件付きエッジでループ

2. **Prebuilt関数で作成したグラフ = エージェント**
   - `create_react_agent`などのPrebuilt関数も、内部でグラフを構築してエージェントを作成します
   - 最終的には同じグラフ構造になります

**つまり、どちらの方法で作成しても、結果は「エージェント（グラフ）」です。**

エージェントは、LLM（大規模言語モデル）を活用し、以下のような特徴を持ちます：

- **ツールの呼び出し**: エージェントは、必要に応じて外部のツールやサービスを呼び出してタスクを遂行します
- **ループ処理**: ツールをループ内で呼び出し、停止条件が満たされるまで処理を続けます
- **状態管理**: エージェントは、自身の状態を管理し、タスクの進行状況や結果を追跡します
- **動的な判断**: LLMが状態に基づいて次の行動を動的に決定します

## エージェントの基本概念

### エージェントとは

エージェントは、**ツールを使用してアクションを実行するLLM**として実装されることが一般的です。エージェントは継続的なフィードバックループで動作し、問題と解決策が予測不可能な状況で使用されます。

**重要な理解：**
- エージェント = グラフ（ノード + エッジ）
- 手動構築もPrebuilt関数も、最終的には同じグラフ構造
- 違いは「構築方法」であり、「エージェントかどうか」ではない

エージェントはワークフローよりも自律性が高く、使用するツールや問題の解決方法について決定を下すことができます。ただし、利用可能なツールセットとエージェントの動作に関するガイドラインは、開発者が定義できます。

### エージェントの動作フロー

典型的なエージェントの動作フローは以下のようになります：

```
START → llm_call → [ツール呼び出しあり？] → tool_node → llm_call → END
                      ↓
                    [ツール呼び出しなし]
                      ↓
                     END
```

1. **START**: エージェントの開始
2. **llm_call**: LLMがユーザーの質問を分析し、ツールを呼び出すかどうかを決定
3. **should_continue**: 条件分岐ロジック
   - ツール呼び出しあり → `tool_node`へ
   - ツール呼び出しなし → `END`へ
4. **tool_node**: ツールを実行し、結果を返す
5. **llm_call**: ツールの結果を受け取り、最終的な回答を生成
6. **END**: エージェントの終了

## エージェントの作成方法

LangGraphでは、エージェントを作成する方法が2つあります：

1. **手動でグラフを構築する方法**（柔軟性が高い）
2. **Prebuilt関数を使用する方法**（開発効率が高い）

### 重要な理解

**どちらの方法でも、最終的には同じ「エージェント（グラフ）」が作成されます。**

```
手動構築: StateGraph → ノード追加 → エッジ追加 → compile() → エージェント（グラフ）
Prebuilt: create_react_agent() → 内部でグラフ構築 → エージェント（グラフ）
```

**結果は同じです。** 違いは「構築方法」であり、「エージェントかどうか」ではありません。

### 1. 手動でReActエージェントを構築する方法

LangGraphでは、`StateGraph`を使用してReActエージェントを手動で構築できます。これは最も柔軟な方法で、完全な制御が可能です。

**この方法で作成したグラフも「ReActエージェント」です。** 実際、`create_react_agent`は内部でこの構造と同じグラフを作成しています。

#### ReActパターンとは

ReAct（Reasoning + Acting）パターンは、以下のサイクルを繰り返します：

1. **思考（Thought）**: LLMが状況を分析し、次の行動を決定
2. **行動（Action）**: ツールを呼び出してアクションを実行
3. **観察（Observation）**: ツールの結果を観察
4. これを繰り返し、タスクが完了するまで続ける

#### 手動構築の実装例

```python
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from langchain.tools import tool
from typing_extensions import Literal

# ツールの定義
@tool
def multiply(a: int, b: int) -> int:
    """`a`と`b`を掛けます。"""
    return a * b

@tool
def add(a: int, b: int) -> int:
    """`a`と`b`を足します。"""
    return a + b

@tool
def divide(a: int, b: int) -> float:
    """`a`を`b`で割ります。"""
    return a / b

# LLMにツールを追加
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

# ノード1: LLM呼び出し（思考と行動の決定）
def llm_call(state: MessagesState):
    """
    ReActパターンの「思考（Thought）」と「行動（Action）」の決定
    
    LLMが現在の状況を分析し、ツールを呼び出すかどうかを決定します。
    """
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

# ノード2: ツール実行（行動の実行と観察）
def tool_node(state: dict):
    """
    ReActパターンの「行動（Action）」の実行と「観察（Observation）」
    
    LLMが決定したツール呼び出しを実行し、結果を観察として返します。
    """
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        # ツールを実行（Action）
        observation = tool.invoke(tool_call["args"])
        # 観察結果をメッセージとして追加（Observation）
        result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": result}

# 条件付きエッジ関数: ループの継続判定
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """
    ReActループを続けるかどうかを決定
    
    - ツール呼び出しがある場合: ツールを実行してループを継続
    - ツール呼び出しがない場合: タスク完了として終了
    """
    messages = state["messages"]
    last_message = messages[-1]
    # LLMがツール呼び出しを行う場合、アクションを実行
    if last_message.tool_calls:
        return "tool_node"
    # それ以外の場合は停止（ユーザーに返信）
    return END

# グラフの構築（ReActパターンの実装）
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)      # 思考と行動の決定
agent_builder.add_node("tool_node", tool_node)    # 行動の実行と観察

# エッジの追加（ReActループの構築）
agent_builder.add_edge(START, "llm_call")         # 開始 → 思考
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]                            # 思考 → 行動 or 終了
)
agent_builder.add_edge("tool_node", "llm_call")   # 観察 → 思考（ループ）

# エージェントをコンパイル
agent = agent_builder.compile()

# 実行例
messages = [HumanMessage(content="3と4を足してください。")]
result = agent.invoke({"messages": messages})
```

#### ReActループの動作フロー

この実装は、以下のReActループを実現しています：

```
START
  ↓
llm_call (思考: 状況を分析)
  ↓
[ツール呼び出しあり？]
  ├─ YES → tool_node (行動: ツール実行 → 観察: 結果取得)
  │         ↓
  │       llm_call (再思考: 観察結果を踏まえて次の行動を決定)
  │         ↓
  │       [ループ継続...]
  │
  └─ NO  → END (タスク完了)
```

#### `create_react_agent`との対応関係

`create_react_agent`は、内部で上記と同じ構造のグラフを作成します：

```python
# Prebuilt関数（内部で上記と同じグラフ構造を作成）
from langchain.agents import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=[add, multiply, divide],
    checkpointer=checkpointer
)

# 手動構築（上記のコードと同じ構造）
# agent = agent_builder.compile()
```

**両者は同じReActエージェントです。** 違いは、Prebuilt関数が内部でグラフ構築のコードを自動生成するだけです。

### 2. Prebuilt関数を使用する方法

LangGraphには、エージェントを簡単に作成するためのPrebuilt関数が用意されています。

**この方法で作成したグラフも「エージェント」です。** Prebuilt関数は、内部で手動構築と同じグラフ構造を作成します。

#### Prebuilt関数のメリット・デメリット

**メリット：**
- **開発効率の向上**: 複雑なエージェントの構築が容易になり、迅速なプロトタイピングが可能
- **ベストプラクティスの活用**: 事前構築された関数は、一般的なユースケースに基づいて設計されており、信頼性が高い
- **コードの簡潔性**: 数行のコードでエージェントを作成できる

**デメリット：**
- **カスタマイズの制限**: 特定の要件に合わせた細かな調整が難しい場合がある
  - 例：長期メモリの取得や独自の終了条件を間に挟むのが難しい
- **内部構造の理解**: Prebuilt関数の内部動作を理解するには、一定の学習が必要

**推奨される使い分け：**
- **Prebuilt関数**: 基本的なReActエージェントが必要な場合、プロトタイピング
- **手動構築**: カスタムロジックが必要な場合、実用化に向けた開発

#### `create_react_agent`

**注意**: `create_react_agent`は`langgraph.prebuilt`から`langchain.agents`に移動されました。これは**関数の移動**であり、Prebuilt関数自体が非推奨になったわけではありません。

```python
# 旧: langgraph.prebuiltから（非推奨）
# from langgraph.prebuilt import create_react_agent

# 新: langchain.agentsから（推奨）
from langchain.agents import create_react_agent

# ReActエージェントの作成（内部で手動構築と同じグラフ構造を作成）
agent = create_react_agent(
    model=llm,
    tools=[add, multiply, divide],
    checkpointer=checkpointer  # オプション: 永続化が必要な場合
)

# このagentも、手動で構築したReActエージェントと同じ構造です
# 内部では、上記の手動構築例と同じノードとエッジが作成されます
```

**`create_react_agent`の内部動作：**

この関数は、内部で以下のようなグラフ構造を自動生成します：

```python
# create_react_agentが内部で行うこと（概念的なコード）
def _create_react_agent_internal(model, tools, checkpointer=None):
    # ツールの準備
    tools_by_name = {tool.name: tool for tool in tools}
    model_with_tools = model.bind_tools(tools)
    
    # ノードの定義（手動構築と同じ）
    def llm_call(state): ...
    def tool_node(state): ...
    def should_continue(state): ...
    
    # グラフの構築（手動構築と同じ）
    graph = StateGraph(MessagesState)
    graph.add_node("llm_call", llm_call)
    graph.add_node("tool_node", tool_node)
    graph.add_edge(START, "llm_call")
    graph.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    graph.add_edge("tool_node", "llm_call")
    
    return graph.compile(checkpointer=checkpointer)
```

つまり、`create_react_agent`は、手動構築のコードを自動生成するヘルパー関数です。

**Prebuilt関数自体は非推奨ではありません。** 一部の関数が`langgraph.prebuilt`から`langchain.agents`に移動しただけです。

#### `chat_agent_executor`

`chat_agent_executor`は、チャット形式のエージェントを実行するための関数です。

```python
from langgraph.prebuilt import chat_agent_executor

# エージェントの作成
agent = chat_agent_executor.create_agent(
    model=llm,
    tools=[add, multiply, divide],
    checkpointer=checkpointer  # オプション
)

# このagentも、手動で構築したグラフと同じ「エージェント（グラフ）」です
```

## エージェントの特徴

### 1. ツールの使用

エージェントは、ツールを使用してアクションを実行します。ツールは、外部のサービスやAPI、データベースなどと連携するためのインターフェースです。

```python
from langchain.tools import tool

@tool
def search_web(query: str) -> str:
    """Web検索を実行します。"""
    # 検索ロジック
    return search_results

@tool
def get_weather(city: str) -> str:
    """指定された都市の天気を取得します。"""
    # 天気取得ロジック
    return weather_data

# エージェントにツールを追加
tools = [search_web, get_weather]
llm_with_tools = llm.bind_tools(tools)
```

### 2. ループ処理

エージェントは、ツールをループ内で呼び出し、停止条件が満たされるまで処理を続けます。これにより、複雑なタスクを段階的に解決できます。

```python
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """継続条件の判定"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # ツール呼び出しがある場合は継続
    if last_message.tool_calls:
        return "tool_node"
    
    # 最大反復回数に達した場合は停止
    if len([m for m in messages if hasattr(m, "tool_calls") and m.tool_calls]) >= 10:
        return END
    
    # それ以外の場合は停止
    return END
```

### 3. 状態管理

エージェントは、`MessagesState`を使用して状態を管理します。これにより、会話の履歴やツールの実行結果を保持できます。

```python
from langgraph.graph import MessagesState
from typing import Annotated
from typing_extensions import TypedDict
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]  # メッセージ履歴
    counter: int  # カウンター
    results: list  # 結果のリスト
```

## 実装例

### 例1: 基本的な計算エージェント

```python
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from langchain.tools import tool
from typing_extensions import Literal

# ツールの定義
@tool
def calculate(expression: str) -> float:
    """数式を計算します。例: '2 + 3 * 4'"""
    try:
        return eval(expression)
    except:
        return "計算エラーが発生しました"

# エージェントの構築
tools = [calculate]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

def llm_call(state: MessagesState):
    return {
        "messages": [
            llm_with_tools.invoke(
                [SystemMessage(content="あなたは計算アシスタントです。")] + state["messages"]
            )
        ]
    }

def tool_node(state: dict):
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": result}

def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    if state["messages"][-1].tool_calls:
        return "tool_node"
    return END

# グラフの構築
graph = StateGraph(MessagesState)
graph.add_node("llm_call", llm_call)
graph.add_node("tool_node", tool_node)
graph.add_edge(START, "llm_call")
graph.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
graph.add_edge("tool_node", "llm_call")

agent = graph.compile()
```

### 例2: 検索エージェント

```python
@tool
def search_documents(query: str) -> str:
    """ドキュメントを検索します。"""
    # 検索ロジック
    return f"'{query}'に関する検索結果"

@tool
def summarize_text(text: str) -> str:
    """テキストを要約します。"""
    # 要約ロジック
    return f"要約: {text[:100]}..."

tools = [search_documents, summarize_text]
# ... エージェントの構築（上記と同様）
```

## エージェントのベストプラクティス

### 1. ツールの設計

- **単一責任の原則**: 各ツールは、1つの明確な責任を持つべきです
- **明確な説明**: ツールの説明は、LLMが適切に使用できるように明確に記述します
- **エラーハンドリング**: ツール内で適切なエラーハンドリングを実装します

```python
@tool
def get_user_info(user_id: str) -> str:
    """ユーザー情報を取得します。
    
    Args:
        user_id: ユーザーID
        
    Returns:
        ユーザー情報のJSON文字列
    """
    try:
        # ユーザー情報の取得
        user_info = fetch_user(user_id)
        return json.dumps(user_info)
    except Exception as e:
        return f"エラー: {str(e)}"
```

### 2. 停止条件の設定

エージェントが無限ループに陥らないように、適切な停止条件を設定します。

```python
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    messages = state["messages"]
    last_message = messages[-1]
    
    # ツール呼び出しがない場合は停止
    if not last_message.tool_calls:
        return END
    
    # 最大反復回数をチェック
    tool_call_count = sum(1 for m in messages if hasattr(m, "tool_calls") and m.tool_calls)
    if tool_call_count >= 10:
        return END
    
    return "tool_node"
```

### 3. エラーハンドリング

ツールの実行エラーを適切に処理し、エージェントが継続できるようにします。

```python
def tool_node(state: dict):
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        try:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
        except Exception as e:
            # エラーをメッセージとして返す
            result.append(ToolMessage(
                content=f"エラーが発生しました: {str(e)}",
                tool_call_id=tool_call["id"]
            ))
    return {"messages": result}
```

### 4. 永続化の活用

会話の履歴を保持するために、チェックポインタを使用します。

```python
from langgraph.checkpoint.memory import MemorySaver

# チェックポインタの作成
checkpointer = MemorySaver()

# エージェントにチェックポインタを追加
agent = graph.compile(checkpointer=checkpointer)

# スレッドIDを使用して実行
config = {"configurable": {"thread_id": "thread-1"}}
result = agent.invoke({"messages": [HumanMessage(content="こんにちは")]}, config=config)
```

## エージェントとワークフローの比較

| 特徴 | エージェント型 | ワークフロー型 |
|------|--------------|--------------|
| **処理フロー** | 動的 | 固定 |
| **決定論的** | いいえ | はい |
| **柔軟性** | 高い | 低い |
| **予測可能性** | 低い | 高い |
| **ツールの使用** | 必須 | オプション |
| **適用例** | チャットボット、質問応答 | データ処理、定型業務 |

## まとめ

### エージェントとは何か？

**重要な理解：**
- **エージェント = グラフ（ノード + エッジ）**
- 手動で構築したグラフも、Prebuilt関数で作成したグラフも、どちらも「エージェント」です
- 違いは「構築方法」であり、「エージェントかどうか」ではありません

### 作成方法の比較

| 方法 | メリット | デメリット | 適用例 |
|------|---------|-----------|--------|
| **手動構築** | 完全な制御、カスタマイズ性が高い | コード量が多い、開発時間がかかる | 実用化、カスタムロジックが必要 |
| **Prebuilt関数** | 開発効率が高い、コードが簡潔 | カスタマイズ性に制限 | プロトタイピング、基本的なReActエージェント |

### Prebuilt関数について

- **Prebuilt関数自体は非推奨ではありません**
- 一部の関数（`create_react_agent`など）が`langgraph.prebuilt`から`langchain.agents`に移動しただけです
- これは機能の統合であり、廃止ではありません

### エージェントの特徴

LangGraphにおけるエージェントは、以下の特徴を持ちます：

1. **ツールの使用**: エージェントは、ツールを使用してアクションを実行します
2. **ループ処理**: ツールをループ内で呼び出し、停止条件が満たされるまで処理を続けます
3. **動的な判断**: LLMが状態に基づいて次の行動を動的に決定します
4. **状態管理**: `MessagesState`を使用して状態を管理します

エージェントは、予測不可能な状況や複雑なタスクに対応するために使用されます。適切に設計することで、柔軟で強力なAIシステムを構築できます。

## 次のステップ

- [P30: Supervisor](./p30_supervisor.md): 複数のエージェントを管理するスーパーバイザー
- [P31: Swarm](./p31_swarm.md): 複数のエージェントが協調するスワーム
- [P14: Workflows + Agents](./P14_workflows_agents.md): ワークフローとエージェントの違い
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る

## 参考資料

- [公式リファレンス: Agents](https://reference.langchain.com/python/langgraph/agents/)
- [LangGraphのマルチエージェントシステム](https://qiita.com/taka_yayoi/items/f25835e123a251ab102a)
- [LangChain エージェントのドキュメント](https://docs.langchain.com/oss/python/langchain/agents)


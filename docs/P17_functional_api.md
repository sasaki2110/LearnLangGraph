# Functional API

このドキュメントでは、LangGraphの関数型API（Functional API）の使用方法について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/functional-api

## 概要

LangGraphには、グラフを構築するための2つのAPIがあります：

1. **Graph API**: オブジェクト指向スタイル（P12で使用）
2. **Functional API**: 関数型スタイル（このドキュメントで解説）

Functional APIは、**デコレータベース**のアプローチで、より簡潔にグラフを定義できます。

## Graph APIとFunctional APIの比較

### Graph API（オブジェクト指向スタイル）

```python
from langgraph.graph import StateGraph, START, END

# グラフの構築
graph = StateGraph(MessagesState)
graph.add_node("llm_call", llm_call)
graph.add_node("tool_node", tool_node)
graph.add_edge(START, "llm_call")
graph.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
graph.add_edge("tool_node", "llm_call")

agent = graph.compile()
```

### Functional API（関数型スタイル）

```python
from langgraph.graph import StateGraph

@StateGraph(MessagesState)
def agent_graph(state):
    """関数型スタイルでのグラフ定義"""
    # ノードの実行
    state = llm_call(state)
    
    # 条件分岐
    if should_continue(state) == "tool_node":
        state = tool_node(state)
        state = llm_call(state)  # 再帰的に呼び出し
    
    return state

agent = agent_graph.compile()
```

## Functional APIの基本構文

### デコレータの使用

`@StateGraph`デコレータを使用して、グラフを定義します。

```python
from langgraph.graph import StateGraph

@StateGraph(StateType)
def my_graph(state):
    """グラフ関数"""
    # ノードの実行
    state = node1(state)
    state = node2(state)
    return state
```

### ノードの実行

ノード関数を直接呼び出すことで、ノードを実行します。

```python
@StateGraph(MessagesState)
def agent_graph(state):
    # ノードの実行
    state = llm_call(state)
    state = tool_node(state)
    return state
```

### 条件分岐

通常のPythonの条件分岐を使用できます。

```python
@StateGraph(MessagesState)
def agent_graph(state):
    state = llm_call(state)
    
    # 条件分岐
    if should_continue(state) == "tool_node":
        state = tool_node(state)
        state = llm_call(state)
    
    return state
```

### ループ

Pythonのループ構文を使用できます。

```python
@StateGraph(MessagesState)
def agent_graph(state):
    # 最大3回までループ
    for _ in range(3):
        state = llm_call(state)
        
        if should_continue(state) == END:
            break
        
        state = tool_node(state)
    
    return state
```

## 実装例

### 例1: 基本的なFunctional API

```python
from langgraph.graph import StateGraph
from langchain.messages import HumanMessage, AIMessage

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

@StateGraph(MessagesState)
def agent_graph(state: MessagesState) -> MessagesState:
    """関数型スタイルでのエージェント定義"""
    
    # LLM呼び出し
    state = llm_call(state)
    
    # 条件分岐
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # ツール実行
        state = tool_node(state)
        # 再度LLM呼び出し
        state = llm_call(state)
    
    return state

# コンパイル
agent = agent_graph.compile()

# 実行
result = agent.invoke({
    "messages": [HumanMessage(content="Add 3 and 4.")],
    "llm_calls": 0
})
```

### 例2: 複雑な条件分岐

```python
@StateGraph(MessagesState)
def complex_agent_graph(state: MessagesState) -> MessagesState:
    """複雑な条件分岐を含むエージェント"""
    
    # 初期処理
    state = preprocess(state)
    
    # メインループ
    max_iterations = 5
    for i in range(max_iterations):
        state = llm_call(state)
        
        last_message = state["messages"][-1]
        
        # 条件分岐
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            state = tool_node(state)
        elif hasattr(last_message, "content") and "ERROR" in last_message.content:
            state = error_handler(state)
            break
        else:
            # 終了条件
            break
    
    # 後処理
    state = postprocess(state)
    
    return state
```

### 例3: 並列処理のシミュレーション

```python
@StateGraph(MessagesState)
def parallel_agent_graph(state: MessagesState) -> MessagesState:
    """並列処理をシミュレート"""
    
    # 複数の処理を順次実行（実際の並列処理ではない）
    results = []
    
    for task in state.get("tasks", []):
        task_state = {"messages": [HumanMessage(content=task)], "llm_calls": 0}
        task_state = llm_call(task_state)
        results.append(task_state["messages"][-1].content)
    
    # 結果を統合
    state["results"] = results
    
    return state
```

## Graph APIとFunctional APIの使い分け

### Graph APIを選ぶべき場合

1. **複雑なグラフ構造**: 多くのノードとエッジがある場合
2. **動的なグラフ構築**: 実行時にグラフを動的に構築する場合
3. **可視化**: グラフの可視化が必要な場合
4. **明示的な制御**: エッジを明示的に制御したい場合

### Functional APIを選ぶべき場合

1. **シンプルなグラフ**: 比較的シンプルなグラフ構造の場合
2. **関数型スタイル**: 関数型プログラミングを好む場合
3. **簡潔なコード**: より簡潔なコードを書きたい場合
4. **Pythonの構文**: Pythonの標準的な構文を使用したい場合

## Functional APIの利点と制限

### 利点

1. **簡潔性**: コードがより簡潔になる
2. **可読性**: Pythonの標準的な構文で読みやすい
3. **柔軟性**: 条件分岐やループを自然に記述できる
4. **デバッグ**: 通常のPythonデバッガーが使用できる

### 制限

1. **複雑なグラフ**: 非常に複雑なグラフには不向き
2. **可視化**: グラフの可視化が困難
3. **動的構築**: 実行時にグラフを動的に構築するのが困難
4. **並列処理**: 真の並列処理を表現するのが困難

## 実践的な使用例

### チャットボットの実装

```python
@StateGraph(MessagesState)
def chatbot_graph(state: MessagesState) -> MessagesState:
    """シンプルなチャットボット"""
    
    # ユーザーメッセージの処理
    state = llm_call(state)
    
    # ツールが必要な場合
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        state = tool_node(state)
        state = llm_call(state)
    
    return state

chatbot = chatbot_graph.compile()
```

### データ処理パイプライン

```python
@StateGraph(DataState)
def data_pipeline_graph(state: DataState) -> DataState:
    """データ処理パイプライン"""
    
    # 抽出
    state = extract(state)
    
    # 変換
    state = transform(state)
    
    # 検証
    if not validate(state):
        state = error_handler(state)
        return state
    
    # ロード
    state = load(state)
    
    return state

pipeline = data_pipeline_graph.compile()
```

## まとめ

Functional APIは、以下の特徴があります：

1. **簡潔性**: デコレータベースでコードが簡潔
2. **可読性**: Pythonの標準的な構文で読みやすい
3. **柔軟性**: 条件分岐やループを自然に記述できる

用途に応じて、Graph APIとFunctional APIを適切に選択することで、効率的にグラフを構築できます。

## 次のステップ

- [P18: Interrupts](./P18_interrupts.md): 人間の介入（Human-in-the-loop）
- [P19: Subgraphs](./P19_subgraphs.md): サブグラフの概念
- [P20: Memory](./P20_memory.md): メモリ管理


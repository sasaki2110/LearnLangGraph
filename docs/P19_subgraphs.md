# Subgraphs

このドキュメントでは、LangGraphにおけるサブグラフ（Subgraphs）の概念と使用方法について解説します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/use-subgraphs

## 概要

サブグラフ（Subgraphs）は、**グラフ内にネストされた別のグラフ**です。これにより、以下のことが可能になります：

1. **モジュール化**: 複雑なグラフを小さな単位に分割
2. **再利用性**: 同じサブグラフを複数の場所で使用
3. **保守性**: 各部分を独立して管理・テストできる
4. **可読性**: グラフの構造が明確になる

## サブグラフの基本概念

### サブグラフとは

サブグラフは、**独立したグラフ**として定義され、**親グラフのノードとして使用**されます。

```
親グラフ
  ├─ ノードA
  ├─ サブグラフ（子グラフ）
  │    ├─ ノード1
  │    ├─ ノード2
  │    └─ ノード3
  └─ ノードB
```

### サブグラフの利点

1. **モジュール化**: 機能ごとに分割できる
2. **再利用性**: 同じサブグラフを複数回使用できる
3. **テスト**: サブグラフを個別にテストできる
4. **保守性**: 変更の影響範囲が限定的

## 基本的な使用方法

### サブグラフの定義

サブグラフは、通常のグラフと同様に定義します。

```python
from langgraph.graph import StateGraph, START, END

# サブグラフの定義
def create_subgraph():
    """サブグラフを作成"""
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("node1", node1_function)
    subgraph.add_node("node2", node2_function)
    subgraph.add_edge(START, "node1")
    subgraph.add_edge("node1", "node2")
    subgraph.add_edge("node2", END)
    return subgraph.compile()

# 親グラフでの使用
parent_graph = StateGraph(MessagesState)
parent_graph.add_node("subgraph", create_subgraph())
parent_graph.add_node("other_node", other_node_function)
parent_graph.add_edge(START, "subgraph")
parent_graph.add_edge("subgraph", "other_node")
parent_graph.add_edge("other_node", END)
```

## 実装例

### 例1: 基本的なサブグラフ

```python
from langgraph.graph import StateGraph, START, END

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# サブグラフ1: データ前処理
def create_preprocessing_subgraph():
    """前処理サブグラフ"""
    subgraph = StateGraph(MessagesState)
    
    def clean_data(state: MessagesState) -> dict:
        """データのクリーニング"""
        cleaned = clean(state["messages"])
        return {"messages": [AIMessage(content=cleaned)]}
    
    def validate_data(state: MessagesState) -> dict:
        """データの検証"""
        validated = validate(state["messages"])
        return {"messages": [AIMessage(content=validated)]}
    
    subgraph.add_node("clean_data", clean_data)
    subgraph.add_node("validate_data", validate_data)
    subgraph.add_edge(START, "clean_data")
    subgraph.add_edge("clean_data", "validate_data")
    subgraph.add_edge("validate_data", END)
    
    return subgraph.compile()

# サブグラフ2: データ処理
def create_processing_subgraph():
    """処理サブグラフ"""
    subgraph = StateGraph(MessagesState)
    
    def process_data(state: MessagesState) -> dict:
        """データの処理"""
        processed = process(state["messages"])
        return {"messages": [AIMessage(content=processed)]}
    
    subgraph.add_node("process_data", process_data)
    subgraph.add_edge(START, "process_data")
    subgraph.add_edge("process_data", END)
    
    return subgraph.compile()

# 親グラフの構築
def create_main_graph():
    """メイングラフ"""
    main_graph = StateGraph(MessagesState)
    
    # サブグラフをノードとして追加
    main_graph.add_node("preprocessing", create_preprocessing_subgraph())
    main_graph.add_node("processing", create_processing_subgraph())
    main_graph.add_node("postprocessing", postprocessing_function)
    
    # エッジの設定
    main_graph.add_edge(START, "preprocessing")
    main_graph.add_edge("preprocessing", "processing")
    main_graph.add_edge("processing", "postprocessing")
    main_graph.add_edge("postprocessing", END)
    
    return main_graph.compile()

# 実行
main_agent = create_main_graph()
result = main_agent.invoke({"messages": [HumanMessage(content="Process data")]})
```

### 例2: 再利用可能なサブグラフ

```python
# 共通のサブグラフ: LLM呼び出しループ
def create_llm_loop_subgraph():
    """LLM呼び出しループのサブグラフ（再利用可能）"""
    subgraph = StateGraph(MessagesState)
    
    def llm_call(state: MessagesState) -> dict:
        """LLM呼び出し"""
        response = model.invoke(state["messages"])
        return {"messages": [response]}
    
    def should_continue(state: MessagesState) -> Literal["tool_node", END]:
        """継続判定"""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tool_node"
        return END
    
    def tool_node(state: MessagesState) -> dict:
        """ツール実行"""
        results = execute_tools(state)
        return {"messages": results}
    
    subgraph.add_node("llm_call", llm_call)
    subgraph.add_node("tool_node", tool_node)
    subgraph.add_edge(START, "llm_call")
    subgraph.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    subgraph.add_edge("tool_node", "llm_call")
    
    return subgraph.compile()

# 複数の親グラフで使用
def create_agent1():
    """エージェント1"""
    graph = StateGraph(MessagesState)
    graph.add_node("llm_loop", create_llm_loop_subgraph())  # 再利用
    graph.add_node("finalize", finalize_function)
    graph.add_edge(START, "llm_loop")
    graph.add_edge("llm_loop", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()

def create_agent2():
    """エージェント2"""
    graph = StateGraph(MessagesState)
    graph.add_node("preprocess", preprocess_function)
    graph.add_node("llm_loop", create_llm_loop_subgraph())  # 再利用
    graph.add_node("postprocess", postprocess_function)
    graph.add_edge(START, "preprocess")
    graph.add_edge("preprocess", "llm_loop")
    graph.add_edge("llm_loop", "postprocess")
    graph.add_edge("postprocess", END)
    return graph.compile()
```

### 例3: ネストされたサブグラフ

```python
# レベル1のサブグラフ
def create_level1_subgraph():
    """レベル1のサブグラフ"""
    subgraph = StateGraph(MessagesState)
    
    # レベル2のサブグラフを含む
    def create_level2_subgraph():
        """レベル2のサブグラフ"""
        subgraph2 = StateGraph(MessagesState)
        subgraph2.add_node("node_a", node_a_function)
        subgraph2.add_node("node_b", node_b_function)
        subgraph2.add_edge(START, "node_a")
        subgraph2.add_edge("node_a", "node_b")
        subgraph2.add_edge("node_b", END)
        return subgraph2.compile()
    
    subgraph.add_node("level2", create_level2_subgraph())
    subgraph.add_node("level1_node", level1_node_function)
    subgraph.add_edge(START, "level2")
    subgraph.add_edge("level2", "level1_node")
    subgraph.add_edge("level1_node", END)
    
    return subgraph.compile()

# 親グラフ
def create_parent_graph():
    """親グラフ"""
    graph = StateGraph(MessagesState)
    graph.add_node("level1", create_level1_subgraph())
    graph.add_node("parent_node", parent_node_function)
    graph.add_edge(START, "level1")
    graph.add_edge("level1", "parent_node")
    graph.add_edge("parent_node", END)
    return graph.compile()
```

## サブグラフの状態管理

### 状態の共有

サブグラフは、親グラフと同じ状態型を使用します。

```python
# 親グラフとサブグラフで同じ状態型を使用
class SharedState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    counter: int

# サブグラフ
def create_subgraph():
    subgraph = StateGraph(SharedState)  # 同じ状態型
    # ...
    return subgraph.compile()

# 親グラフ
def create_parent_graph():
    parent = StateGraph(SharedState)  # 同じ状態型
    parent.add_node("subgraph", create_subgraph())
    # ...
    return parent.compile()
```

### 状態の分離

必要に応じて、サブグラフ専用の状態型を定義することも可能です。

```python
# サブグラフ専用の状態
class SubgraphState(TypedDict):
    data: list
    processed: bool

# 親グラフの状態
class ParentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    subgraph_result: dict

# 状態の変換関数
def convert_to_subgraph_state(parent_state: ParentState) -> SubgraphState:
    """親グラフの状態をサブグラフの状態に変換"""
    return {
        "data": extract_data(parent_state["messages"]),
        "processed": False
    }

def convert_from_subgraph_state(subgraph_state: SubgraphState) -> dict:
    """サブグラフの状態を親グラフの状態に変換"""
    return {
        "subgraph_result": subgraph_state
    }
```

## サブグラフのベストプラクティス

### 1. 明確な責任の分離

各サブグラフは、明確な責任を持つべきです。

```python
# 良い例: 明確な責任
def create_data_processing_subgraph():
    """データ処理専用のサブグラフ"""
    # データ処理のみを行う
    pass

# 悪い例: 複数の責任
def create_mixed_subgraph():
    """複数の責任を持つサブグラフ（避けるべき）"""
    # データ処理、LLM呼び出し、ツール実行など
    pass
```

### 2. 再利用性の考慮

共通の処理は、サブグラフとして定義し、再利用します。

```python
# 再利用可能なサブグラフ
def create_common_llm_loop():
    """共通のLLMループ（複数のグラフで使用）"""
    # ...
    return subgraph.compile()

# 複数のグラフで使用
graph1.add_node("llm_loop", create_common_llm_loop())
graph2.add_node("llm_loop", create_common_llm_loop())
```

### 3. テストの容易さ

サブグラフは、個別にテストできるように設計します。

```python
# サブグラフのテスト
def test_subgraph():
    """サブグラフのテスト"""
    subgraph = create_subgraph()
    result = subgraph.invoke(initial_state)
    assert result["processed"] == True

# 親グラフのテスト
def test_parent_graph():
    """親グラフのテスト"""
    parent = create_parent_graph()
    result = parent.invoke(initial_state)
    assert "subgraph_result" in result
```

## まとめ

サブグラフにより、以下のことが可能になります：

1. **モジュール化**: 複雑なグラフを小さな単位に分割
2. **再利用性**: 同じサブグラフを複数の場所で使用
3. **保守性**: 各部分を独立して管理・テストできる
4. **可読性**: グラフの構造が明確になる

適切にサブグラフを使用することで、より保守性が高く、拡張性のあるグラフを構築できます。

## 次のステップ

- [P20: Memory](./P20_memory.md): メモリ管理
- [P21: Durable Execution](./P21_durable_execution.md): 長時間実行の管理
- [P00: Roadmap](./P00_roadmap.md): 学習ロードマップに戻る


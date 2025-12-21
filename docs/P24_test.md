# Testing

このドキュメントでは、LangGraphアプリケーションのテスト方法について解説します。ユニットテスト、統合テスト、モックとフィクスチャの活用方法を説明します。

公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/test

## 概要

LangGraphアプリケーションのテストは、アプリケーションの品質を保証し、リグレッションを防ぐために重要です。適切なテスト戦略により、以下の利点が得られます：

- **品質保証**: 各コンポーネントが期待通りに動作することを確認
- **リグレッション防止**: 変更による既存機能の破壊を早期に発見
- **ドキュメント化**: テストコードがアプリケーションの使用方法を示す
- **リファクタリングの安全性**: 変更を加えても既存の動作が保証される

LangGraphアプリケーションのテストには、以下の種類があります：

1. **ユニットテスト**: 個別のノードやツールのテスト
2. **統合テスト**: グラフ全体の実行フローのテスト
3. **部分実行テスト**: グラフの特定の部分のみを実行するテスト

## 前提条件

### pytestのインストール

LangGraphのテストには、`pytest`を使用します。

```bash
pip install -U pytest
```

### テスト用の依存関係

テストに必要な追加のパッケージをインストールします。

```bash
pip install pytest pytest-asyncio pytest-mock
```

`requirements.txt`に追加する場合：

```txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0
```

## 基本的なテスト

### グラフの実行テスト

最も基本的なテストは、グラフ全体を実行して結果を検証することです。

```python
import pytest
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

def create_graph() -> StateGraph:
    """テスト用のグラフを作成"""
    class MyState(TypedDict):
        my_key: str
    
    graph = StateGraph(MyState)
    graph.add_node("node1", lambda state: {"my_key": "hello from node1"})
    graph.add_node("node2", lambda state: {"my_key": "hello from node2"})
    graph.add_edge(START, "node1")
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", END)
    return graph

def test_basic_agent_execution() -> None:
    """基本的なグラフ実行のテスト"""
    checkpointer = MemorySaver()
    graph = create_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    result = compiled_graph.invoke(
        {"my_key": "initial_value"},
        config={"configurable": {"thread_id": "1"}}
    )
    
    assert result["my_key"] == "hello from node2"
```

### テストのベストプラクティス

1. **各テストで新しいチェックポインタを使用**: テスト間で状態が干渉しないようにする
2. **一意のthread_idを使用**: 各テストで異なるthread_idを使用する
3. **グラフをテストごとに作成**: テスト間でグラフの状態が共有されないようにする

```python
@pytest.fixture
def checkpointer():
    """テスト用のチェックポインタフィクスチャ"""
    return MemorySaver()

@pytest.fixture
def graph():
    """テスト用のグラフフィクスチャ"""
    return create_graph()

def test_basic_agent_execution(checkpointer, graph):
    """フィクスチャを使用したテスト"""
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    result = compiled_graph.invoke(
        {"my_key": "initial_value"},
        config={"configurable": {"thread_id": "test-1"}}
    )
    
    assert result["my_key"] == "hello from node2"
```

## 個別ノードとエッジのテスト

### 個別ノードのテスト

コンパイル済みのグラフは、`graph.nodes`を通じて個別のノードにアクセスできます。これにより、ノードを個別にテストできます。

**注意**: 個別ノードのテストでは、チェックポインタは使用されません。

```python
def test_individual_node_execution() -> None:
    """個別ノードの実行テスト"""
    checkpointer = MemorySaver()
    graph = create_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    # node1のみを実行
    result = compiled_graph.nodes["node1"].invoke(
        {"my_key": "initial_value"}
    )
    
    assert result["my_key"] == "hello from node1"
```

### 複数のノードを順番にテスト

複数のノードを順番に実行して、状態の遷移をテストできます。

```python
def test_multiple_nodes_sequential() -> None:
    """複数のノードを順番に実行するテスト"""
    graph = create_graph()
    compiled_graph = graph.compile()
    
    state = {"my_key": "initial_value"}
    
    # node1を実行
    state = compiled_graph.nodes["node1"].invoke(state)
    assert state["my_key"] == "hello from node1"
    
    # node2を実行
    state = compiled_graph.nodes["node2"].invoke(state)
    assert state["my_key"] == "hello from node2"
```

### 条件付きエッジのテスト

条件付きエッジの動作をテストするには、異なる状態でノードを実行し、エッジの選択を検証します。

```python
def create_graph_with_conditional_edge() -> StateGraph:
    """条件付きエッジを持つグラフを作成"""
    class MyState(TypedDict):
        value: int
        path: str
    
    def should_continue(state: MyState) -> str:
        if state["value"] > 10:
            return "high"
        return "low"
    
    graph = StateGraph(MyState)
    graph.add_node("start", lambda state: {"value": state.get("value", 0)})
    graph.add_node("high_path", lambda state: {"path": "high"})
    graph.add_node("low_path", lambda state: {"path": "low"})
    
    graph.add_edge(START, "start")
    graph.add_conditional_edges(
        "start",
        should_continue,
        {"high": "high_path", "low": "low_path"}
    )
    graph.add_edge("high_path", END)
    graph.add_edge("low_path", END)
    
    return graph

def test_conditional_edge_high() -> None:
    """条件付きエッジ（high）のテスト"""
    graph = create_graph_with_conditional_edge()
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({"value": 15})
    assert result["path"] == "high"

def test_conditional_edge_low() -> None:
    """条件付きエッジ（low）のテスト"""
    graph = create_graph_with_conditional_edge()
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({"value": 5})
    assert result["path"] == "low"
```

## 部分実行のテスト

大きなグラフでは、全体を実行せずに特定の部分のみをテストしたい場合があります。LangGraphの永続化メカニズムを使用して、特定のノードから開始し、特定のノードで停止するテストを実装できます。

### 部分実行の手順

1. チェックポインタ付きでグラフをコンパイル
2. `update_state`メソッドを使用して、開始したいノードの**前**のノードの状態を設定
3. `interrupt_after`パラメータを使用して、停止したいノードの**後**で実行を停止

```python
def test_partial_execution_from_node2_to_node3() -> None:
    """node2からnode3までの部分実行テスト"""
    checkpointer = MemorySaver()
    graph = create_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    # node1の終了状態をシミュレート
    # これにより、実行はnode2から開始される
    compiled_graph.update_state(
        config={
            "configurable": {
                "thread_id": "1"
            }
        },
        # node1の終了時の状態
        values={"my_key": "initial_value"},
        # node1の終了時点として状態を設定
        as_node="node1",
    )
    
    # node2から開始し、node3の後で停止
    result = compiled_graph.invoke(
        None,  # 状態は既に設定されているためNone
        config={"configurable": {"thread_id": "1"}},
        interrupt_after="node3",  # node3の後で停止
    )
    
    assert result["my_key"] == "hello from node3"
```

### 部分実行の使用例

複雑なグラフで、特定の処理フローのみをテストする場合に便利です。

```python
def create_complex_graph() -> StateGraph:
    """複雑なグラフを作成"""
    class MyState(TypedDict):
        step: str
        data: dict
    
    graph = StateGraph(MyState)
    
    graph.add_node("preprocess", lambda s: {"step": "preprocessed"})
    graph.add_node("validate", lambda s: {"step": "validated"})
    graph.add_node("process", lambda s: {"step": "processed"})
    graph.add_node("postprocess", lambda s: {"step": "postprocessed"})
    graph.add_node("finalize", lambda s: {"step": "finalized"})
    
    graph.add_edge(START, "preprocess")
    graph.add_edge("preprocess", "validate")
    graph.add_edge("validate", "process")
    graph.add_edge("process", "postprocess")
    graph.add_edge("postprocess", "finalize")
    graph.add_edge("finalize", END)
    
    return graph

def test_processing_pipeline_only() -> None:
    """processノードのみをテスト"""
    checkpointer = MemorySaver()
    graph = create_complex_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    # validateの終了状態をシミュレート
    compiled_graph.update_state(
        config={"configurable": {"thread_id": "1"}},
        values={"step": "validated", "data": {"input": "test"}},
        as_node="validate",
    )
    
    # processノードのみを実行
    result = compiled_graph.invoke(
        None,
        config={"configurable": {"thread_id": "1"}},
        interrupt_after="process",
    )
    
    assert result["step"] == "processed"
```

## モックとフィクスチャの活用

### LLMのモック

LLM呼び出しをモックして、テストを高速化し、外部依存を排除します。

```python
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage

def test_agent_with_mocked_llm():
    """LLMをモックしたエージェントのテスト"""
    from langchain_openai import ChatOpenAI
    
    # LLMのモックを作成
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="Mocked response")
    
    # LLMを使用するノードを定義
    def llm_node(state):
        messages = state.get("messages", [])
        response = mock_llm.invoke(messages)
        return {"messages": messages + [response]}
    
    class MyState(TypedDict):
        messages: list
    
    graph = StateGraph(MyState)
    graph.add_node("llm", llm_node)
    graph.add_edge(START, "llm")
    graph.add_edge("llm", END)
    
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({
        "messages": [HumanMessage(content="Hello")]
    })
    
    assert len(result["messages"]) == 2
    assert result["messages"][-1].content == "Mocked response"
    mock_llm.invoke.assert_called_once()
```

### ツールのモック

外部APIやデータベースへのアクセスをモックします。

```python
from unittest.mock import Mock, patch

def test_agent_with_mocked_tool():
    """ツールをモックしたエージェントのテスト"""
    
    # ツールのモック
    mock_search = Mock(return_value="Mocked search result")
    
    def search_node(state):
        query = state.get("query", "")
        result = mock_search(query)
        return {"result": result}
    
    class MyState(TypedDict):
        query: str
        result: str
    
    graph = StateGraph(MyState)
    graph.add_node("search", search_node)
    graph.add_edge(START, "search")
    graph.add_edge("search", END)
    
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({"query": "test query"})
    
    assert result["result"] == "Mocked search result"
    mock_search.assert_called_once_with("test query")
```

### pytestフィクスチャの使用

再利用可能なテストコンポーネントをフィクスチャとして定義します。

```python
import pytest
from langgraph.checkpoint.memory import MemorySaver

@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()

@pytest.fixture
def graph():
    """グラフフィクスチャ"""
    return create_graph()

@pytest.fixture
def compiled_graph(checkpointer, graph):
    """コンパイル済みグラフフィクスチャ"""
    return graph.compile(checkpointer=checkpointer)

def test_with_fixtures(compiled_graph):
    """フィクスチャを使用したテスト"""
    result = compiled_graph.invoke(
        {"my_key": "initial_value"},
        config={"configurable": {"thread_id": "fixture-test"}}
    )
    
    assert result["my_key"] == "hello from node2"
```

### モックレスポンスのフィクスチャ

状態に基づいて異なるモックレスポンスを返すフィクスチャを作成します。

```python
@pytest.fixture
def mock_llm_responses():
    """状態に基づくLLMレスポンスのモック"""
    responses = {
        "greeting": "Hello! How can I help you?",
        "question": "I can answer that question.",
        "goodbye": "Goodbye! Have a nice day!"
    }
    
    def get_response(state):
        intent = state.get("intent", "greeting")
        return responses.get(intent, "I don't understand.")
    
    return get_response

def test_agent_with_state_based_mock(mock_llm_responses):
    """状態ベースのモックを使用したテスト"""
    def llm_node(state):
        response = mock_llm_responses(state)
        return {"response": response}
    
    class MyState(TypedDict):
        intent: str
        response: str
    
    graph = StateGraph(MyState)
    graph.add_node("llm", llm_node)
    graph.add_edge(START, "llm")
    graph.add_edge("llm", END)
    
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({"intent": "question"})
    assert result["response"] == "I can answer that question."
```

## 統合テスト

### エンドツーエンドのテスト

グラフ全体を実行し、実際のシナリオをテストします。

```python
def test_end_to_end_workflow():
    """エンドツーエンドのワークフローテスト"""
    checkpointer = MemorySaver()
    graph = create_complex_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    # 初期状態
    initial_state = {
        "step": "initial",
        "data": {"input": "test data"}
    }
    
    # グラフ全体を実行
    result = compiled_graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": "e2e-test"}}
    )
    
    # 最終状態を検証
    assert result["step"] == "finalized"
    assert "data" in result
```

### 複数ステップのテスト

複数のステップにわたる会話やワークフローをテストします。

```python
def test_multi_step_conversation():
    """複数ステップの会話テスト"""
    checkpointer = MemorySaver()
    graph = create_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    thread_id = "conversation-test"
    config = {"configurable": {"thread_id": thread_id}}
    
    # ステップ1
    result1 = compiled_graph.invoke(
        {"my_key": "step1"},
        config=config
    )
    assert result1["my_key"] == "hello from node2"
    
    # ステップ2（同じthread_idで続行）
    result2 = compiled_graph.invoke(
        {"my_key": "step2"},
        config=config
    )
    assert result2["my_key"] == "hello from node2"
```

## エラーハンドリングのテスト

### 例外処理のテスト

ノードで発生する可能性のあるエラーをテストします。

```python
def create_graph_with_error_handling() -> StateGraph:
    """エラーハンドリングを含むグラフ"""
    class MyState(TypedDict):
        value: int
        error: str
    
    def risky_node(state):
        value = state.get("value", 0)
        if value < 0:
            raise ValueError("Value cannot be negative")
        return {"value": value * 2}
    
    def error_handler_node(state):
        return {"error": "Error occurred"}
    
    graph = StateGraph(MyState)
    graph.add_node("risky", risky_node)
    graph.add_node("error_handler", error_handler_node)
    
    graph.add_edge(START, "risky")
    # エラー時はerror_handlerへ
    graph.add_edge("risky", "error_handler")
    graph.add_edge("error_handler", END)
    
    return graph

def test_error_handling():
    """エラーハンドリングのテスト"""
    graph = create_graph_with_error_handling()
    compiled_graph = graph.compile()
    
    # 正常ケース
    result1 = compiled_graph.invoke({"value": 5})
    assert result1["value"] == 10
    
    # エラーケース
    with pytest.raises(ValueError):
        compiled_graph.invoke({"value": -1})
```

## 非同期テスト

### 非同期グラフのテスト

非同期ノードを含むグラフをテストします。

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_graph():
    """非同期グラフのテスト"""
    async def async_node(state):
        await asyncio.sleep(0.1)  # 非同期処理をシミュレート
        return {"result": "async completed"}
    
    class MyState(TypedDict):
        result: str
    
    graph = StateGraph(MyState)
    graph.add_node("async", async_node)
    graph.add_edge(START, "async")
    graph.add_edge("async", END)
    
    compiled_graph = graph.compile()
    
    result = await compiled_graph.ainvoke({"result": ""})
    assert result["result"] == "async completed"
```

## テストの組織化

### テストディレクトリ構造

プロジェクトのテストを整理するための推奨構造：

```
my-app/
├── my_agent/
│   ├── agent.py
│   └── utils/
│       ├── nodes.py
│       └── tools.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # 共通フィクスチャ
│   ├── test_nodes.py        # ノードのユニットテスト
│   ├── test_tools.py        # ツールのユニットテスト
│   ├── test_graph.py        # グラフの統合テスト
│   └── test_integration.py   # エンドツーエンドテスト
├── requirements.txt
└── pytest.ini               # pytest設定
```

### conftest.pyの例

共通のフィクスチャを`conftest.py`に定義します。

```python
# tests/conftest.py
import pytest
from langgraph.checkpoint.memory import MemorySaver
from my_agent.agent import create_graph

@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()

@pytest.fixture
def graph():
    """グラフフィクスチャ"""
    return create_graph()

@pytest.fixture
def compiled_graph(checkpointer, graph):
    """コンパイル済みグラフフィクスチャ"""
    return graph.compile(checkpointer=checkpointer)
```

### pytest.iniの設定

`pytest.ini`でテストの設定を行います。

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

## テストの実行

### すべてのテストを実行

```bash
pytest
```

### 特定のテストファイルを実行

```bash
pytest tests/test_nodes.py
```

### 特定のテスト関数を実行

```bash
pytest tests/test_nodes.py::test_individual_node_execution
```

### マーカーでフィルタリング

```bash
# ユニットテストのみ実行
pytest -m unit

# 統合テストのみ実行
pytest -m integration

# スローテストをスキップ
pytest -m "not slow"
```

### カバレッジレポートの生成

```bash
pip install pytest-cov
pytest --cov=my_agent --cov-report=html
```

## ベストプラクティス

### 1. テストの独立性

各テストは独立して実行できるようにします。

```python
def test_independent_1(checkpointer):
    """独立したテスト1"""
    graph = create_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    # テスト実行...

def test_independent_2(checkpointer):
    """独立したテスト2"""
    graph = create_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    # テスト実行...
```

### 2. 明確なアサーション

テストの意図が明確になるようにアサーションを書きます。

```python
def test_clear_assertions():
    """明確なアサーションの例"""
    result = compiled_graph.invoke({"input": "test"})
    
    # 良い例: 明確なアサーション
    assert result["output"] == "expected_output", \
        f"Expected 'expected_output', got '{result['output']}'"
    
    # 悪い例: 不明確
    assert result
```

### 3. テストデータの分離

テストデータをコードから分離します。

```python
# tests/test_data.py
TEST_CASES = [
    {"input": "case1", "expected": "output1"},
    {"input": "case2", "expected": "output2"},
]

# tests/test_graph.py
@pytest.mark.parametrize("test_case", TEST_CASES)
def test_multiple_cases(test_case, compiled_graph):
    """パラメータ化されたテスト"""
    result = compiled_graph.invoke({"input": test_case["input"]})
    assert result["output"] == test_case["expected"]
```

### 4. モックの適切な使用

外部依存をモックして、テストを高速化し、再現性を確保します。

```python
@patch('my_agent.utils.tools.external_api_call')
def test_with_mock(mock_api):
    """モックを使用したテスト"""
    mock_api.return_value = "mocked_response"
    # テスト実行...
```

### 5. エッジケースのテスト

正常ケースだけでなく、エッジケースもテストします。

```python
def test_edge_cases():
    """エッジケースのテスト"""
    # 空の入力
    result1 = compiled_graph.invoke({})
    assert result1 is not None
    
    # 非常に大きな入力
    large_input = {"data": "x" * 10000}
    result2 = compiled_graph.invoke(large_input)
    assert result2 is not None
    
    # None値
    result3 = compiled_graph.invoke({"data": None})
    assert result3 is not None
```

## まとめ

LangGraphアプリケーションのテストには：

- ✅ **ユニットテスト**: 個別のノードやツールをテスト
- ✅ **統合テスト**: グラフ全体の実行フローをテスト
- ✅ **部分実行テスト**: 特定の部分のみをテスト
- ✅ **モックとフィクスチャ**: 外部依存を排除し、テストを高速化
- ✅ **エラーハンドリング**: エッジケースを含む包括的なテスト

適切なテスト戦略により、品質の高いLangGraphアプリケーションを構築・保守できます。

## 参考資料

- [公式ドキュメント: Test](https://docs.langchain.com/oss/python/langgraph/test)
- [pytest公式ドキュメント](https://docs.pytest.org/)
- [LangChain Testing Guide](https://python.langchain.com/docs/contributing/how_to/testing/)

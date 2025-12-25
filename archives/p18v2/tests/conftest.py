"""
共通フィクスチャ
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import node_a, node_b, node_c


@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()


@pytest.fixture
def config():
    """RunnableConfigフィクスチャ"""
    return RunnableConfig(configurable={"thread_id": "test-thread-1"})


@pytest.fixture
def initial_state():
    """初期状態フィクスチャ"""
    return {
        "messages": [],
        "approved": False,
        "action": ""
    }


@pytest.fixture
def graph_with_checkpointer(checkpointer):
    """チェックポインター付きグラフフィクスチャ（テスト用）"""
    # グラフの構築
    workflow = StateGraph(State)
    workflow.add_node("node_a", node_a)
    workflow.add_node("node_b", node_b)
    workflow.add_node("node_c", node_c)
    
    # エッジの追加: nodeA → nodeB → nodeC
    workflow.add_edge(START, "node_a")
    workflow.add_edge("node_a", "node_b")
    workflow.add_edge("node_b", "node_c")
    workflow.add_edge("node_c", END)
    
    # チェックポインターを指定してコンパイル（テスト用）
    return workflow.compile(checkpointer=checkpointer)


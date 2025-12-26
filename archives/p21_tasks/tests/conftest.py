"""
共通フィクスチャ
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import call_api


@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()


@pytest.fixture
def graph_with_checkpointer(checkpointer):
    """チェックポインタ付きグラフフィクスチャ"""
    # グラフの構築
    builder = StateGraph(State)
    builder.add_node("call_api", call_api)
    builder.add_edge(START, "call_api")
    builder.add_edge("call_api", END)
    
    # チェックポインタを指定してコンパイル
    return builder.compile(checkpointer=checkpointer)


"""
共通フィクスチャ
"""
import pytest
import uuid
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import generate_topic, write_message


@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()


@pytest.fixture
def config():
    """RunnableConfigフィクスチャ"""
    return RunnableConfig(configurable={"thread_id": str(uuid.uuid4())})


@pytest.fixture
def initial_state():
    """初期状態フィクスチャ"""
    return {
        "steps": []
    }


@pytest.fixture
def graph_with_checkpointer(checkpointer):
    """チェックポインター付きグラフフィクスチャ（テスト用）"""
    # グラフの構築
    workflow = StateGraph(State)
    workflow.add_node("generate_topic", generate_topic)
    workflow.add_node("write_message", write_message)
    
    # エッジの追加: generate_topic → write_message
    workflow.add_edge(START, "generate_topic")
    workflow.add_edge("generate_topic", "write_message")
    workflow.add_edge("write_message", END)
    
    # チェックポインターを指定してコンパイル（テスト用）
    return workflow.compile(checkpointer=checkpointer)


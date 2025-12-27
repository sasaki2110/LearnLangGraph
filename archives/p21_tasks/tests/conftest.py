"""
共通フィクスチャ
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import call_api, process_with_different_tasks
from my_agent.utils.logging_config import setup_logging, get_log_level

# テスト実行時にロギングを初期化
log_level = get_log_level()
setup_logging(log_level=log_level, initialize=True)


@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()


@pytest.fixture
def graph_with_checkpointer(checkpointer):
    """チェックポインタ付きグラフフィクスチャ"""
    # グラフの構築（agent.pyと同じ構造）
    builder = StateGraph(State)
    builder.add_node("call_api", call_api)
    builder.add_node("process_with_different_tasks", process_with_different_tasks)
    
    # エッジの追加（順序を逆にする）
    builder.add_edge(START, "process_with_different_tasks")
    builder.add_edge("process_with_different_tasks", "call_api")
    builder.add_edge("call_api", END)
    
    # チェックポインタを指定してコンパイル
    return builder.compile(checkpointer=checkpointer)


"""
共通フィクスチャ
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver
from my_agent.agent import graph


@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()


@pytest.fixture
def graph_with_checkpointer(checkpointer):
    """チェックポインタ付きグラフフィクスチャ"""
    # グラフを再コンパイルしてチェックポインタを追加
    from langgraph.graph import StateGraph, START, END
    from my_agent.utils.state import State
    from my_agent.utils.nodes import (
        task_planner,
        task_executor,
        result_synthesizer,
        assign_tasks
    )
    
    # グラフの構築
    builder = StateGraph(State)
    builder.add_node("task_planner", task_planner)
    builder.add_node("task_executor", task_executor)
    builder.add_node("result_synthesizer", result_synthesizer)
    
    # エッジの追加
    builder.add_edge(START, "task_planner")
    builder.add_conditional_edges(
        "task_planner",
        assign_tasks,
        ["task_executor"]
    )
    builder.add_edge("task_executor", "result_synthesizer")
    builder.add_edge("result_synthesizer", END)
    
    # チェックポインタを指定してコンパイル
    return builder.compile(checkpointer=checkpointer)


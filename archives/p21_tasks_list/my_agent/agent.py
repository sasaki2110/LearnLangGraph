"""
タスクリスト提案機能を持つエージェントのグラフ定義
"""
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

# ノードの追加
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

# グラフをコンパイル
graph = builder.compile()


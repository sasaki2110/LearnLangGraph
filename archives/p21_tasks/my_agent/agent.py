"""
タスクを使用したエージェントのグラフ定義
"""
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import call_api, process_with_different_tasks

# グラフの構築
builder = StateGraph(State)

# ノードの追加
builder.add_node("call_api", call_api)
builder.add_node("process_with_different_tasks", process_with_different_tasks)

# エッジの追加（順序を逆にする）
builder.add_edge(START, "process_with_different_tasks")
builder.add_edge("process_with_different_tasks", "call_api")
builder.add_edge("call_api", END)

# コンパイルしてモジュールレベルの変数に代入
# LangGraph APIでは永続化が自動的に処理されるため、チェックポインタは不要
# テストでは別途チェックポインタを設定する
graph = builder.compile()


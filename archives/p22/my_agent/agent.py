"""
P22: タイムトラベル（Time Travel）の例 - グラフ定義

LangSmith studioで実行する前提で、graphのコンパイルまでを実装しています。
invoke以降の処理はUIに任せます。

注意: LangGraph API（LangSmith studio）では、persistenceは自動的に処理されるため、
チェックポインターを明示的に指定する必要はありません。
"""
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import generate_topic, write_message

# グラフの構築
workflow = StateGraph(State)
workflow.add_node("generate_topic", generate_topic)
workflow.add_node("write_message", write_message)

# エッジの追加: generate_topic → write_message
workflow.add_edge(START, "generate_topic")
workflow.add_edge("generate_topic", "write_message")
workflow.add_edge("write_message", END)

# コンパイルしてモジュールレベルの変数に代入
# langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
# 注意: LangGraph APIでは、persistenceは自動的に処理されるため、
# チェックポインターを指定する必要はありません
graph = workflow.compile()


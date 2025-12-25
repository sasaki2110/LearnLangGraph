"""
P18v2: 基本的な中断（Interrupts）の例 - グラフ定義

LangSmith studioで実行する前提で、graphのコンパイルまでを実装しています。
invoke以降の処理はUIに任せます。

注意: LangGraph API（LangSmith studio）では、persistenceは自動的に処理されるため、
チェックポインターを明示的に指定する必要はありません。
"""
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import node_a, node_b, node_c

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

# コンパイルしてモジュールレベルの変数に代入
# langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
# 注意: LangGraph APIでは、persistenceは自動的に処理されるため、
# チェックポインターを指定する必要はありません
graph = workflow.compile()


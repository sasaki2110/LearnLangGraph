"""
条件付きエッジのテスト
"""
import pytest
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from unittest.mock import Mock
from langchain_core.messages import HumanMessage, AIMessage
from my_agent.utils.nodes import should_continue
from my_agent.utils.state import MessagesState


def create_graph_with_conditional_edge() -> StateGraph:
    """条件付きエッジを持つグラフを作成（LLMモック）"""
    # カスタム状態定義（valueフィールドを追加）
    class ConditionalState(TypedDict):
        messages: list
        llm_calls: int
        value: int
    
    # モックLLMを作成
    mock_llm = Mock()
    
    def llm_call_high(state: ConditionalState):
        """高値の場合のLLM呼び出し"""
        mock_llm.invoke.return_value = AIMessage(
            content="High value detected",
            tool_calls=[]  # ツール呼び出しなし
        )
        return {
            "messages": [mock_llm.invoke(state["messages"])],
            "llm_calls": state.get("llm_calls", 0) + 1
        }
    
    def llm_call_low(state: ConditionalState):
        """低値の場合のLLM呼び出し"""
        mock_llm.invoke.return_value = AIMessage(
            content="Low value detected",
            tool_calls=[]  # ツール呼び出しなし
        )
        return {
            "messages": [mock_llm.invoke(state["messages"])],
            "llm_calls": state.get("llm_calls", 0) + 1
        }
    
    def should_route(state: ConditionalState) -> str:
        """値に基づいてルーティング"""
        value = state.get("value", 0)
        if value > 10:
            return "high_path"
        return "low_path"
    
    graph = StateGraph(ConditionalState)
    graph.add_node("start", lambda state: state)  # 開始ノード
    graph.add_node("high_path", llm_call_high)
    graph.add_node("low_path", llm_call_low)
    
    graph.add_edge(START, "start")
    graph.add_conditional_edges(
        "start",
        should_route,
        {
            "high_path": "high_path",
            "low_path": "low_path"
        }
    )
    graph.add_edge("high_path", END)
    graph.add_edge("low_path", END)
    
    return graph


def test_conditional_edge_high():
    """条件付きエッジ（high）のテスト（LLMモック）"""
    graph = create_graph_with_conditional_edge()
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({
        "messages": [HumanMessage(content="Test")],
        "llm_calls": 0,
        "value": 15
    })
    
    assert result["value"] == 15
    assert len(result["messages"]) > 0


def test_conditional_edge_low():
    """条件付きエッジ（low）のテスト（LLMモック）"""
    graph = create_graph_with_conditional_edge()
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({
        "messages": [HumanMessage(content="Test")],
        "llm_calls": 0,
        "value": 5
    })
    
    assert result["value"] == 5
    assert len(result["messages"]) > 0


"""
pytestフィクスチャの使用テスト
"""
import pytest
from langchain_core.messages import HumanMessage
from my_agent.utils.state import MessagesState
from tests.conftest import checkpointer, compiled_graph_with_mock, mock_llm, mock_llm_with_tools


def test_with_fixtures(compiled_graph_with_mock):
    """フィクスチャを使用したテスト（LLMモック）"""
    result = compiled_graph_with_mock.invoke(
        {
            "messages": [HumanMessage(content="Hello")],
            "llm_calls": 0
        },
        config={"configurable": {"thread_id": "fixture-test"}}
    )
    
    assert len(result["messages"]) > 1
    assert result["llm_calls"] > 0


@pytest.fixture
def mock_llm_responses():
    """状態に基づくLLMレスポンスのモック"""
    responses = {
        "greeting": "Hello! How can I help you?",
        "question": "I can answer that question.",
        "calculation": "I'll calculate that for you.",
        "goodbye": "Goodbye! Have a nice day!"
    }
    
    def get_response(state: MessagesState):
        """状態に基づいてレスポンスを返す"""
        if not state.get("messages"):
            return responses["greeting"]
        
        last_message = state["messages"][-1]
        content = last_message.content.lower() if hasattr(last_message, 'content') else ""
        
        if "hello" in content or "hi" in content:
            return responses["greeting"]
        elif "calculate" in content or "+" in content or "*" in content:
            return responses["calculation"]
        elif "?" in content:
            return responses["question"]
        else:
            return responses["goodbye"]
    
    return get_response


def test_agent_with_state_based_mock(mock_llm_responses):
    """状態ベースのモックを使用したテスト（LLMモック）"""
    from unittest.mock import Mock
    from langgraph.graph import StateGraph, START, END
    from langchain_core.messages import AIMessage
    
    # モックLLMを作成
    mock_llm = Mock()
    
    def llm_node(state: MessagesState):
        """状態に基づいてレスポンスを返すLLMノード"""
        response_text = mock_llm_responses(state)
        mock_llm.invoke.return_value = AIMessage(content=response_text)
        return {
            "messages": [mock_llm.invoke(state["messages"])],
            "llm_calls": state.get("llm_calls", 0) + 1
        }
    
    graph = StateGraph(MessagesState)
    graph.add_node("llm", llm_node)
    graph.add_edge(START, "llm")
    graph.add_edge("llm", END)
    
    compiled_graph = graph.compile()
    
    # 挨拶メッセージでテスト
    result = compiled_graph.invoke({
        "messages": [HumanMessage(content="Hello")],
        "llm_calls": 0
    })
    
    assert result["messages"][-1].content == "Hello! How can I help you?"
    
    # 計算メッセージでテスト
    result2 = compiled_graph.invoke({
        "messages": [HumanMessage(content="Calculate 2 + 3")],
        "llm_calls": 0
    })
    
    assert result2["messages"][-1].content == "I'll calculate that for you."


def test_multiple_tests_with_same_fixtures(compiled_graph_with_mock):
    """同じフィクスチャを使用した複数のテスト（LLMモック）"""
    # テスト1
    result1 = compiled_graph_with_mock.invoke(
        {
            "messages": [HumanMessage(content="Test 1")],
            "llm_calls": 0
        },
        config={"configurable": {"thread_id": "test-fixture-1"}}
    )
    assert len(result1["messages"]) > 1
    
    # テスト2（同じフィクスチャを使用）
    result2 = compiled_graph_with_mock.invoke(
        {
            "messages": [HumanMessage(content="Test 2")],
            "llm_calls": 0
        },
        config={"configurable": {"thread_id": "test-fixture-2"}}
    )
    assert len(result2["messages"]) > 1


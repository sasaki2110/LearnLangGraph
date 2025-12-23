"""
基本的なテスト：グラフの実行テストと個別ノードのテスト
"""
import pytest
from langchain_core.messages import HumanMessage, AIMessage
from my_agent.utils.state import MessagesState
from tests.conftest import checkpointer, compiled_graph_with_mock, mock_llm_with_tools


def test_basic_agent_execution(compiled_graph_with_mock):
    """基本的なグラフ実行のテスト（LLMモック）"""
    result = compiled_graph_with_mock.invoke(
        {
            "messages": [HumanMessage(content="What is 2 + 3?")],
            "llm_calls": 0
        },
        config={"configurable": {"thread_id": "test-1"}}
    )
    
    # メッセージが追加されていることを確認
    assert len(result["messages"]) > 1
    assert result["llm_calls"] > 0


def test_individual_node_execution(compiled_graph_with_mock):
    """個別ノードの実行テスト（LLMモック）"""
    # llm_callノードのみを実行
    initial_state = {
        "messages": [HumanMessage(content="Hello")],
        "llm_calls": 0
    }
    
    result = compiled_graph_with_mock.nodes["llm_call"].invoke(initial_state)
    
    # LLM呼び出しが実行されたことを確認
    assert "messages" in result
    assert len(result["messages"]) > 0
    assert result["llm_calls"] == 1


def test_multiple_nodes_sequential(compiled_graph_with_mock):
    """複数のノードを順番に実行するテスト（LLMモック）"""
    state = {
        "messages": [HumanMessage(content="Calculate 2 + 3")],
        "llm_calls": 0
    }
    
    # llm_callノードを実行
    state = compiled_graph_with_mock.nodes["llm_call"].invoke(state)
    assert "messages" in state
    assert state["llm_calls"] == 1
    
    # tool_nodeを実行（ツール呼び出しがある場合）
    if state["messages"][-1].tool_calls:
        state = compiled_graph_with_mock.nodes["tool_node"].invoke(state)
        assert "messages" in state
        assert len(state["messages"]) > 1


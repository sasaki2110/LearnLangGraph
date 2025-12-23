"""
LLMのモックテスト
"""
import pytest
from unittest.mock import Mock
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import MessagesState
from my_agent.utils.nodes import llm_call, tool_node, should_continue
from my_agent.utils.tools import add, multiply, divide


def test_agent_with_mocked_llm():
    """LLMをモックしたエージェントのテスト"""
    # LLMのモックを作成
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(content="Mocked response")
    
    # bind_tools()をモック
    def bind_tools(tools):
        bound_mock = Mock()
        bound_mock.invoke.return_value = AIMessage(content="Mocked response")
        return bound_mock
    
    mock_llm.bind_tools = bind_tools
    
    # ツールをバインド
    tools = [add, multiply, divide]
    mock_llm_with_tools = mock_llm.bind_tools(tools)
    
    # LLMを使用するノードを定義
    def llm_node(state: MessagesState):
        return llm_call(state, mock_llm_with_tools)
    
    graph = StateGraph(MessagesState)
    graph.add_node("llm", llm_node)
    graph.add_edge(START, "llm")
    graph.add_edge("llm", END)
    
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({
        "messages": [HumanMessage(content="Hello")],
        "llm_calls": 0
    })
    
    assert len(result["messages"]) == 2
    assert result["messages"][-1].content == "Mocked response"
    # bind_tools()で作成されたMockオブジェクトのinvokeが呼び出されたことを確認
    assert mock_llm_with_tools.invoke.called


def test_agent_with_mocked_llm_tool_calls():
    """ツール呼び出しを含むLLMモックのテスト"""
    # LLMのモックを作成（ツール呼び出しあり）
    mock_llm = Mock()
    mock_llm.invoke.return_value = AIMessage(
        content="I'll calculate that for you.",
        tool_calls=[
            {
                "name": "add",
                "args": {"a": 2, "b": 3},
                "id": "call_123"
            }
        ]
    )
    
    # bind_tools()をモック
    def bind_tools(tools):
        bound_mock = Mock()
        
        # 状態に基づいてレスポンスを変更
        def invoke(messages):
            # ツールメッセージが含まれている場合は、ツール呼び出しなしのレスポンスを返す
            from langchain.messages import ToolMessage
            has_tool_message = any(isinstance(msg, ToolMessage) for msg in messages)
            
            if has_tool_message:
                # ツール呼び出し後のレスポンス（ツール呼び出しなし）
                return AIMessage(content="The result is 5.")
            else:
                # 最初の呼び出し（ツール呼び出しあり）
                return AIMessage(
                    content="I'll calculate that for you.",
                    tool_calls=[
                        {
                            "name": "add",
                            "args": {"a": 2, "b": 3},
                            "id": "call_123"
                        }
                    ]
                )
        
        bound_mock.invoke.side_effect = invoke
        return bound_mock
    
    mock_llm.bind_tools = bind_tools
    
    # ツールをバインド
    tools = [add, multiply, divide]
    mock_llm_with_tools = mock_llm.bind_tools(tools)
    
    # LLM呼び出しノード
    def llm_node(state: MessagesState):
        return llm_call(state, mock_llm_with_tools)
    
    graph = StateGraph(MessagesState)
    graph.add_node("llm_call", llm_node)
    graph.add_node("tool_node", tool_node)
    graph.add_edge(START, "llm_call")
    graph.add_conditional_edges(
        "llm_call",
        should_continue,
        {
            "tool_node": "tool_node",
            END: END
        }
    )
    graph.add_edge("tool_node", "llm_call")
    
    compiled_graph = graph.compile()
    
    result = compiled_graph.invoke({
        "messages": [HumanMessage(content="What is 2 + 3?")],
        "llm_calls": 0
    })
    
    # ツールが呼び出されたことを確認
    assert len(result["messages"]) > 1
    # 最後のメッセージがツールの結果であることを確認
    assert any(msg.content == "5" for msg in result["messages"] if hasattr(msg, 'content'))


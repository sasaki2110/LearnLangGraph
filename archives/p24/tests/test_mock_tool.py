"""
ツールのモックテスト
"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import MessagesState
from my_agent.utils.nodes import llm_call, tool_node, should_continue
from my_agent.utils.tools import add, multiply, divide


def test_agent_with_mocked_tool():
    """ツールをモックしたエージェントのテスト（LLMモック）"""
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
    
    # ツールのモック
    mock_add = Mock(return_value="Mocked result: 5")
    
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
                return AIMessage(content="The calculation is complete.")
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
    
    # ツールノードをモックでラップ
    def tool_node_mocked(state: MessagesState):
        """モックツールを使用するツールノード"""
        result = []
        for tool_call in state["messages"][-1].tool_calls:
            if tool_call["name"] == "add":
                observation = mock_add(tool_call["args"]["a"], tool_call["args"]["b"])
            else:
                # 他のツールは通常通り実行
                tool = {tool.name: tool for tool in tools}[tool_call["name"]]
                observation = tool.invoke(tool_call["args"])
            from langchain.messages import ToolMessage
            result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
        return {"messages": result}
    
    graph = StateGraph(MessagesState)
    graph.add_node("llm_call", llm_node)
    graph.add_node("tool_node", tool_node_mocked)
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
    
    # モックツールが呼び出されたことを確認
    mock_add.assert_called_once_with(2, 3)
    assert len(result["messages"]) > 1


def test_agent_with_patched_tool():
    """パッチを使用したツールのモックテスト（LLMモック）"""
    from my_agent.utils.tools import multiply, divide
    import my_agent.utils.nodes as nodes_module
    
    # モックツールの設定（LangChainのツールはinvoke()メソッドを持つ）
    mock_add = Mock()
    mock_add.invoke = Mock(return_value=100)  # invoke()が呼ばれたときに100を返す
    mock_add.name = "add"  # ツール名を設定
    
    # tools_by_nameを直接置き換える（元の値を保存）
    original_tools_by_name = nodes_module.tools_by_name.copy()
    nodes_module.tools_by_name = {
        "add": mock_add,
        "multiply": multiply,
        "divide": divide
    }
    
    try:
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
                    return AIMessage(content="The calculation is complete.")
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
        tools = [mock_add, multiply, divide]
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
        
        # モックツールが呼び出されたことを確認（invoke()メソッドが呼ばれる）
        mock_add.invoke.assert_called_once_with({'a': 2, 'b': 3})
        # モックの結果が返されていることを確認
        assert any("100" in str(msg.content) for msg in result["messages"] if hasattr(msg, 'content'))
    finally:
        # 元のtools_by_nameを復元
        nodes_module.tools_by_name = original_tools_by_name


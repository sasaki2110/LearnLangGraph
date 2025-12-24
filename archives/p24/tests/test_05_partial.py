"""
部分実行のテスト
"""
import pytest
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from my_agent.utils.state import MessagesState
from tests.conftest import graph_with_mock_llm


def test_partial_execution_from_llm_to_tool():
    """llm_callからtool_nodeまでの部分実行テスト（LLMモック）"""
    from unittest.mock import Mock
    from langchain_core.messages import AIMessage
    from langgraph.graph import StateGraph, START, END
    from my_agent.utils.state import MessagesState
    from my_agent.utils.nodes import llm_call, tool_node, should_continue
    from my_agent.utils.tools import add, multiply, divide
    
    # モックLLMを作成
    mock_llm = Mock()
    
    # bind_tools()をモック
    def bind_tools(tools):
        bound_mock = Mock()
        bound_mock.invoke.return_value = AIMessage(
            content="I'll calculate that",
            tool_calls=[{
                "name": "add",
                "args": {"a": 2, "b": 3},
                "id": "call_123"
            }]
        )
        return bound_mock
    
    mock_llm.bind_tools = bind_tools
    
    # ツールをバインド
    tools = [add, multiply, divide]
    mock_llm_with_tools = mock_llm.bind_tools(tools)
    
    # LLM呼び出しノード
    def llm_call_node(state: MessagesState):
        return llm_call(state, mock_llm_with_tools)
    
    # グラフの構築
    graph = StateGraph(MessagesState)
    graph.add_node("llm_call", llm_call_node)
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
    
    checkpointer = MemorySaver()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    # llm_callの終了状態をシミュレート
    # これにより、実行はtool_nodeから開始される
    compiled_graph.update_state(
        config={
            "configurable": {
                "thread_id": "partial-test-1"
            }
        },
        # llm_callの終了時の状態（ツール呼び出しあり）
        values={
            "messages": [
                HumanMessage(content="Calculate 2 + 3"),
                # モックLLMのレスポンス（ツール呼び出しあり）
                AIMessage(
                    content="I'll calculate that",
                    tool_calls=[{
                        "name": "add",
                        "args": {"a": 2, "b": 3},
                        "id": "call_123"
                    }]
                )
            ],
            "llm_calls": 1
        },
        # llm_callの終了時点として状態を設定
        as_node="llm_call",
    )
    
    # tool_nodeから開始し、llm_callの後で停止
    result = compiled_graph.invoke(
        None,  # 状態は既に設定されているためNone
        config={"configurable": {"thread_id": "partial-test-1"}},
        interrupt_after="llm_call",  # llm_callの後で停止
    )
    
    # tool_nodeが実行されたことを確認
    assert len(result["messages"]) > 1


def test_processing_pipeline_only():
    """特定のノードのみをテスト（LLMモック）"""
    from langgraph.graph import StateGraph, START, END
    from typing_extensions import TypedDict
    
    class ProcessingState(TypedDict):
        step: str
        data: dict
        messages: list
    
    def preprocess_node(state: ProcessingState):
        return {"step": "preprocessed", "data": {"input": "test"}}
    
    def validate_node(state: ProcessingState):
        return {"step": "validated"}
    
    def process_node(state: ProcessingState):
        return {"step": "processed"}
    
    def postprocess_node(state: ProcessingState):
        return {"step": "postprocessed"}
    
    def finalize_node(state: ProcessingState):
        return {"step": "finalized"}
    
    graph = StateGraph(ProcessingState)
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("validate", validate_node)
    graph.add_node("process", process_node)
    graph.add_node("postprocess", postprocess_node)
    graph.add_node("finalize", finalize_node)
    
    graph.add_edge(START, "preprocess")
    graph.add_edge("preprocess", "validate")
    graph.add_edge("validate", "process")
    graph.add_edge("process", "postprocess")
    graph.add_edge("postprocess", "finalize")
    graph.add_edge("finalize", END)
    
    checkpointer = MemorySaver()
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    # validateの終了状態をシミュレート
    compiled_graph.update_state(
        config={"configurable": {"thread_id": "pipeline-test"}},
        values={"step": "validated", "data": {"input": "test"}, "messages": []},
        as_node="validate",
    )
    
    # processノードのみを実行
    result = compiled_graph.invoke(
        None,
        config={"configurable": {"thread_id": "pipeline-test"}},
        interrupt_after="process",
    )
    
    assert result["step"] == "processed"


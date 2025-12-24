"""
共通フィクスチャ
"""
import pytest
from unittest.mock import Mock
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage
from my_agent.utils.state import MessagesState
from my_agent.utils.nodes import llm_call, tool_node, should_continue
from my_agent.utils.tools import add, multiply, divide
from langgraph.graph import StateGraph, START, END


"""
チェックポインターのフィクスチャ

テスト用のモックLLMをコンパイルする際に、スレッドIDを使ったスレッド管理を行うため、
スレッドIDを使ったチェックポインターを使用する。

テスト用なので、メモリで短期記憶を行う。
"""
@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()

"""
モックLLMのフィクスチャ

モックLLMを作成する。
モックLLMは、ツール呼び出しをモックして、ツール呼び出し後のレスポンスを返す。

このモックは、bind_tools()をモックしている。
つまり、正式版の

tools = [add, multiply, divide]
model_with_tools = model.bind_tools(tools)
をモックするもの。

bind_tools()が返すのは、bound_mock。（これがLLM相当の動きをするオブジェクト）
bound_mock.invoke()が呼び出されたときに、invoke()が呼び出される。

llm_call()が呼び出されたときに、bound_mock.invoke()が呼び出される。
（逆に言うと、llm_call()に、このmock_llmを渡す。）
"""
@pytest.fixture
def mock_llm():
    """モックLLMフィクスチャ"""
    mock = Mock()
    
    # bind_tools()をモック（実際のLLMのように動作）
    def bind_tools(tools):
        bound_mock = Mock()
        
        # 状態に基づいてレスポンスを変更
        def invoke(messages):
            # ツールメッセージが含まれている場合は、ツール呼び出しなしのレスポンスを返す
            from langchain.messages import ToolMessage
            has_tool_message = any(isinstance(msg, ToolMessage) for msg in messages)
            
            if has_tool_message:
                # ツール呼び出し後のレスポンス（ツール呼び出しなし）
                return AIMessage(content="I've completed the task.")
            else:
                # 最初の呼び出し（ツール呼び出しなし）
                return AIMessage(content="Hello, how can I help you?")
        
        bound_mock.invoke.side_effect = invoke
        return bound_mock
    
    mock.bind_tools = bind_tools
    return mock

"""
モックLLMを使用したグラフフィクスチャ

グラフ自体はLangGraphのStateGraphを使用して、通常通りにグラフを構築する。
ただし、LLMをモックしたものを使用する。
"""
@pytest.fixture
def graph_with_mock_llm(mock_llm):
    """モックLLMを使用したグラフフィクスチャ"""
    # ツールをバインド
    tools = [add, multiply, divide]
    mock_llm_with_tools = mock_llm.bind_tools(tools)
    
    # LLM呼び出しノードをラップ
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
    
    return graph


@pytest.fixture
def compiled_graph_with_mock(checkpointer, graph_with_mock_llm):
    """コンパイル済みグラフフィクスチャ（モックLLM使用）"""
    return graph_with_mock_llm.compile(checkpointer=checkpointer)


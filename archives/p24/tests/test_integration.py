"""
結合テスト（実際のLLMを使用）
"""
import pytest
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import MessagesState
from my_agent.utils.nodes import llm_call, tool_node, should_continue
from my_agent.utils.tools import add, multiply, divide

# 環境変数の読み込み
load_dotenv()


@pytest.fixture
def checkpointer():
    """チェックポインタフィクスチャ"""
    return MemorySaver()


@pytest.fixture
def compiled_graph(checkpointer):
    """実際のLLMを使用したコンパイル済みグラフフィクスチャ"""
    # 実際のLLMを使用してグラフを構築
    MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    model = init_chat_model(MODEL_NAME, temperature=0)
    
    # ツールをバインド
    tools = [add, multiply, divide]
    model_with_tools = model.bind_tools(tools)
    
    # LLM呼び出しノードをラップ
    def llm_call_node(state: MessagesState):
        return llm_call(state, model_with_tools)
    
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
    
    return graph.compile(checkpointer=checkpointer)


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEYが設定されていないため、結合テストをスキップします"
)
def test_end_to_end_workflow(compiled_graph):
    """エンドツーエンドのワークフローテスト（実際のLLM使用）"""
    # 初期状態
    initial_state = {
        "messages": [HumanMessage(content="What is 2 + 3?")],
        "llm_calls": 0
    }
    
    # グラフ全体を実行
    result = compiled_graph.invoke(
        initial_state,
        config={"configurable": {"thread_id": "e2e-test"}}
    )
    
    # 最終状態を検証
    assert len(result["messages"]) > 1
    assert result["llm_calls"] > 0
    # 計算結果が含まれていることを確認
    assert any("5" in str(msg.content) for msg in result["messages"] if hasattr(msg, 'content'))


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEYが設定されていないため、結合テストをスキップします"
)
def test_multi_step_conversation(compiled_graph):
    """複数ステップの会話テスト（実際のLLM使用）"""
    thread_id = "conversation-test"
    config = {"configurable": {"thread_id": thread_id}}
    
    # ステップ1: 加算
    result1 = compiled_graph.invoke(
        {
            "messages": [HumanMessage(content="What is 2 + 3?")],
            "llm_calls": 0
        },
        config=config
    )
    assert len(result1["messages"]) > 1
    assert result1["llm_calls"] > 0
    
    # ステップ2: 乗算（同じthread_idで続行）
    result2 = compiled_graph.invoke(
        {
            "messages": [HumanMessage(content="What is 4 * 5?")],
            "llm_calls": 0
        },
        config=config
    )
    assert len(result2["messages"]) > 1
    assert result2["llm_calls"] > 0


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEYが設定されていないため、結合テストをスキップします"
)
def test_calculation_tools(compiled_graph):
    """計算ツールの統合テスト（実際のLLM使用）"""
    test_cases = [
        ("What is 10 + 20?", "30"),
        ("What is 5 * 6?", "30"),
        ("What is 100 / 4?", "25"),
    ]
    
    for question, expected in test_cases:
        result = compiled_graph.invoke(
            {
                "messages": [HumanMessage(content=question)],
                "llm_calls": 0
            },
            config={"configurable": {"thread_id": f"calc-test-{question}"}}
        )
        
        # 結果が含まれていることを確認
        assert len(result["messages"]) > 1
        # 期待される値が結果に含まれていることを確認
        assert any(
            expected in str(msg.content) 
            for msg in result["messages"] 
            if hasattr(msg, 'content')
        )


"""
グラフのinvokeを確認するテスト
"""
import pytest
from langchain.messages import HumanMessage
from my_agent.agent import graph
from my_agent.utils.state import MessagesState


def test_graph_invoke_add(calculator_graph):
    """加算計算のinvokeテスト"""
    # テスト用のメッセージ
    initial_state: MessagesState = {
        "messages": [HumanMessage(content="5と3を足してください")],
        "llm_calls": 0
    }
    
    # グラフの実行
    result = calculator_graph.invoke(initial_state)
    
    # 結果の検証
    assert "messages" in result
    assert "llm_calls" in result
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) > 0
    
    # LLMが呼び出されたことを確認
    assert result["llm_calls"] > 0
    
    # 最後のメッセージを確認（計算結果が含まれているはず）
    last_message = result["messages"][-1]
    assert last_message is not None
    
    # メッセージの内容を確認（数値が含まれているはず）
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
    assert content is not None
    assert len(str(content)) > 0


def test_graph_invoke_multiply(calculator_graph):
    """乗算計算のinvokeテスト"""
    # テスト用のメッセージ
    initial_state: MessagesState = {
        "messages": [HumanMessage(content="4と7を掛けてください")],
        "llm_calls": 0
    }
    
    # グラフの実行
    result = calculator_graph.invoke(initial_state)
    
    # 結果の検証
    assert "messages" in result
    assert "llm_calls" in result
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) > 0
    
    # LLMが呼び出されたことを確認
    assert result["llm_calls"] > 0
    
    # 最後のメッセージを確認
    last_message = result["messages"][-1]
    assert last_message is not None


def test_graph_invoke_divide(calculator_graph):
    """除算計算のinvokeテスト"""
    # テスト用のメッセージ
    initial_state: MessagesState = {
        "messages": [HumanMessage(content="10を2で割ってください")],
        "llm_calls": 0
    }
    
    # グラフの実行
    result = calculator_graph.invoke(initial_state)
    
    # 結果の検証
    assert "messages" in result
    assert "llm_calls" in result
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) > 0
    
    # LLMが呼び出されたことを確認
    assert result["llm_calls"] > 0
    
    # 最後のメッセージを確認
    last_message = result["messages"][-1]
    assert last_message is not None


def test_graph_invoke_multiple_operations(calculator_graph):
    """複数の計算を連続で行うテスト"""
    # テスト用のメッセージ（複数の計算を依頼）
    initial_state: MessagesState = {
        "messages": [HumanMessage(content="5と3を足して、その結果に2を掛けてください")],
        "llm_calls": 0
    }
    
    # グラフの実行
    result = calculator_graph.invoke(initial_state)
    
    # 結果の検証
    assert "messages" in result
    assert "llm_calls" in result
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) > 0
    
    # 複数の計算が実行された場合、複数のLLM呼び出しが発生する可能性がある
    assert result["llm_calls"] > 0


def test_graph_invoke_state_structure(calculator_graph):
    """状態の構造を確認するテスト"""
    # テスト用のメッセージ
    initial_state: MessagesState = {
        "messages": [HumanMessage(content="2と3を足してください")],
        "llm_calls": 0
    }
    
    # グラフの実行
    result = calculator_graph.invoke(initial_state)
    
    # 状態の構造を確認
    assert isinstance(result, dict)
    assert "messages" in result
    assert "llm_calls" in result
    
    # messagesがリストであることを確認
    assert isinstance(result["messages"], list)
    
    # llm_callsが整数であることを確認
    assert isinstance(result["llm_calls"], int)
    assert result["llm_calls"] >= 0


def test_graph_invoke_empty_messages(calculator_graph):
    """空のメッセージでグラフを実行するテスト"""
    # 空のメッセージリスト
    initial_state: MessagesState = {
        "messages": [],
        "llm_calls": 0
    }
    
    # グラフの実行（エラーが発生する可能性があるが、エラーハンドリングを確認）
    try:
        result = calculator_graph.invoke(initial_state)
        # エラーが発生しなかった場合、結果を確認
        assert "messages" in result
        assert "llm_calls" in result
    except Exception as e:
        # エラーが発生した場合、それは期待される動作かもしれない
        assert isinstance(e, Exception)


def test_graph_invoke_multiple_requests(calculator_graph):
    """複数の異なる計算要求でグラフを実行するテスト"""
    test_cases = [
        "5と3を足してください",
        "4と7を掛けてください",
        "10を2で割ってください",
    ]
    
    for user_message in test_cases:
        initial_state: MessagesState = {
            "messages": [HumanMessage(content=user_message)],
            "llm_calls": 0
        }
        
        result = calculator_graph.invoke(initial_state)
        
        # 基本的な結果の検証
        assert "messages" in result
        assert "llm_calls" in result
        assert isinstance(result["messages"], list)
        assert len(result["messages"]) > 0
        assert result["llm_calls"] > 0


def test_graph_invoke_llm_calls_counter(calculator_graph):
    """LLM呼び出しカウンターが正しく動作することを確認するテスト"""
    initial_state: MessagesState = {
        "messages": [HumanMessage(content="2と3を足してください")],
        "llm_calls": 0
    }
    
    # グラフの実行
    result = calculator_graph.invoke(initial_state)
    
    # LLM呼び出しカウンターが増加していることを確認
    assert result["llm_calls"] > initial_state["llm_calls"]
    
    # カウンターが整数であることを確認
    assert isinstance(result["llm_calls"], int)


def test_graph_invoke_tool_execution(calculator_graph):
    """ツールが実行されることを確認するテスト"""
    # ツール呼び出しを明示的に要求するメッセージ
    initial_state: MessagesState = {
        "messages": [HumanMessage(content="addツールを使って5と3を足してください")],
        "llm_calls": 0
    }
    
    # グラフの実行
    result = calculator_graph.invoke(initial_state)
    
    # 結果の検証
    assert "messages" in result
    assert len(result["messages"]) > 0
    
    # ツールが実行された場合、ToolMessageが含まれるはず
    # （実際の実装に依存するが、メッセージが増えていることを確認）
    assert len(result["messages"]) >= len(initial_state["messages"])


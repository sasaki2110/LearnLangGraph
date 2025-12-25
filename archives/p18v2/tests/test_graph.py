"""
グラフの統合テスト
"""
from langgraph.types import Command


def test_graph_invoke_with_interrupt(config, initial_state, graph_with_checkpointer):
    """グラフをinvokeして中断が発生することを確認"""
    # 初期状態でグラフを実行（nodeBで中断される）
    result = graph_with_checkpointer.invoke(initial_state, config)
    
    # 中断が発生していることを確認
    assert "__interrupt__" in result
    
    # 中断情報を確認
    interrupt_info = result["__interrupt__"]
    assert interrupt_info is not None
    assert len(interrupt_info) > 0
    
    # 中断ペイロードを確認
    payload = interrupt_info[0].value if hasattr(interrupt_info[0], 'value') else interrupt_info[0]
    assert isinstance(payload, dict)
    assert "question" in payload
    assert "action" in payload
    assert "message" in payload


def test_graph_invoke_with_resume(config, initial_state, graph_with_checkpointer):
    """グラフをinvokeして再開できることを確認"""
    # 初期状態でグラフを実行（nodeBで中断される）
    result = graph_with_checkpointer.invoke(initial_state, config)
    
    # 中断が発生していることを確認
    assert "__interrupt__" in result
    
    # 承認して再開
    result = graph_with_checkpointer.invoke(Command(resume=True), config=config)
    
    # 中断が発生していないことを確認（完了）
    assert "__interrupt__" not in result
    
    # 最終状態を確認
    assert "messages" in result
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) > 0
    
    # node_cのメッセージが含まれていることを確認
    messages = result["messages"]
    node_c_message = [msg for msg in messages if "node_c" in msg]
    assert len(node_c_message) > 0


def test_graph_get_state(config, initial_state, graph_with_checkpointer):
    """グラフの状態を取得できることを確認"""
    # 初期状態でグラフを実行（nodeBで中断される）
    result = graph_with_checkpointer.invoke(initial_state, config)
    
    # 中断が発生していることを確認
    assert "__interrupt__" in result
    
    # 現在の状態を取得
    state = graph_with_checkpointer.get_state(config)
    
    # 状態が取得できることを確認
    assert state is not None
    assert state.values is not None
    assert "messages" in state.values
    assert "action" in state.values
    
    # 次に実行するノードが存在することを確認
    assert state.next is not None


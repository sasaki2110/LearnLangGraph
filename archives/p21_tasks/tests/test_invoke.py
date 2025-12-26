"""
グラフのinvokeを確認するテスト
"""
import pytest
import uuid
from langgraph.types import Command
from my_agent.utils.state import State


def test_graph_invoke(graph_with_checkpointer):
    """グラフをinvokeして結果を確認するテスト"""
    # スレッドIDを含む設定を定義
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # テスト用のURL
    test_urls = ["https://www.example.com"]
    
    # グラフの実行
    result = graph_with_checkpointer.invoke({"urls": test_urls}, config)
    
    # 結果の検証
    assert "results" in result
    assert isinstance(result["results"], list)
    assert len(result["results"]) == len(test_urls)
    assert all(isinstance(r, str) for r in result["results"])
    assert len(result["results"][0]) == 100  # 最初の100文字を取得


def test_graph_invoke_multiple_urls(graph_with_checkpointer):
    """複数のURLを処理するテスト"""
    # スレッドIDを含む設定を定義
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # 複数のテスト用URL
    test_urls = [
        "https://www.example.com",
        "https://www.python.org"
    ]
    
    # グラフの実行
    result = graph_with_checkpointer.invoke({"urls": test_urls}, config)
    
    # 結果の検証
    assert "results" in result
    assert isinstance(result["results"], list)
    assert len(result["results"]) == len(test_urls)
    assert all(isinstance(r, str) for r in result["results"])
    assert all(len(r) == 100 for r in result["results"])  # 各結果は100文字


def test_graph_invoke_with_same_thread_id(graph_with_checkpointer):
    """同じスレッドIDで再実行した場合、タスクが再実行されないことを確認するテスト"""
    # スレッドIDを含む設定を定義
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # テスト用のURL
    test_urls = ["https://www.example.com"]
    
    # 最初の実行
    result1 = graph_with_checkpointer.invoke({"urls": test_urls}, config)
    
    # 2回目の実行（同じスレッドID）
    result2 = graph_with_checkpointer.invoke({"urls": test_urls}, config)
    
    # 結果が同じであることを確認（タスクが再実行されず、永続化レイヤーから結果が取得される）
    assert result1["results"] == result2["results"]


def test_graph_invoke_state_structure(graph_with_checkpointer):
    """状態の構造を確認するテスト"""
    # スレッドIDを含む設定を定義
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # テスト用のURL
    test_urls = ["https://www.example.com"]
    
    # グラフの実行
    result = graph_with_checkpointer.invoke({"urls": test_urls}, config)
    
    # 状態の構造を検証
    assert isinstance(result, dict)
    assert "urls" in result
    assert "results" in result
    assert result["urls"] == test_urls
    assert isinstance(result["results"], list)


def test_interrupt_and_resume_with_tasks(graph_with_checkpointer):
    """中断と再開のシナリオを確認するテスト
    
    シナリオ：
    1. process_with_different_tasksが先に実行される（タスクが実行され、永続化される）
    2. call_apiで中断される
    3. 再開すると、process_with_different_tasksのタスクは再実行されず、永続化された値が利用される
    4. call_apiが実行される
    """
    # スレッドIDを含む設定を定義
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # テスト用のURL
    test_urls = ["https://www.example.com"]
    
    # 1. 最初の実行（process_with_different_tasks → call_apiで中断）
    result1 = graph_with_checkpointer.invoke({"urls": test_urls}, config)
    
    # 中断が発生したことを確認
    assert "__interrupt__" in result1
    interrupt_info = result1["__interrupt__"]
    assert interrupt_info is not None
    assert len(interrupt_info) > 0
    
    # process_with_different_tasksの結果が含まれていることを確認
    # （タスクが実行され、永続化されている）
    assert "random_id" in result1
    assert "processed" in result1
    
    # 最初のrandom_idとprocessedを保存（再開時に同じ値が使われることを確認するため）
    first_random_id = result1["random_id"]
    first_processed = result1["processed"]
    
    # 2. ユーザー承認で再開
    user_response = {"approved": True}
    result2 = graph_with_checkpointer.invoke(Command(resume=user_response), config=config)
    
    # 3. 再開後の結果を確認
    # process_with_different_tasksのタスクは再実行されず、永続化された値が利用される
    assert "random_id" in result2
    assert "processed" in result2
    
    # タスクが再実行されていないことを確認（同じ値が返される）
    assert result2["random_id"] == first_random_id
    assert result2["processed"] == first_processed
    
    # call_apiの結果も含まれていることを確認
    assert "results" in result2
    assert isinstance(result2["results"], list)
    assert len(result2["results"]) > 0


def test_multiple_tasks_with_interrupt(checkpointer):
    """複数のタスクを実行し、途中で中断した場合の動作を確認するテスト
    
    シナリオ：
    1. node_with_multiple_tasks_and_interruptが実行される
    2. task_1が実行され、結果が永続化される
    3. task_2が実行され、結果が永続化される
    4. 中断が発生
    5. 再開すると、task_1とtask_2は再実行されず、永続化された結果が使用される
    6. task_3のみが新しく実行される
    """
    from my_agent.utils.nodes import node_with_multiple_tasks_and_interrupt
    from langgraph.graph import StateGraph, START, END
    from my_agent.utils.state import State
    
    # テスト用のグラフを作成
    builder = StateGraph(State)
    builder.add_node("test_node", node_with_multiple_tasks_and_interrupt)
    builder.add_edge(START, "test_node")
    builder.add_edge("test_node", END)
    
    # チェックポインタ付きでコンパイル
    test_graph = builder.compile(checkpointer=checkpointer)
    
    # スレッドIDを含む設定を定義
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # テスト用のURL（空でも良い）
    test_urls = ["https://www.example.com"]
    
    # 1. 最初の実行（task_1, task_2まで実行して中断）
    result1 = test_graph.invoke({"urls": test_urls}, config)
    
    # 中断が発生したことを確認
    assert "__interrupt__" in result1
    interrupt_info = result1["__interrupt__"]
    assert interrupt_info is not None
    assert len(interrupt_info) > 0
    
    # 中断情報からtask_1とtask_2の結果を取得
    interrupt_value = interrupt_info[0].value if hasattr(interrupt_info[0], 'value') else interrupt_info[0]
    assert isinstance(interrupt_value, dict)
    assert "task_1_result" in interrupt_value
    assert "task_2_result" in interrupt_value
    assert interrupt_value["task_1_result"] == "task_1_result"
    assert interrupt_value["task_2_result"] == "task_2_result"
    
    # 最初の結果を保存（再開時に同じ値が使われることを確認するため）
    first_task_1_result = interrupt_value["task_1_result"]
    first_task_2_result = interrupt_value["task_2_result"]
    
    # 2. ユーザー承認で再開
    user_response = {"approved": True}
    result2 = test_graph.invoke(Command(resume=user_response), config=config)
    
    # 3. 再開後の結果を確認
    # task_1とtask_2は再実行されず、永続化された値が利用される
    assert "task_1_result" in result2
    assert "task_2_result" in result2
    assert "task_3_result" in result2
    
    # タスクが再実行されていないことを確認（同じ値が返される）
    assert result2["task_1_result"] == first_task_1_result
    assert result2["task_2_result"] == first_task_2_result
    
    # task_3は新しく実行されていることを確認
    assert result2["task_3_result"] == "task_3_result"


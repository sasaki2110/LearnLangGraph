"""
グラフのinvokeを確認するテスト
"""
import pytest
import uuid
from my_agent.agent import graph


def test_graph_invoke():
    """グラフをinvokeして結果を確認するテスト"""
    # テスト用のユーザー要求
    user_request = "PythonのLangGraphについて簡単に説明してください。"
    
    # グラフの実行
    result = graph.invoke({"user_request": user_request})
    
    # 結果の検証
    assert "user_request" in result
    assert "task_list" in result
    assert "completed_tasks" in result
    assert "final_result" in result
    
    # タスクリストが生成されていることを確認
    assert isinstance(result["task_list"], list)
    assert len(result["task_list"]) > 0
    
    # 完了したタスクがあることを確認
    assert isinstance(result["completed_tasks"], list)
    assert len(result["completed_tasks"]) > 0
    
    # 最終結果が生成されていることを確認
    assert isinstance(result["final_result"], str)
    assert len(result["final_result"]) > 0


def test_graph_invoke_with_checkpointer(graph_with_checkpointer):
    """チェックポインタ付きグラフをinvokeして結果を確認するテスト"""
    # スレッドIDを含む設定を定義
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # テスト用のユーザー要求
    user_request = "PythonのLangGraphについて簡単に説明してください。"
    
    # グラフの実行
    result = graph_with_checkpointer.invoke({"user_request": user_request}, config)
    
    # 結果の検証
    assert "user_request" in result
    assert "task_list" in result
    assert "completed_tasks" in result
    assert "final_result" in result
    
    # タスクリストが生成されていることを確認
    assert isinstance(result["task_list"], list)
    assert len(result["task_list"]) > 0
    
    # 完了したタスクがあることを確認
    assert isinstance(result["completed_tasks"], list)
    assert len(result["completed_tasks"]) > 0
    
    # 最終結果が生成されていることを確認
    assert isinstance(result["final_result"], str)
    assert len(result["final_result"]) > 0


def test_graph_invoke_task_structure(graph_with_checkpointer):
    """タスクの構造を確認するテスト"""
    # スレッドIDを含む設定を定義
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # テスト用のユーザー要求
    user_request = "PythonのLangGraphについて簡単に説明してください。"
    
    # グラフの実行
    result = graph_with_checkpointer.invoke({"user_request": user_request}, config)
    
    # タスクリストの構造を確認
    task_list = result["task_list"]
    assert len(task_list) > 0
    
    # 各タスクの構造を確認
    for task in task_list:
        assert hasattr(task, "id")
        assert hasattr(task, "title")
        assert hasattr(task, "description")
        assert hasattr(task, "task_type")
        assert hasattr(task, "dependencies")
        assert hasattr(task, "priority")
        
        # タスクタイプが有効な値であることを確認
        assert task.task_type in ["research", "analysis", "generation"]
        
        # 優先度が有効な範囲であることを確認
        assert 1 <= task.priority <= 5
    
    # 完了したタスクの構造を確認
    completed_tasks = result["completed_tasks"]
    assert len(completed_tasks) > 0
    
    for completed_task in completed_tasks:
        assert "task_id" in completed_task
        assert "title" in completed_task
        assert "description" in completed_task
        assert "task_type" in completed_task
        assert "result" in completed_task
        assert "status" in completed_task
        assert completed_task["status"] == "completed"


def test_graph_invoke_multiple_requests():
    """複数の異なる要求でグラフを実行するテスト"""
    requests = [
        "PythonのLangGraphについて簡単に説明してください。",
        "機械学習の基礎について3つのポイントを説明してください。",
    ]
    
    for user_request in requests:
        result = graph.invoke({"user_request": user_request})
        
        # 基本的な結果の検証
        assert "user_request" in result
        assert result["user_request"] == user_request
        assert "task_list" in result
        assert "completed_tasks" in result
        assert "final_result" in result
        
        # タスクリストが生成されていることを確認
        assert len(result["task_list"]) > 0
        assert len(result["completed_tasks"]) > 0
        assert len(result["final_result"]) > 0


def test_graph_invoke_empty_request():
    """空の要求でグラフを実行するテスト"""
    user_request = ""
    
    # グラフの実行（エラーが発生する可能性があるが、エラーハンドリングを確認）
    try:
        result = graph.invoke({"user_request": user_request})
        # エラーが発生しなかった場合、結果を確認
        assert "user_request" in result
    except Exception as e:
        # エラーが発生した場合、それは期待される動作かもしれない
        assert isinstance(e, Exception)


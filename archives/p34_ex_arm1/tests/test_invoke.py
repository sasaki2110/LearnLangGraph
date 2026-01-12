"""
invokeのテスト

このテストは、グラフが正常にinvokeできることを確認します。
"""

import sys
from pathlib import Path

# p34_ex_arm1ディレクトリをパスに追加
p34_dir = Path(__file__).parent.parent
sys.path.insert(0, str(p34_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_invoke():
    """グラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力
    initial_state = {
        "messages": [HumanMessage(content="赤いコップを青いトレイに置いて")],
        "gripper_position_x": 0.0,
        "gripper_position_y": 0.0,
        "gripper_position_z": 0.0,
        "gripper_state": "open",
        "instruction": None,
        "task_completed": False
    }
    
    print("=" * 60)
    print("invokeテスト開始")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print("\n" + "-" * 60)
    
    # invokeを実行（再帰制限を50に増やす）
    config = {"recursion_limit": 50}
    print(f"再帰制限: {config['recursion_limit']}")
    result = graph.invoke(initial_state, config=config)
    
    print("\n最終状態:")
    print("-" * 60)
    print(f"  instruction: {result.get('instruction', None)}")
    print(f"  タスクリスト: {len(result.get('task_list', []))}個のタスク")
    print(f"  完了タスク: {len(result.get('completed_tasks', []))}個")
    print(f"  グリッパー位置: ({result.get('gripper_position_x', 0.0)}, {result.get('gripper_position_y', 0.0)}, {result.get('gripper_position_z', 0.0)})")
    print(f"  グリッパー状態: {result.get('gripper_state', None)}")
    print(f"  task_completed: {result.get('task_completed', False)}")
    print("=" * 60)
    
    # 結果の検証
    assert "instruction" in result, "instructionが設定されている必要があります"
    assert result["instruction"] is not None, "instructionがNoneでない必要があります"
    assert len(result["instruction"]) > 0, "instructionが空でない必要があります"
    
    # タスクリストが生成されていることを確認
    if "task_list" in result and result["task_list"]:
        print(f"  生成されたタスク:")
        for i, task in enumerate(result["task_list"], 1):
            print(f"    {i}. {task.id}: {task.description}")
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)


if __name__ == "__main__":
    print("test_invoke を実行します...")
    test_invoke()
    
    print("\n" + "=" * 60)
    print("✓ すべてのテストが完了しました")

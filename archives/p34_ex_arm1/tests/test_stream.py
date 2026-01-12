"""
ストリーミングのテスト

このテストは、グラフが正常にstreamできることを確認します。
stream_mode="updates"を使用して、各ノード後の状態更新をストリームします。
"""

import sys
from pathlib import Path

# p34_ex_arm1ディレクトリをパスに追加
p34_dir = Path(__file__).parent.parent
sys.path.insert(0, str(p34_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_stream_updates():
    """グラフが正常にstreamできることを確認するテスト（updatesモード）"""
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
    print("streamテスト開始 (stream_mode='updates')")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  グリッパー位置: ({initial_state['gripper_position_x']}, {initial_state['gripper_position_y']}, {initial_state['gripper_position_z']})")
    print(f"  グリッパー状態: {initial_state['gripper_state']}")
    print("\n" + "-" * 60)
    print("\nストリーミング出力:")
    print("-" * 60)
    
    # streamを実行
    chunks = []
    actual_nodes = []
    
    for chunk in graph.stream(
        initial_state,
        stream_mode="updates",  # 各ノード後のグラフ状態の更新のみをストリーム
    ):
        chunks.append(chunk)
        node_name = list(chunk.keys())[0]
        actual_nodes.append(node_name)
        update = chunk[node_name]
        
        print(f"\n[ノード: {node_name}]")
        for key, value in update.items():
            if key == "messages" and isinstance(value, list):
                # messagesの場合は内容を表示
                print(f"  {key}: {len(value)}個のメッセージ")
                for msg in value:
                    if hasattr(msg, "content"):
                        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                        print(f"    - {type(msg).__name__}: {content_preview}")
            elif key == "instruction" and value:
                # instructionの場合は最初の50文字を表示
                instruction_preview = value[:50] + "..." if len(value) > 50 else value
                print(f"  {key}: {instruction_preview}")
            elif key == "task_list" and value:
                print(f"  {key}: {len(value)}個のタスク")
            elif key == "completed_tasks" and value:
                print(f"  {key}: {len(value)}個のタスクが完了")
            elif key == "current_task_id" and value:
                print(f"  {key}: {value}")
            elif key == "object_positions" and value:
                print(f"  {key}: {value}")
            elif key in ["gripper_position_x", "gripper_position_y", "gripper_position_z"] and value is not None:
                print(f"  {key}: {value}")
            elif key == "gripper_state" and value:
                print(f"  {key}: {value}")
            elif key == "task_completed":
                print(f"  {key}: {value}")
            elif value is not None:
                print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert len(chunks) > 0, "ストリームチャンクが生成されている必要があります"
    
    # extractorノードが実行されていることを確認
    extractor_found = any("extractor" in chunk for chunk in chunks)
    assert extractor_found, "extractorノードが実行されている必要があります"
    
    # plannerノードが実行されていることを確認
    planner_found = any("planner" in chunk for chunk in chunks)
    assert planner_found, "plannerノードが実行されている必要があります"
    
    # task_selectorノードが実行されていることを確認
    task_selector_found = any("task_selector" in chunk for chunk in chunks)
    assert task_selector_found, "task_selectorノードが実行されている必要があります"
    
    # tool_executorノードが実行されていることを確認
    tool_executor_found = any("tool_executor" in chunk for chunk in chunks)
    assert tool_executor_found, "tool_executorノードが実行されている必要があります"
    
    # task_updaterノードが実行されていることを確認
    task_updater_found = any("task_updater" in chunk for chunk in chunks)
    assert task_updater_found, "task_updaterノードが実行されている必要があります"
    
    # verifierノードが実行されていることを確認
    verifier_found = any("verifier" in chunk for chunk in chunks)
    assert verifier_found, "verifierノードが実行されている必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)


def test_stream_node_order():
    """ノードが正しい順序で実行されることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    initial_state = {
        "messages": [HumanMessage(content="ボールを箱に置いて")],
        "gripper_position_x": 0.0,
        "gripper_position_y": 0.0,
        "gripper_position_z": 0.0,
        "gripper_state": "open",
        "instruction": None,
        "task_completed": False
    }
    
    actual_order = []
    
    for chunk in graph.stream(
        initial_state,
        stream_mode="updates",
    ):
        node_name = list(chunk.keys())[0]
        actual_order.append(node_name)
    
    # 最初のノードはextractorである必要がある
    assert actual_order[0] == "extractor", f"最初のノードは 'extractor' である必要がありますが、'{actual_order[0]}' でした"
    
    # extractorの次はplannerである必要がある
    assert "planner" in actual_order, "plannerノードが実行されている必要があります"
    
    # plannerの次はtask_selectorである必要がある
    assert "task_selector" in actual_order, "task_selectorノードが実行されている必要があります"
    
    # task_selectorの次はtool_executorである必要がある
    assert "tool_executor" in actual_order, "tool_executorノードが実行されている必要があります"
    
    # tool_executorの次はtask_updaterである必要がある
    assert "task_updater" in actual_order, "task_updaterノードが実行されている必要があります"
    
    # task_updaterの次はverifierである必要がある
    assert "verifier" in actual_order, "verifierノードが実行されている必要があります"


if __name__ == "__main__":
    print("test_stream_updates を実行します...")
    test_stream_updates()
    
    print("\n" + "=" * 60)
    print("test_stream_node_order を実行します...")
    test_stream_node_order()
    
    print("\n" + "=" * 60)
    print("✓ すべてのテストが完了しました")

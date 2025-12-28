"""
tasksのストリーミングを確認するテスト

このテストは、tasksが段階的にストリーミングされることを確認します。
create_taskノードでin_progress状態、execute_taskノードでcompleted状態になることを確認します。
"""

import sys
from pathlib import Path

# p31_streamingディレクトリをパスに追加
p31_dir = Path(__file__).parent.parent
sys.path.insert(0, str(p31_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_stream_tasks_progression():
    """tasksが段階的にストリーミングされることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    initial_state = {
        "messages": [HumanMessage(content="チョコレート")],
        "topic": None,
        "tasks": None,
        "joke": None
    }
    
    print("=" * 60)
    print("tasksストリーミングテスト開始 (stream_mode='updates')")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  tasks: {initial_state['tasks']}")
    print("\n" + "-" * 60)
    print("\nストリーミング出力:")
    print("-" * 60)
    
    chunks = []
    tasks_updates = []
    
    for chunk in graph.stream(
        initial_state,
        stream_mode="updates",
    ):
        chunks.append(chunk)
        node_name = list(chunk.keys())[0]
        update = chunk[node_name]
        
        print(f"\n[ノード: {node_name}]")
        
        # @taskデコレータでラップされたタスク関数の場合は、出力が文字列になる
        if isinstance(update, str):
            print(f"  タスク結果: {update[:50]}...")
            continue
        
        # tasksが含まれている場合は記録
        if isinstance(update, dict) and "tasks" in update:
            tasks_list = update["tasks"]
            # タスクリストのコピーを作成して記録（状態が変更されないように）
            tasks_copy = []
            for task in tasks_list:
                if isinstance(task, dict):
                    tasks_copy.append(task.copy())
                else:
                    tasks_copy.append(task)
            tasks_updates.append({
                "node": node_name,
                "tasks": tasks_copy
            })
            print(f"  tasks: {len(tasks_list)}個のタスク")
            for task in tasks_list:
                if isinstance(task, dict):
                    status = task.get('status', 'N/A')
                    title = task.get('title', 'N/A')
                    print(f"    - {title}: {status}")
        
        # その他の更新も表示
        if isinstance(update, dict):
            for key, value in update.items():
                if key != "tasks":
                    if key == "topic" and value:
                        topic_preview = value[:50] + "..." if len(value) > 50 else value
                        print(f"  {key}: {topic_preview}")
                    elif key == "joke" and value:
                        joke_preview = value[:50] + "..." if len(value) > 50 else value
                        print(f"  {key}: {joke_preview}")
                    elif key == "messages" and isinstance(value, list):
                        print(f"  {key}: {len(value)}個のメッセージ")
    
    print("\n" + "=" * 60)
    print("tasksの更新履歴:")
    print("-" * 60)
    for i, update in enumerate(tasks_updates):
        print(f"\n{i+1}. [{update['node']}]")
        for task in update['tasks']:
            if isinstance(task, dict):
                print(f"   - {task.get('title', 'N/A')}: {task.get('status', 'N/A')}")
    
    print("\n" + "=" * 60)
    
    # 検証
    assert len(tasks_updates) >= 2, f"tasksが少なくとも2回更新される必要があります（実際: {len(tasks_updates)}回）"
    
    # 最初の更新（create_task）でin_progress状態であることを確認
    first_update = tasks_updates[0]
    assert first_update["node"] == "create_task", f"最初の更新は'create_task'ノードである必要があります（実際: {first_update['node']}）"
    assert len(first_update["tasks"]) > 0, "タスクリストが空でない必要があります"
    assert first_update["tasks"][0].get("status") == "in_progress", \
        f"create_taskノードではタスクがin_progress状態である必要があります（実際: {first_update['tasks'][0].get('status')}）"
    
    # 最後の更新（execute_task）でcompleted状態であることを確認
    last_update = tasks_updates[-1]
    assert last_update["node"] == "execute_task", f"最後の更新は'execute_task'ノードである必要があります（実際: {last_update['node']}）"
    assert len(last_update["tasks"]) > 0, "タスクリストが空でない必要があります"
    assert last_update["tasks"][0].get("status") == "completed", \
        f"execute_taskノードではタスクがcompleted状態である必要があります（実際: {last_update['tasks'][0].get('status')}）"
    
    print("✓ tasksが段階的にストリーミングされることを確認しました")
    print("=" * 60)


if __name__ == "__main__":
    test_stream_tasks_progression()


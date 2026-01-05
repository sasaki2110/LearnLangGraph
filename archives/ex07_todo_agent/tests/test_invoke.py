"""
invokeのテスト

このテストは、グラフが正常にinvokeできることを確認します。
ストリーミングではなく、通常のinvokeを使用してテストします。

注意: このテストを実行するには、以下の依存関係がインストールされている必要があります:
- langchain
- langchain-openai
- langgraph
- python-dotenv (オプション)
"""
import sys
from pathlib import Path

# ex07_todo_agentディレクトリをパスに追加
ex07_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex07_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_invoke():
    """グラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力（タスク追加）
    initial_state = {
        "messages": [HumanMessage(content="資料作成を1月10日までに登録して")],
        "todo_list": [],
        "recent_change": None,
        "operation": None,
        "extracted_data": None
    }
    
    print("=" * 60)
    print("invokeテスト開始")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  todo_list: {initial_state['todo_list']}")
    print(f"  recent_change: {initial_state['recent_change']}")
    print("\n" + "-" * 60)
    
    # invokeを実行
    result = graph.invoke(initial_state)
    
    print("\n実行結果:")
    print("-" * 60)
    print(f"  todo_list数: {len(result.get('todo_list', []))}")
    print(f"  recent_change: {result.get('recent_change', 'N/A')}")
    
    # TODOリストを表示
    todo_list = result.get('todo_list', [])
    if todo_list:
        print(f"\nTODOリスト:")
        for todo in todo_list:
            print(f"  - ID: {todo.get('task_id', 'N/A')[:8]}...")
            print(f"    内容: {todo.get('content', 'N/A')}")
            print(f"    期限: {todo.get('deadline', 'N/A')}")
            print(f"    ステータス: {todo.get('status', 'N/A')}")
    
    # 最終メッセージを表示
    messages = result.get('messages', [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            print(f"\n最終回答 (最初の200文字):")
            print(f"  {last_message.content[:200]}...")
    
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert "todo_list" in result, "結果に'todo_list'が含まれている必要があります"
    assert "recent_change" in result, "結果に'recent_change'が含まれている必要があります"
    assert isinstance(result["todo_list"], list), "todo_listはリストである必要があります"
    
    # 最終メッセージが存在することを確認
    assert len(messages) > 0, "メッセージが存在する必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)
    
    # pytestのテスト関数はNoneを返すべき


if __name__ == "__main__":
    # 直接実行時もNoneを返す（pytestの警告を避けるため）
    test_invoke()


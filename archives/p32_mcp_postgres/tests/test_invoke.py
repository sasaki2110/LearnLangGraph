"""
invokeのテスト

このテストは、グラフが正常にinvokeできることを確認します。
ストリーミングではなく、通常のinvokeを使用してテストします。

注意: このテストを実行するには、以下の依存関係がインストールされている必要があります:
- langchain
- langchain-openai
- langgraph
- langchain-mcp-adapters
- python-dotenv (オプション)
"""
import sys
from pathlib import Path

# p32_mcp_postgresディレクトリをパスに追加
p32_dir = Path(__file__).parent.parent
sys.path.insert(0, str(p32_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_invoke():
    """グラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力（Vercel AI SDKのチャット形式を想定）
    initial_state = {
        "messages": [HumanMessage(content="データベースのテーブル一覧を表示してください")],
        "topic": None,
        "query_result": None
    }
    
    print("=" * 60)
    print("invokeテスト開始")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  topic: {initial_state['topic']}")
    print(f"  query_result: {initial_state['query_result']}")
    print("\n" + "-" * 60)
    
    # invokeを実行
    result = graph.invoke(initial_state)
    
    print("\n実行結果:")
    print("-" * 60)
    print(f"  topic: {result.get('topic', 'N/A')}")
    print(f"  query_result: {result.get('query_result', 'N/A')}")
    print(f"  messages数: {len(result.get('messages', []))}")
    if result.get('messages'):
        last_msg = result['messages'][-1]
        if hasattr(last_msg, 'content'):
            print(f"  最後のメッセージ: {last_msg.content[:100]}...")
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert "messages" in result, "結果に'messages'が含まれている必要があります"
    assert len(result["messages"]) > 0, "メッセージが生成されている必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)


if __name__ == "__main__":
    # 直接実行時もNoneを返す（pytestの警告を避けるため）
    test_invoke()


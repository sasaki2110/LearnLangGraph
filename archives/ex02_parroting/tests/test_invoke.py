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

# ex02_parrotingディレクトリをパスに追加
ex02_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex02_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_invoke():
    """グラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力
    initial_state = {
        "messages": [HumanMessage(content="こんにちは、元気ですか？")],
        "message": None,
        "char_count": 0
    }
    
    print("=" * 60)
    print("invokeテスト開始")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  message: {initial_state['message']}")
    print(f"  char_count: {initial_state['char_count']}")
    print("\n" + "-" * 60)
    
    # invokeを実行
    result = graph.invoke(initial_state)
    
    print("\n実行結果:")
    print("-" * 60)
    print(f"  message: {result.get('message', 'N/A')}")
    print(f"  char_count: {result.get('char_count', 'N/A')}")
    print(f"  messages数: {len(result.get('messages', []))}")
    if result.get('messages'):
        print(f"  最後のメッセージ: {result['messages'][-1].content[:200] if hasattr(result['messages'][-1], 'content') else str(result['messages'][-1])[:200]}")
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert "message" in result, "結果に'message'が含まれている必要があります"
    assert "char_count" in result, "結果に'char_count'が含まれている必要があります"
    assert "messages" in result, "結果に'messages'が含まれている必要があります"
    assert result["message"] is not None, "メッセージが設定されている必要があります"
    assert len(result["message"]) > 0, "メッセージが空でない必要があります"
    assert result["char_count"] > 0, "文字数がカウントされている必要があります"
    assert len(result["messages"]) > 0, "メッセージが生成されている必要があります"
    
    # 最後のメッセージに文字数情報が含まれているか確認
    last_message = result["messages"][-1]
    if hasattr(last_message, "content"):
        assert "文字です" in last_message.content or "文字数" in last_message.content, "メッセージに文字数情報が含まれている必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)


if __name__ == "__main__":
    # 直接実行時もNoneを返す（pytestの警告を避けるため）
    test_invoke()


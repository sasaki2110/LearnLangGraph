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

# ex01_helloディレクトリをパスに追加
ex01_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex01_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_invoke_japanese():
    """日本語メッセージでグラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力（日本語）
    initial_state = {
        "messages": [HumanMessage(content="こんにちは")],
        "language": None
    }
    
    print("=" * 60)
    print("invokeテスト開始（日本語）")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  language: {initial_state['language']}")
    print("\n" + "-" * 60)
    
    # invokeを実行
    result = graph.invoke(initial_state)
    
    print("\n実行結果:")
    print("-" * 60)
    print(f"  language: {result.get('language', 'N/A')}")
    print(f"  messages数: {len(result.get('messages', []))}")
    if result.get('messages'):
        print(f"  最後のメッセージ: {result['messages'][-1].content[:100] if hasattr(result['messages'][-1], 'content') else str(result['messages'][-1])[:100]}")
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert "language" in result, "結果に'language'が含まれている必要があります"
    assert "messages" in result, "結果に'messages'が含まれている必要があります"
    assert len(result["messages"]) > 0, "メッセージが生成されている必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)


def test_invoke_english():
    """英語メッセージでグラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力（英語）
    initial_state = {
        "messages": [HumanMessage(content="Hello")],
        "language": None
    }
    
    print("=" * 60)
    print("invokeテスト開始（英語）")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  language: {initial_state['language']}")
    print("\n" + "-" * 60)
    
    # invokeを実行
    result = graph.invoke(initial_state)
    
    print("\n実行結果:")
    print("-" * 60)
    print(f"  language: {result.get('language', 'N/A')}")
    print(f"  messages数: {len(result.get('messages', []))}")
    if result.get('messages'):
        print(f"  最後のメッセージ: {result['messages'][-1].content[:100] if hasattr(result['messages'][-1], 'content') else str(result['messages'][-1])[:100]}")
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert "language" in result, "結果に'language'が含まれている必要があります"
    assert "messages" in result, "結果に'messages'が含まれている必要があります"
    assert len(result["messages"]) > 0, "メッセージが生成されている必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)


if __name__ == "__main__":
    # 直接実行時もNoneを返す（pytestの警告を避けるため）
    test_invoke_japanese()
    print("\n")
    test_invoke_english()


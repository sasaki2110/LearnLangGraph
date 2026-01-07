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

# p33_ui_simpleディレクトリをパスに追加
p33_dir = Path(__file__).parent.parent
sys.path.insert(0, str(p33_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_invoke():
    """グラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力（Vercel AI SDKのチャット形式を想定）
    initial_state = {
        "messages": [HumanMessage(content="ジョークを生成してください")],
        "jokes": []
    }
    
    print("=" * 60)
    print("invokeテスト開始")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  jokes: {initial_state['jokes']}")
    print("\n" + "-" * 60)
    
    # invokeを実行
    result = graph.invoke(initial_state)
    
    print("\n実行結果:")
    print("-" * 60)
    print(f"  jokes数: {len(result.get('jokes', []))}")
    print(f"  jokes: {result.get('jokes', [])}")
    print(f"  messages数: {len(result.get('messages', []))}")
    if result.get('messages'):
        print(f"  最終メッセージ: {result['messages'][-1].content[:100]}...")
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert "jokes" in result, "結果に'jokes'が含まれている必要があります"
    assert "messages" in result, "結果に'messages'が含まれている必要があります"
    assert len(result["jokes"]) >= 3, "あ行・か行・さ行のジョークが生成されている必要があります（最低3つ）"
    assert len(result["messages"]) > 0, "メッセージが生成されている必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)
    
    # pytestのテスト関数はNoneを返すべき


if __name__ == "__main__":
    # 直接実行時もNoneを返す（pytestの警告を避けるため）
    test_invoke()


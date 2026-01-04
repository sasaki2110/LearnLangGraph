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

# ex03_censorshipディレクトリをパスに追加
ex03_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex03_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_invoke():
    """グラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力（NGワードを含まないケース）
    initial_state = {
        "messages": [HumanMessage(content="新しい日本一高速な、ゲーミングスマートフォンのキャッチコピー案")],
        "new_product_catchphrase_idea": None,
        "catchphrase": None,
        "has_ngword": None,
        "improvement_points": None
    }
    
    print("=" * 60)
    print("invokeテスト開始")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  new_product_catchphrase_idea: {initial_state['new_product_catchphrase_idea']}")
    print(f"  catchphrase: {initial_state['catchphrase']}")
    print(f"  has_ngword: {initial_state['has_ngword']}")
    print(f"  improvement_points: {initial_state['improvement_points']}")
    print("\n" + "-" * 60)
    
    # invokeを実行
    result = graph.invoke(initial_state)
    
    print("\n実行結果:")
    print("-" * 60)
    print(f"  new_product_catchphrase_idea: {result.get('new_product_catchphrase_idea', 'N/A')}")
    print(f"  catchphrase: {result.get('catchphrase', 'N/A')}")
    print(f"  has_ngword: {result.get('has_ngword', 'N/A')}")
    print(f"  improvement_points: {result.get('improvement_points', 'N/A')}")
    print(f"  messages数: {len(result.get('messages', []))}")
    if result.get('messages'):
        print(f"  最後のメッセージ: {result['messages'][-1].content[:200] if hasattr(result['messages'][-1], 'content') else str(result['messages'][-1])[:200]}")
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert "new_product_catchphrase_idea" in result, "結果に'new_product_catchphrase_idea'が含まれている必要があります"
    assert "catchphrase" in result, "結果に'catchphrase'が含まれている必要があります"
    assert "has_ngword" in result, "結果に'has_ngword'が含まれている必要があります"
    assert result["new_product_catchphrase_idea"] is not None, "アイデアが設定されている必要があります"
    assert result["catchphrase"] is not None, "キャッチコピーが生成されている必要があります"
    assert result["has_ngword"] is False, "NGワードが含まれていない必要があります"
    assert len(result["messages"]) > 0, "メッセージが生成されている必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)


if __name__ == "__main__":
    # 直接実行時もNoneを返す（pytestの警告を避けるため）
    test_invoke()


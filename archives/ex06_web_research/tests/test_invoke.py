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

# ex06_web_researchディレクトリをパスに追加
ex06_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex06_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_invoke():
    """グラフが正常にinvokeできることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力（「最近のAI動向」をテーマとして）
    initial_state = {
        "messages": [HumanMessage(content="最近のAI動向について調べてまとめて")],
        "theme": None,
        "survey_results": [],
        "is_sufficient": None,
        "tool_count": 0,
        "llm_call_count": 0
    }
    
    print("=" * 60)
    print("invokeテスト開始")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  theme: {initial_state['theme']}")
    print(f"  survey_results: {initial_state['survey_results']}")
    print(f"  is_sufficient: {initial_state['is_sufficient']}")
    print(f"  tool_count: {initial_state['tool_count']}")
    print(f"  llm_call_count: {initial_state['llm_call_count']}")
    print("\n" + "-" * 60)
    
    # invokeを実行
    result = graph.invoke(initial_state)
    
    print("\n実行結果:")
    print("-" * 60)
    print(f"  theme: {result.get('theme', 'N/A')}")
    print(f"  survey_results数: {len(result.get('survey_results', []))}")
    print(f"  is_sufficient: {result.get('is_sufficient', 'N/A')}")
    print(f"  tool_count: {result.get('tool_count', 'N/A')}")
    print(f"  llm_call_count: {result.get('llm_call_count', 'N/A')}")
    
    # 最終メッセージを表示
    messages = result.get('messages', [])
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            print(f"\n最終回答 (最初の200文字):")
            print(f"  {last_message.content[:200]}...")
    
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert "theme" in result, "結果に'theme'が含まれている必要があります"
    assert "survey_results" in result, "結果に'survey_results'が含まれている必要があります"
    assert "is_sufficient" in result, "結果に'is_sufficient'が含まれている必要があります"
    assert result["theme"] is not None, "テーマが設定されている必要があります"
    assert len(result["theme"]) > 0, "テーマが空でない必要があります"
    assert len(result["survey_results"]) > 0, "調査結果が1つ以上ある必要があります"
    
    # 最終メッセージが存在することを確認
    assert len(messages) > 0, "メッセージが存在する必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)
    
    # pytestのテスト関数はNoneを返すべき


if __name__ == "__main__":
    # 直接実行時もNoneを返す（pytestの警告を避けるため）
    test_invoke()


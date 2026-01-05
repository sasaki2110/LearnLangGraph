"""
基本的な動作確認テスト

このテストは、グラフが正常に動作することを確認します。
"""
import sys
from pathlib import Path

# ex04_calculatorディレクトリをパスに追加
ex04_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex04_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_add():
    """加算のテスト"""
    from langchain.messages import HumanMessage
    
    print("=" * 60)
    print("加算テスト")
    print("=" * 60)
    
    result = graph.invoke({
        "messages": [HumanMessage(content="5 + 3 を計算してください")]
    })
    
    print(f"\n結果:")
    print(f"  メッセージ数: {len(result['messages'])}")
    if result['messages']:
        last_message = result['messages'][-1]
        print(f"  最後のメッセージ: {last_message.content if hasattr(last_message, 'content') else str(last_message)}")
    
    print("\n" + "-" * 60 + "\n")


def test_multiply():
    """乗算のテスト"""
    from langchain.messages import HumanMessage
    
    print("=" * 60)
    print("乗算テスト")
    print("=" * 60)
    
    result = graph.invoke({
        "messages": [HumanMessage(content="10 * 7 を計算してください")]
    })
    
    print(f"\n結果:")
    print(f"  メッセージ数: {len(result['messages'])}")
    if result['messages']:
        last_message = result['messages'][-1]
        print(f"  最後のメッセージ: {last_message.content if hasattr(last_message, 'content') else str(last_message)}")
    
    print("\n" + "-" * 60 + "\n")


def test_subtract():
    """減算のテスト"""
    from langchain.messages import HumanMessage
    
    print("=" * 60)
    print("減算テスト")
    print("=" * 60)
    
    result = graph.invoke({
        "messages": [HumanMessage(content="20 - 8 を計算してください")]
    })
    
    print(f"\n結果:")
    print(f"  メッセージ数: {len(result['messages'])}")
    if result['messages']:
        last_message = result['messages'][-1]
        print(f"  最後のメッセージ: {last_message.content if hasattr(last_message, 'content') else str(last_message)}")
    
    print("\n" + "-" * 60 + "\n")


def test_divide():
    """除算のテスト"""
    from langchain.messages import HumanMessage
    
    print("=" * 60)
    print("除算テスト")
    print("=" * 60)
    
    result = graph.invoke({
        "messages": [HumanMessage(content="15 / 3 を計算してください")]
    })
    
    print(f"\n結果:")
    print(f"  メッセージ数: {len(result['messages'])}")
    if result['messages']:
        last_message = result['messages'][-1]
        print(f"  最後のメッセージ: {last_message.content if hasattr(last_message, 'content') else str(last_message)}")
    
    print("\n" + "-" * 60 + "\n")


def test_stream():
    """ストリーミングのテスト"""
    from langchain.messages import HumanMessage
    
    print("=" * 60)
    print("ストリーミングテスト")
    print("=" * 60)
    
    print("\nストリーミング出力:")
    print("-" * 60)
    
    for chunk in graph.stream({
        "messages": [HumanMessage(content="12 + 8 を計算してください")]
    }, stream_mode="updates"):
        print(f"\nチャンク: {chunk}")
    
    print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ex04_calculator テストスイート")
    print("=" * 60 + "\n")
    
    try:
        test_add()
        test_multiply()
        test_subtract()
        test_divide()
        test_stream()
        
        print("=" * 60)
        print("✅ すべてのテストが完了しました")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


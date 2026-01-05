"""
基本的な動作確認テスト

このテストは、グラフが正常に動作することを確認します。
注意: 中断（interrupt）機能を使用するため、LangGraph Studioで実行することを推奨します。
"""
import sys
from pathlib import Path

# ex99_sns_post_editorディレクトリをパスに追加
ex99_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex99_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_theme_extraction():
    """テーマ取得のテスト"""
    from langchain.messages import HumanMessage
    
    print("=" * 60)
    print("テーマ取得テスト")
    print("=" * 60)
    
    test_theme = "今日の天気について"
    
    # 注意: 中断機能を使用するため、完全な実行はできません
    # ここでは初期状態のみを確認します
    initial_state = {
        "messages": [HumanMessage(content=test_theme)]
    }
    
    print(f"\n初期状態:")
    print(f"  メッセージ数: {len(initial_state['messages'])}")
    print(f"  テーマ: {test_theme}")
    
    print("\n" + "-" * 60)
    print("注意: このエージェントは中断（interrupt）機能を使用します。")
    print("完全なテストは、LangGraph Studioで実行してください。")
    print("-" * 60 + "\n")


def test_graph_structure():
    """グラフ構造の確認"""
    print("=" * 60)
    print("グラフ構造の確認")
    print("=" * 60)
    
    print("\nグラフが正常にコンパイルされていることを確認します...")
    
    if graph is None:
        print("❌ グラフがNoneです")
        return
    
    print("✅ グラフが正常にコンパイルされています")
    print(f"   グラフタイプ: {type(graph)}")
    
    print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ex99_sns_post_editor テストスイート")
    print("=" * 60 + "\n")
    
    try:
        test_theme_extraction()
        test_graph_structure()
        
        print("=" * 60)
        print("✅ 基本的なテストが完了しました")
        print("=" * 60)
        print("\n注意: 中断（interrupt）機能の完全なテストは、")
        print("LangGraph Studioで実行してください。")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


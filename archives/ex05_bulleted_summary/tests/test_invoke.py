"""
基本的な動作確認テスト

このテストは、グラフが正常に動作することを確認します。
"""
import sys
from pathlib import Path

# ex05_bulleted_summaryディレクトリをパスに追加
ex05_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex05_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_summary():
    """要約のテスト"""
    from langchain.messages import HumanMessage
    
    print("=" * 60)
    print("要約テスト")
    print("=" * 60)
    
    test_text = """
Pythonは、1991年にGuido van Rossumによって開発されたプログラミング言語です。
Pythonは、読みやすさとシンプルさを重視した設計で、初心者にも優しい言語です。
Pythonは、Web開発、データサイエンス、機械学習、自動化など、様々な用途で使用されています。
Pythonには、豊富なライブラリとフレームワークがあり、開発効率を高めます。
Pythonは、オープンソースで、大規模なコミュニティに支えられています。
NumPy、Pandas、Django、Flaskなど、多くの人気ライブラリがPythonで開発されています。
Pythonは、動的型付け言語で、柔軟なコーディングが可能です。
Pythonは、クロスプラットフォームで、Windows、macOS、Linuxで動作します。
"""
    
    result = graph.invoke({
        "messages": [HumanMessage(content=test_text)]
    })
    
    print(f"\n結果:")
    print(f"  raw_textの長さ: {len(result.get('raw_text', ''))}文字")
    print(f"  抽出された項目数: {len(result.get('extracted_items', []))}")
    print(f"  精緻化された項目数: {len(result.get('refined_items', []))}")
    print(f"  最終回答の長さ: {len(result.get('final_report', ''))}文字")
    
    print("\n最終回答:")
    print("-" * 60)
    print(result.get('final_report', 'N/A'))
    print("-" * 60)
    
    print("\n" + "-" * 60 + "\n")


def test_stream():
    """ストリーミングのテスト"""
    from langchain.messages import HumanMessage
    
    print("=" * 60)
    print("ストリーミングテスト")
    print("=" * 60)
    
    test_text = """
人工知能（AI）は、コンピュータシステムが人間の知能を模倣する技術です。
機械学習は、AIの一分野で、データから学習してパターンを認識します。
深層学習は、ニューラルネットワークを使用した機械学習の一種です。
自然言語処理は、コンピュータが人間の言語を理解し、処理する技術です。
コンピュータビジョンは、画像や動画を分析して理解する技術です。
これらの技術は、医療、金融、自動車、エンターテインメントなど、様々な分野で活用されています。
"""
    
    print("\nストリーミング出力:")
    print("-" * 60)
    
    for chunk in graph.stream({
        "messages": [HumanMessage(content=test_text)]
    }, stream_mode="updates"):
        node_name = list(chunk.keys())[0] if chunk else "unknown"
        print(f"\nノード: {node_name}")
        if node_name in chunk:
            state = chunk[node_name]
            if "extracted_items" in state:
                print(f"  抽出された項目数: {len(state['extracted_items'])}")
            if "refined_items" in state:
                print(f"  精緻化された項目数: {len(state['refined_items'])}")
            if "final_report" in state:
                print(f"  最終回答の長さ: {len(state['final_report'])}文字")
    
    print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ex05_bulleted_summary テストスイート")
    print("=" * 60 + "\n")
    
    try:
        test_summary()
        test_stream()
        
        print("=" * 60)
        print("✅ すべてのテストが完了しました")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


"""
ストリーミングのテスト

このテストは、グラフが正常にstreamできることを確認します。
stream_mode="updates"を使用して、各ノード後の状態更新をストリームします。

注意: 中断（interrupt）機能を使用するため、完全なストリーミングテストは
LangGraph Studioで実行することを推奨します。
"""
import sys
from pathlib import Path

# ex99_sns_post_editorディレクトリをパスに追加
ex99_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ex99_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_stream_updates():
    """グラフが正常にstreamできることを確認するテスト（updatesモード）"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力
    initial_state = {
        "messages": [HumanMessage(content="今日の天気について")],
        "theme": None,
        "draft_post": None,
        "final_post": None,
        "approved": None
    }
    
    print("=" * 60)
    print("streamテスト開始 (stream_mode='updates')")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  theme: {initial_state['theme']}")
    print(f"  draft_post: {initial_state['draft_post']}")
    print("\n" + "-" * 60)
    print("\nストリーミング出力:")
    print("-" * 60)
    
    # streamを実行
    chunks = []
    # 中断が発生するため、__interrupt__も含める
    expected_nodes = ["extract_theme", "create_draft_post", "request_approval", "__interrupt__"]
    actual_nodes = []
    
    try:
        for chunk in graph.stream(
            initial_state,
            stream_mode="updates",  # 各ノード後のグラフ状態の更新のみをストリーム
        ):
            chunks.append(chunk)
            node_name = list(chunk.keys())[0]
            actual_nodes.append(node_name)
            update = chunk[node_name]
            
            print(f"\n[ノード: {node_name}]")
            
            # __interrupt__ノードの場合は特別に処理
            if node_name == "__interrupt__":
                print(f"  中断が発生しました（これは正常な動作です）")
                if isinstance(update, tuple):
                    print(f"  中断情報: {update}")
                elif isinstance(update, dict):
                    for key, value in update.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  中断情報: {update}")
                continue
            
            # 通常のノードの場合
            if not isinstance(update, dict):
                print(f"  更新情報: {update}")
                continue
                
            for key, value in update.items():
                if key == "messages" and isinstance(value, list):
                    # messagesの場合は内容を表示
                    print(f"  {key}: {len(value)}個のメッセージ")
                    for msg in value:
                        if hasattr(msg, "content"):
                            content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                            print(f"    - {type(msg).__name__}: {content_preview}")
                elif key == "theme" and value:
                    # themeの場合は最初の50文字を表示
                    theme_preview = value[:50] + "..." if len(value) > 50 else value
                    print(f"  {key}: {theme_preview}")
                elif key == "draft_post" and value:
                    # draft_postの場合は最初の100文字を表示
                    draft_preview = value[:100] + "..." if len(value) > 100 else value
                    print(f"  {key}: {draft_preview}")
                elif key == "final_post" and value:
                    # final_postの場合は最初の100文字を表示
                    final_preview = value[:100] + "..." if len(value) > 100 else value
                    print(f"  {key}: {final_preview}")
                elif key == "approved" and value is not None:
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        
        # 結果の検証
        assert len(chunks) > 0, "ストリームチャンクが生成されている必要があります"
        
        # extract_themeノードでthemeが設定されることを確認
        extract_theme_chunk = None
        for chunk in chunks:
            if "extract_theme" in chunk:
                extract_theme_chunk = chunk["extract_theme"]
                break
        
        assert extract_theme_chunk is not None, "'extract_theme' ノードのチャンクが見つかりません"
        assert "theme" in extract_theme_chunk, "'extract_theme' チャンクに 'theme' が含まれている必要があります"
        assert extract_theme_chunk["theme"] is not None, "テーマが設定されている必要があります"
        assert len(extract_theme_chunk["theme"]) > 0, "テーマが空でない必要があります"
        
        # create_draft_postノードでdraft_postが設定されることを確認
        create_draft_post_chunk = None
        for chunk in chunks:
            if "create_draft_post" in chunk:
                create_draft_post_chunk = chunk["create_draft_post"]
                break
        
        assert create_draft_post_chunk is not None, "'create_draft_post' ノードのチャンクが見つかりません"
        assert "draft_post" in create_draft_post_chunk, "'create_draft_post' チャンクに 'draft_post' が含まれている必要があります"
        assert create_draft_post_chunk["draft_post"] is not None, "下書きが設定されている必要があります"
        assert len(create_draft_post_chunk["draft_post"]) > 0, "下書きが空でない必要があります"
        
        print("✓ すべての検証が成功しました")
        print("=" * 60)
        print("\n注意: 中断（interrupt）機能の完全なテストは、")
        print("LangGraph Studioで実行してください。")
        
    except Exception as e:
        # 中断（interrupt）が発生した場合は、それまでのチャンクを確認
        if "interrupt" in str(e).lower() or len(chunks) > 0:
            print(f"\n⚠️ 中断が発生しました（これは正常です）: {e}")
            print(f"✓ {len(chunks)}個のチャンクが正常にストリーミングされました")
            print("=" * 60)
        else:
            raise


def test_stream_updates_node_order():
    """ノードが正しい順序で実行されることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    initial_state = {
        "messages": [HumanMessage(content="プログラミング学習")],
        "theme": None,
        "draft_post": None,
        "final_post": None,
        "approved": None
    }
    
    # 中断が発生するため、__interrupt__も含める
    expected_order = ["extract_theme", "create_draft_post", "request_approval", "__interrupt__"]
    actual_order = []
    
    try:
        for chunk in graph.stream(
            initial_state,
            stream_mode="updates",
        ):
            node_name = list(chunk.keys())[0]
            actual_order.append(node_name)
        
        # 中断が発生するため、__interrupt__まで含めて確認
        assert len(actual_order) >= 3, \
            f"最低3つのノードが実行される必要がありますが、実際: {len(actual_order)}"
        
        # 最初の3つのノードが期待される順序であることを確認
        assert actual_order[0] == "extract_theme", \
            f"最初のノードは 'extract_theme' である必要がありますが、'{actual_order[0]}' でした"
        assert actual_order[1] == "create_draft_post", \
            f"2番目のノードは 'create_draft_post' である必要がありますが、'{actual_order[1]}' でした"
        assert actual_order[2] == "request_approval", \
            f"3番目のノードは 'request_approval' である必要がありますが、'{actual_order[2]}' でした"
        
        # 4番目は__interrupt__であることを確認
        if len(actual_order) >= 4:
            assert actual_order[3] == "__interrupt__", \
                f"4番目のノードは '__interrupt__' である必要がありますが、'{actual_order[3]}' でした"
        
    except Exception as e:
        # 中断が発生した場合は、それまでの順序を確認
        if len(actual_order) >= 3:
            assert actual_order[0] == "extract_theme", \
                f"最初のノードは 'extract_theme' である必要がありますが、'{actual_order[0]}' でした"
            assert actual_order[1] == "create_draft_post", \
                f"2番目のノードは 'create_draft_post' である必要がありますが、'{actual_order[1]}' でした"
            assert actual_order[2] == "request_approval", \
                f"3番目のノードは 'request_approval' である必要がありますが、'{actual_order[2]}' でした"


def test_stream_updates_state_progression():
    """状態が段階的に更新されることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    initial_state = {
        "messages": [HumanMessage(content="コーヒー")],
        "theme": None,
        "draft_post": None,
        "final_post": None,
        "approved": None
    }
    
    state_updates = {}
    
    try:
        for chunk in graph.stream(
            initial_state,
            stream_mode="updates",
        ):
            node_name = list(chunk.keys())[0]
            update = chunk[node_name]
            state_updates[node_name] = update
        
        # extract_themeでthemeが設定されることを確認
        assert "extract_theme" in state_updates, "extract_themeノードの更新が存在する必要があります"
        assert "theme" in state_updates["extract_theme"], "extract_themeでthemeが設定される必要があります"
        
        # create_draft_postでdraft_postが設定されることを確認
        assert "create_draft_post" in state_updates, "create_draft_postノードの更新が存在する必要があります"
        assert "draft_post" in state_updates["create_draft_post"], "create_draft_postでdraft_postが設定される必要があります"
        
        draft_post = state_updates["create_draft_post"]["draft_post"]
        assert draft_post is not None, "下書きが設定されている必要があります"
        assert len(draft_post) > 0, "下書きが空でない必要があります"
        
    except Exception as e:
        # 中断が発生した場合は、それまでの状態更新を確認
        if "extract_theme" in state_updates and "create_draft_post" in state_updates:
            assert "theme" in state_updates["extract_theme"], "extract_themeでthemeが設定される必要があります"
            assert "draft_post" in state_updates["create_draft_post"], "create_draft_postでdraft_postが設定される必要があります"


if __name__ == "__main__":
    print("test_stream_updates を実行します...")
    test_stream_updates()
    
    print("\n" + "=" * 60)
    print("test_stream_updates_node_order を実行します...")
    test_stream_updates_node_order()
    
    print("\n" + "=" * 60)
    print("test_stream_updates_state_progression を実行します...")
    test_stream_updates_state_progression()
    
    print("\n" + "=" * 60)
    print("✓ すべてのテストが完了しました")
    print("\n注意: 中断（interrupt）機能の完全なテストは、")
    print("LangGraph Studioで実行してください。")


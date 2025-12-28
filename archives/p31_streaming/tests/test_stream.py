"""
ストリーミングのテスト

このテストは、グラフが正常にstreamできることを確認します。
stream_mode="updates"を使用して、各ノード後の状態更新をストリームします。
"""

import sys
from pathlib import Path

# p31_streamingディレクトリをパスに追加
p31_dir = Path(__file__).parent.parent
sys.path.insert(0, str(p31_dir))

# テスト対象のグラフをインポート
from my_agent.agent import graph


def test_stream_updates():
    """グラフが正常にstreamできることを確認するテスト（updatesモード）"""
    from langchain.messages import HumanMessage
    
    # テスト用の入力（Vercel AI SDKのチャット形式を想定）
    initial_state = {
        "messages": [HumanMessage(content="アイスクリーム")],
        "topic": None,
        "joke": None
    }
    
    print("=" * 60)
    print("streamテスト開始 (stream_mode='updates')")
    print("=" * 60)
    print(f"\n初期状態:")
    print(f"  messages: {[msg.content for msg in initial_state['messages']]}")
    print(f"  topic: {initial_state['topic']}")
    print(f"  joke: {initial_state['joke']}")
    print("\n" + "-" * 60)
    print("\nストリーミング出力:")
    print("-" * 60)
    
    # streamを実行
    chunks = []
    expected_nodes = ["extract_topic", "refine_topic", "generate_joke"]
    actual_nodes = []
    
    for chunk in graph.stream(
        initial_state,
        stream_mode="updates",  # 各ノード後のグラフ状態の更新のみをストリーム
    ):
        chunks.append(chunk)
        node_name = list(chunk.keys())[0]
        actual_nodes.append(node_name)
        update = chunk[node_name]
        
        print(f"\n[ノード: {node_name}]")
        for key, value in update.items():
            if key == "messages" and isinstance(value, list):
                # messagesの場合は内容を表示
                print(f"  {key}: {len(value)}個のメッセージ")
                for msg in value:
                    if hasattr(msg, "content"):
                        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                        print(f"    - {type(msg).__name__}: {content_preview}")
            elif key == "topic" and value:
                # topicの場合は最初の50文字を表示
                topic_preview = value[:50] + "..." if len(value) > 50 else value
                print(f"  {key}: {topic_preview}")
            elif key == "joke" and value:
                # jokeの場合は最初の50文字を表示
                joke_preview = value[:50] + "..." if len(value) > 50 else value
                print(f"  {key}: {joke_preview}")
            else:
                print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    
    # 結果の検証
    assert len(chunks) > 0, "ストリームチャンクが生成されている必要があります"
    assert len(actual_nodes) == len(expected_nodes), f"期待されるノード数: {len(expected_nodes)}, 実際: {len(actual_nodes)}"
    
    # 各ノードが期待される順序で実行されていることを確認
    for i, expected_node in enumerate(expected_nodes):
        assert actual_nodes[i] == expected_node, f"ノード {i+1} は '{expected_node}' である必要がありますが、'{actual_nodes[i]}' でした"
    
    # generate_jokeノードでjokeとmessagesが設定されることを確認
    last_chunk = chunks[-1]
    assert "generate_joke" in last_chunk, "最後のチャンクは 'generate_joke' ノードからのものである必要があります"
    
    final_update = last_chunk["generate_joke"]
    assert "joke" in final_update or "messages" in final_update, \
        "最後のチャンクに 'joke' または 'messages' が含まれている必要があります"
    
    # jokeが含まれている場合は、ジョークが生成されていることを確認
    if "joke" in final_update:
        joke = final_update["joke"]
        assert joke is not None, "ジョークが設定されている必要があります"
        assert len(joke) > 0, "ジョークが空でない必要があります"
    
    # topicが精緻化されていることを確認
    topic_chunk = None
    for chunk in chunks:
        if "refine_topic" in chunk:
            topic_chunk = chunk["refine_topic"]
            break
    
    assert topic_chunk is not None, "'refine_topic' ノードのチャンクが見つかりません"
    assert "topic" in topic_chunk, "'refine_topic' チャンクに 'topic' が含まれている必要があります"
    assert topic_chunk["topic"] is not None, "トピックが設定されている必要があります"
    assert len(topic_chunk["topic"]) > 0, "トピックが空でない必要があります"
    
    print("✓ すべての検証が成功しました")
    print("=" * 60)
    
    # pytestのテスト関数はNoneを返すべき


def test_stream_updates_node_order():
    """ノードが正しい順序で実行されることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    initial_state = {
        "messages": [HumanMessage(content="プログラミング")],
        "topic": None,
        "joke": None
    }
    
    expected_order = ["extract_topic", "refine_topic", "generate_joke"]
    actual_order = []
    
    for chunk in graph.stream(
        initial_state,
        stream_mode="updates",
    ):
        node_name = list(chunk.keys())[0]
        actual_order.append(node_name)
    
    assert actual_order == expected_order, f"ノードの実行順序が正しくありません。期待: {expected_order}, 実際: {actual_order}"


def test_stream_updates_state_progression():
    """状態が段階的に更新されることを確認するテスト"""
    from langchain.messages import HumanMessage
    
    initial_state = {
        "messages": [HumanMessage(content="コーヒー")],
        "topic": None,
        "joke": None
    }
    
    state_updates = {}
    
    for chunk in graph.stream(
        initial_state,
        stream_mode="updates",
    ):
        node_name = list(chunk.keys())[0]
        update = chunk[node_name]
        state_updates[node_name] = update
    
    # extract_topicでtopicが設定されることを確認
    assert "extract_topic" in state_updates, "extract_topicノードの更新が存在する必要があります"
    assert "topic" in state_updates["extract_topic"], "extract_topicでtopicが設定される必要があります"
    
    # refine_topicでtopicが更新されることを確認
    assert "refine_topic" in state_updates, "refine_topicノードの更新が存在する必要があります"
    assert "topic" in state_updates["refine_topic"], "refine_topicでtopicが更新される必要があります"
    
    # generate_jokeでjokeとmessagesが設定されることを確認
    assert "generate_joke" in state_updates, "generate_jokeノードの更新が存在する必要があります"
    generate_joke_update = state_updates["generate_joke"]
    assert "joke" in generate_joke_update or "messages" in generate_joke_update, \
        "generate_jokeでjokeまたはmessagesが設定される必要があります"
    
    # jokeが含まれている場合は、ジョークが生成されていることを確認
    if "joke" in generate_joke_update:
        joke = generate_joke_update["joke"]
        assert joke is not None, "ジョークが設定されている必要があります"
        assert len(joke) > 0, "ジョークが空でない必要があります"


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


"""
グラフの統合テスト
"""
import pytest


def test_graph_invoke(config, initial_state, graph_with_checkpointer):
    """グラフをinvokeできることを確認"""
    # グラフを実行
    result = graph_with_checkpointer.invoke(initial_state, config)

    # 結果を確認
    assert "topic" in result
    assert "message" in result
    assert "steps" in result
    assert isinstance(result["topic"], str)
    assert isinstance(result["message"], str)
    assert isinstance(result["steps"], list)
    assert len(result["topic"]) > 0
    assert len(result["message"]) > 0
    assert len(result["steps"]) >= 2  # generate_topicとwrite_messageの2ステップ


def test_graph_get_state_history(config, initial_state, graph_with_checkpointer):
    """実行履歴を取得できることを確認"""
    # グラフを実行
    result = graph_with_checkpointer.invoke(initial_state, config)
    
    # 実行履歴を取得
    states = list(graph_with_checkpointer.get_state_history(config))
    
    # 履歴が存在することを確認
    assert len(states) > 0
    
    # 各チェックポイントを確認
    for state in states:
        assert state.config is not None
        assert "configurable" in state.config
        assert "thread_id" in state.config["configurable"]
        assert "checkpoint_id" in state.config["configurable"]


def test_time_travel_update_state(config, initial_state, graph_with_checkpointer):
    """タイムトラベルで状態を更新して再実行できることを確認"""
    # 1. グラフを実行
    result = graph_with_checkpointer.invoke(initial_state, config)

    print("")
    print("１回目の実行結果")
    print(initial_state)
    print(config)
    print(result)

    original_topic = result["topic"]
    original_message = result["message"]
    
    # 2. チェックポイントを特定
    states = list(graph_with_checkpointer.get_state_history(config))
    assert len(states) > 0
    
    # 3. 状態を更新（トピック生成後の状態を選択）
    # トピック生成後の状態を探す
    topic_state = None
    for state in states:
        if "topic" in state.values and "message" not in state.values:
            topic_state = state
            break
    
    if topic_state is None:
        # フォールバック: 最初の状態を使用
        topic_state = states[-1] if states else None
    
    assert topic_state is not None
    
    # 4. 状態を更新（トピックを変更）
    new_config = graph_with_checkpointer.update_state(
        topic_state.config,
        values={"topic": "chickens"}
    )
    
    # 新しい設定が作成されたことを確認
    assert new_config is not None
    assert "configurable" in new_config
    assert "thread_id" in new_config["configurable"]
    assert "checkpoint_id" in new_config["configurable"]
    
    # 5. チェックポイントから実行を再開
    new_result = graph_with_checkpointer.invoke(None, new_config)

    print("")
    print("２回目の実行結果")
    print(new_config)
    print(new_result)
    
    # 新しい結果を確認
    assert "topic" in new_result
    assert "message" in new_result
    assert "steps" in new_result
    assert new_result["topic"] == "chickens"
    assert "chickens" in new_result["message"].lower()
    
    # 元の結果とは異なることを確認
    assert new_result["topic"] != original_topic
    
    # ステップ履歴が更新されていることを確認
    assert len(new_result["steps"]) >= 1


def test_time_travel_resume_from_checkpoint(config, initial_state, graph_with_checkpointer):
    """チェックポイントから実行を再開できることを確認"""
    # 1. グラフを実行
    result = graph_with_checkpointer.invoke(initial_state, config)

    print(initial_state)
    print(config)
    print(result)
    
    # 2. チェックポイントを特定
    states = list(graph_with_checkpointer.get_state_history(config))
    assert len(states) > 0
    
    # 3. 中間のチェックポイントを選択（状態を変更せずに再実行）
    selected_state = states[0]  # 最新の状態
    
    # 4. チェックポイントから実行を再開
    resume_config = {
        "configurable": {
            "thread_id": config["configurable"]["thread_id"],
            "checkpoint_id": selected_state.config["configurable"]["checkpoint_id"]
        }
    }
    
    # 再実行（状態を変更しない）
    resume_result = graph_with_checkpointer.invoke(None, resume_config)
    
    # 結果を確認
    assert "topic" in resume_result
    assert "message" in resume_result


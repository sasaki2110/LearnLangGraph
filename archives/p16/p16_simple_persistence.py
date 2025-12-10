"""
P16: 基本的な永続化の例

このスクリプトは、LangGraphの永続化機能の基本的な使用方法を示します。
チェックポイントがどのように保存され、状態がどのように管理されるかを確認できます。
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from typing import Annotated
from typing_extensions import TypedDict
from operator import add


# 状態の定義
class State(TypedDict):
    """グラフの状態を定義"""
    foo: str
    bar: Annotated[list[str], add]  # リデューサを使用してリストに追加


# ノード関数の定義
def node_a(state: State) -> dict:
    """ノードA: 状態を更新"""
    print("  → node_a を実行中...")
    return {"foo": "a", "bar": ["a"]}


def node_b(state: State) -> dict:
    """ノードB: 状態を更新"""
    print("  → node_b を実行中...")
    return {"foo": "b", "bar": ["b"]}


def main():
    """メイン関数"""
    print("=" * 60)
    print("P16: 基本的な永続化の例")
    print("=" * 60)
    print()

    # グラフの構築
    print("1. グラフの構築")
    print("-" * 60)
    workflow = StateGraph(State)
    workflow.add_node("node_a", node_a)
    workflow.add_node("node_b", node_b)
    workflow.add_edge(START, "node_a")
    workflow.add_edge("node_a", "node_b")
    workflow.add_edge("node_b", END)
    print("✓ グラフを構築しました")
    print()

    # チェックポインタの作成
    print("2. チェックポインタの作成")
    print("-" * 60)
    checkpointer = MemorySaver()
    print("✓ MemorySaver を作成しました")
    print()

    # グラフのコンパイル（チェックポインタを設定）
    print("3. グラフのコンパイル（チェックポインタを設定）")
    print("-" * 60)
    graph = workflow.compile(checkpointer=checkpointer)
    print("✓ グラフをコンパイルしました（チェックポインタ付き）")
    print()

    # スレッドIDの設定
    print("4. スレッドIDの設定")
    print("-" * 60)
    config = RunnableConfig(configurable={"thread_id": "1"})
    print(f"✓ スレッドID: {config['configurable']['thread_id']}")
    print()

    # グラフの実行
    print("5. グラフの実行")
    print("-" * 60)
    print("初期状態でグラフを実行します...")
    result = graph.invoke({}, config)
    print(f"✓ 実行完了")
    print(f"  最終状態: {result}")
    print()

    # 状態の取得
    print("6. 現在の状態の取得")
    print("-" * 60)
    state = graph.get_state(config)
    print(f"✓ 現在の状態を取得しました")
    print(f"  状態の値: {state.values}")
    print(f"  チェックポイントID: {state.config.get('configurable', {}).get('checkpoint_id', 'N/A')}")
    print(f"  次に実行するノード: {state.next}")
    print()

    # 状態履歴の取得
    print("7. 状態履歴の取得")
    print("-" * 60)
    history = graph.get_state_history(config)
    print(f"✓ チェックポイント数: {len(list(history))}")
    print()
    
    # 各チェックポイントの詳細を表示
    print("8. 各チェックポイントの詳細")
    print("-" * 60)
    history_list = list(graph.get_state_history(config))
    # stepの値でソート（-1, 0, 1, 2の順）
    history_sorted = sorted(
        history_list, 
        key=lambda x: x.metadata.get('step', 999) if x.metadata else 999
    )
    
    for i, checkpoint in enumerate(history_sorted, 1):
        print(f"\nチェックポイント {i}:")
        # チェックポイントIDはconfigから取得
        checkpoint_id = checkpoint.config.get('configurable', {}).get('checkpoint_id', 'N/A')
        print(f"  チェックポイントID: {checkpoint_id}")
        # created_at属性を使用
        if hasattr(checkpoint, 'created_at'):
            print(f"  作成日時: {checkpoint.created_at}")
        print(f"  状態の値: {checkpoint.values}")
        print(f"  次に実行するノード: {checkpoint.next}")
        if checkpoint.metadata:
            step = checkpoint.metadata.get('step', 'N/A')
            source = checkpoint.metadata.get('source', 'N/A')
            print(f"  メタデータ: step={step}, source={source}")
    
    print()
    print("=" * 60)
    print("実行結果のまとめ")
    print("=" * 60)
    print()
    print("このコードを実行すると、以下のチェックポイントが保存されます：")
    print()
    
    # stepの値に基づいて表示
    for cp in history_sorted:
        step = cp.metadata.get('step', 999) if cp.metadata else 999
        if step == -1:
            print("1. 初期状態（START）:")
            print(f"   状態: {cp.values}")
            print(f"   次に実行するノード: {cp.next}")
            print()
        elif step == 0:
            print("2. node_a実行後:")
            print(f"   状態: {cp.values}")
            print(f"   次に実行するノード: {cp.next}")
            print()
        elif step == 1:
            print("3. node_b実行後:")
            print(f"   状態: {cp.values}")
            print(f"   次に実行するノード: {cp.next}")
            print()
        elif step == 2:
            print("4. 最終状態（END）:")
            print(f"   状態: {cp.values}")
            print(f"   次に実行するノード: {cp.next}")
            print()
    print()
    print("各チェックポイントは、グラフの特定の時点での状態をキャプチャし、")
    print("後での分析や再実行に役立ちます。")
    print()
    print("【重要なポイント】")
    print("- 各ノードの実行後にチェックポイントが自動的に保存されます")
    print("- チェックポイントには状態の値、次に実行するノード、メタデータが含まれます")
    print("- 同じスレッドIDを使用することで、会話履歴を保持できます")
    print("- チェックポイントから状態を復元して、実行を再開できます")
    print()


if __name__ == "__main__":
    main()


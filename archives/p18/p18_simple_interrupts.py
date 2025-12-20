"""
P18: 基本的な中断（Interrupts）の例

このスクリプトは、LangGraphの中断機能の基本的な使用方法を示します。
nodeBでユーザー承認を求める中断を実装しています。
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.runnables import RunnableConfig
from typing import Annotated
from typing_extensions import TypedDict
from operator import add


# 状態の定義
class State(TypedDict):
    """グラフの状態を定義"""
    messages: Annotated[list[str], add]  # メッセージのリスト
    approved: bool  # 承認状態
    action: str  # 実行するアクション


# ノード関数の定義
def node_a(state: State) -> dict:
    """ノードA: 初期処理とアクションの準備"""
    print("  → node_a を実行中...")
    action = "重要なデータベース操作を実行します"
    print(f"    準備したアクション: {action}")
    return {
        "messages": ["node_a: 初期処理が完了しました"],
        "action": action
    }


def node_b(state: State) -> dict:
    """ノードB: ユーザー承認を求める中断"""
    print("  → node_b を実行中...")
    print("    承認を求めます...")
    
    # interrupt()を呼び出して実行を一時停止
    # ペイロードは呼び出し元のresult["__interrupt__"]に表示される
    is_approved = interrupt({
        "question": "以下のアクションを実行してもよろしいですか？",
        "action": state.get("action", "不明なアクション"),
        "message": "承認する場合は 'y'、拒否する場合は 'n' を入力してください"
    })
    
    # 再開すると、Command(resume=...)の値がここに返される
    print(f"    承認結果: {is_approved}")
    
    return {
        "messages": [f"node_b: 承認結果 = {is_approved}"],
        "approved": is_approved
    }


def node_c(state: State) -> dict:
    """ノードC: 承認に基づいて最終処理を実行"""
    print("  → node_c を実行中...")
    
    if state.get("approved", False):
        result = "✓ アクションが承認され、実行されました"
        print(f"    {result}")
    else:
        result = "✗ アクションが拒否され、実行されませんでした"
        print(f"    {result}")
    
    return {
        "messages": [f"node_c: {result}"]
    }


def main():
    """メイン関数"""
    print("=" * 60)
    print("P18: 基本的な中断（Interrupts）の例")
    print("=" * 60)
    print()

    # グラフの構築
    print("1. グラフの構築")
    print("-" * 60)
    workflow = StateGraph(State)
    workflow.add_node("node_a", node_a)
    workflow.add_node("node_b", node_b)
    workflow.add_node("node_c", node_c)
    
    # エッジの追加: nodeA → nodeB → nodeC
    workflow.add_edge(START, "node_a")
    workflow.add_edge("node_a", "node_b")
    workflow.add_edge("node_b", "node_c")
    workflow.add_edge("node_c", END)
    print("✓ グラフを構築しました (nodeA → nodeB → nodeC)")
    print()

    # チェックポインターの作成
    print("2. チェックポインターの作成")
    print("-" * 60)
    checkpointer = MemorySaver()
    print("✓ MemorySaver を作成しました")
    print("  （中断を使用するにはチェックポインターが必要です）")
    print()

    # グラフのコンパイル（チェックポインターを設定）
    print("3. グラフのコンパイル（チェックポインターを設定）")
    print("-" * 60)
    graph = workflow.compile(checkpointer=checkpointer)
    print("✓ グラフをコンパイルしました（チェックポインター付き）")
    print()

    # スレッドIDの設定
    print("4. スレッドIDの設定")
    print("-" * 60)
    config = RunnableConfig(configurable={"thread_id": "thread-1"})
    print(f"✓ スレッドID: {config['configurable']['thread_id']}")
    print()

    # グラフの実行（中断まで）
    print("5. グラフの実行（中断まで）")
    print("-" * 60)
    print("初期状態でグラフを実行します...")
    print("  （nodeBで中断されます）")
    print()
    
    initial_state = {
        "messages": [],
        "approved": False,
        "action": ""
    }
    
    result = graph.invoke(initial_state, config)
    print()
    print("✓ 実行が中断されました")
    print()

    # 中断情報の確認
    print("6. 中断情報の確認")
    print("-" * 60)
    if "__interrupt__" in result:
        interrupt_info = result["__interrupt__"]
        print("✓ 中断が検出されました")
        print(f"  中断ペイロード: {interrupt_info}")
        
        # 中断情報から質問を表示
        if interrupt_info and len(interrupt_info) > 0:
            payload = interrupt_info[0].value if hasattr(interrupt_info[0], 'value') else interrupt_info[0]
            if isinstance(payload, dict):
                print(f"\n  【承認リクエスト】")
                print(f"  質問: {payload.get('question', 'N/A')}")
                print(f"  アクション: {payload.get('action', 'N/A')}")
                print(f"  メッセージ: {payload.get('message', 'N/A')}")
    else:
        print("  （中断は検出されませんでした）")
    print()

    # 現在の状態の確認
    print("7. 現在の状態の確認")
    print("-" * 60)
    state = graph.get_state(config)
    print(f"✓ 現在の状態を取得しました")
    print(f"  状態の値: {state.values}")
    print(f"  次に実行するノード: {state.next}")
    print()

    # ユーザー承認のシミュレーション
    print("8. ユーザー承認のシミュレーション")
    print("-" * 60)
    print("実際のアプリケーションでは、ここでユーザーからの入力を待ちます。")
    print("この例では、承認（True）として再開します。")
    print()
    
    # 承認して再開
    print("  → 承認（True）で再開します...")
    result = graph.invoke(Command(resume=True), config=config)
    print()
    print("✓ 実行が完了しました")
    print(f"  最終状態: {result}")
    print()

    # 最終状態の確認
    print("9. 最終状態の確認")
    print("-" * 60)
    final_state = graph.get_state(config)
    print(f"✓ 最終状態を取得しました")
    print(f"  状態の値: {final_state.values}")
    print(f"  次に実行するノード: {final_state.next}")
    print()

    print("=" * 60)
    print("実行結果のまとめ")
    print("=" * 60)
    print()
    print("このコードを実行すると、以下の流れで処理されます：")
    print()
    print("1. nodeA が実行される（初期処理）")
    print("2. nodeB で interrupt() が呼び出され、実行が一時停止")
    print("3. 中断情報が result['__interrupt__'] に表示される")
    print("4. Command(resume=True) で再開")
    print("5. nodeB が再実行され、interrupt() の戻り値として True を受け取る")
    print("6. nodeC が実行される（承認に基づく最終処理）")
    print()
    print("【重要なポイント】")
    print("- interrupt() を使用するにはチェックポインターが必要です")
    print("- 同じ thread_id を使用して再開する必要があります")
    print("- Command(resume=...) の値が interrupt() の戻り値になります")
    print("- ノードは最初から再実行されるため、interrupt() の前のコードも再実行されます")
    print()


if __name__ == "__main__":
    main()

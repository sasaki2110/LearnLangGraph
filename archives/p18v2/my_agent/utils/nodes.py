"""
ノード関数の定義
"""
from langgraph.types import interrupt
from my_agent.utils.state import State


def node_a(state: State) -> dict:
    """ノードA: 初期処理とアクションの準備"""
    action = "重要なデータベース操作を実行します"
    return {
        "messages": ["node_a: 初期処理が完了しました"],
        "action": action
    }


def node_b(state: State) -> dict:
    """ノードB: ユーザー承認を求める中断"""
    # interrupt()を呼び出して実行を一時停止
    # ペイロードは呼び出し元のresult["__interrupt__"]に表示される
    user_input = interrupt({
        "question": "以下のアクションを実行してもよろしいですか？",
        "action": state.get("action", "不明なアクション"),
        "message": "承認する場合は 'y'、拒否する場合は 'n' を入力してください"
    })
    
    # 再開すると、Command(resume=...)の値がここに返される
    # 文字列を真偽値に変換（"y"またはTrueの場合のみ承認）
    if isinstance(user_input, str):
        is_approved = user_input.lower() == "y"
    else:
        is_approved = bool(user_input)
    
    return {
        "messages": [f"node_b: 承認結果 = {is_approved}"],
        "approved": is_approved
    }


def node_c(state: State) -> dict:
    """ノードC: 承認に基づいて最終処理を実行"""
    if state.get("approved", False):
        result = "✓ アクションが承認され、実行されました"
    else:
        result = "✗ アクションが拒否され、実行されませんでした"
    
    return {
        "messages": [f"node_c: {result}"]
    }


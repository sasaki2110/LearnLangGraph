"""
ノード関数の定義
"""
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def node_a(state: State) -> dict:
    """ノードA: 初期処理とアクションの準備"""
    logger.info("🚀 [NODE_A] 初期処理ノードを開始します")
    logger.debug(f"📊 [NODE_A] 現在の状態: messages数={len(state.get('messages', []))}")
    
    try:
        action = "重要なデータベース操作を実行します"
        logger.info(f"📝 [NODE_A] アクションを準備しました: {action}")
        
        result = {
            "messages": ["node_a: 初期処理が完了しました"],
            "action": action
        }
        
        logger.info("✅ [NODE_A] 初期処理ノードが完了しました")
        return result
        
    except Exception as e:
        logger.error(f"❌ [NODE_A] 初期処理中にエラーが発生しました: {e}", exc_info=True)
        raise


def node_b(state: State) -> dict:
    """ノードB: ユーザー承認を求める中断"""
    logger.info("⏸️ [NODE_B] ユーザー承認ノードを開始します")
    
    try:
        action = state.get("action", "不明なアクション")
        logger.info(f"📋 [NODE_B] 承認を求めるアクション: {action}")
        
        # interrupt()を呼び出して実行を一時停止
        # ペイロードは呼び出し元のresult["__interrupt__"]に表示される
        logger.info("⏸️ [NODE_B] 中断を要求します（ユーザー承認待ち）")
        try:
            user_input = interrupt({
                "question": "以下のアクションを実行してもよろしいですか？",
                "action": action,
                "message": "承認する場合は 'y'、拒否する場合は 'n' を入力してください"
            })
        except GraphInterrupt as e:
            # GraphInterruptは正常な動作の一部なので、エラーではなくINFOログとして記録
            logger.info(f"⏸️ [NODE_B] 中断が発行されました（これは正常な動作です）")
            # 例外を再raiseして、LangGraphが正常に処理できるようにする
            raise
        
        logger.info(f"🔄 [NODE_B] 中断から再開しました（ユーザー入力: {user_input}）")
        
        # 再開すると、Command(resume=...)の値がここに返される
        # 文字列を真偽値に変換（"y"またはTrueの場合のみ承認）
        if isinstance(user_input, str):
            is_approved = user_input.lower() == "y"
        else:
            is_approved = bool(user_input)
        
        logger.info(f"✅ [NODE_B] 承認結果: {is_approved}")
        
        result = {
            "messages": [f"node_b: 承認結果 = {is_approved}"],
            "approved": is_approved
        }
        
        logger.info("✅ [NODE_B] ユーザー承認ノードが完了しました")
        return result
        
    except GraphInterrupt:
        # GraphInterruptは再raiseして、LangGraphが正常に処理できるようにする
        raise
    except Exception as e:
        logger.error(f"❌ [NODE_B] ユーザー承認処理中にエラーが発生しました: {e}", exc_info=True)
        raise


def node_c(state: State) -> dict:
    """ノードC: 承認に基づいて最終処理を実行"""
    logger.info("🏁 [NODE_C] 最終処理ノードを開始します")
    
    try:
        approved = state.get("approved", False)
        logger.info(f"📋 [NODE_C] 承認状態: {approved}")
        
        if approved:
            result = "✓ アクションが承認され、実行されました"
            logger.info("✅ [NODE_C] アクションが承認され、実行されました")
        else:
            result = "✗ アクションが拒否され、実行されませんでした"
            logger.info("❌ [NODE_C] アクションが拒否され、実行されませんでした")
        
        final_result = {
            "messages": [f"node_c: {result}"]
        }
        
        logger.info("✅ [NODE_C] 最終処理ノードが完了しました")
        return final_result
        
    except Exception as e:
        logger.error(f"❌ [NODE_C] 最終処理中にエラーが発生しました: {e}", exc_info=True)
        raise


"""
ノード関数の実装
"""
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def count_characters(state: State):
    """文字数をカウントするPythonノード"""
    logger.info("🔢 [COUNT] 文字数カウントを開始します")
    logger.debug(f"📊 [COUNT] 現在の状態: messages数={len(state.get('messages', []))}")
    
    try:
        # メッセージが存在する場合、最後のメッセージから内容を取得
        if state.get("messages") and len(state["messages"]) > 0:
            # 最後のメッセージの内容を取得
            last_message = state["messages"][-1]
            # 辞書形式のメッセージ（LangSmithから来る場合）にも対応
            if isinstance(last_message, dict):
                message_content = last_message.get("content", "").strip()
            elif hasattr(last_message, "content"):
                message_content = last_message.content.strip()
            else:
                message_content = str(last_message).strip()
            logger.info(f"✅ [COUNT] メッセージから内容を取得しました: {message_content[:50]}...")
        else:
            # メッセージがない場合は、既存のmessageを使用
            message_content = state.get("message", "")
            logger.info(f"📝 [COUNT] 既存のメッセージを使用します: {message_content[:50] if message_content else 'なし'}...")
        
        if not message_content:
            logger.warning("⚠️ [COUNT] メッセージ内容が空です")
            return {
                "message": "",
                "char_count": 0
            }
        
        # 文字数をカウント
        char_count = len(message_content)
        
        logger.info(f"📝 [COUNT] メッセージ: {message_content[:50]}...")
        logger.info(f"🔢 [COUNT] 文字数: {char_count}")
        
        # 状態を更新
        # char_countはoperator.addで加算される
        # messageは最初のユーザーメッセージを保持
        current_message = state.get("message")
        if not current_message:
            # 最初のメッセージを保持
            return {
                "message": message_content,
                "char_count": char_count
            }
        else:
            # 既にメッセージがある場合は、char_countのみ更新
            return {
                "char_count": char_count
            }
    except Exception as e:
        logger.error(f"❌ [COUNT] 文字数カウント中にエラーが発生しました: {e}", exc_info=True)
        raise


def parrot_with_count(state: State, llm):
    """オウム返しするLLMノード（文字数情報付き）"""
    logger.info("🦜 [PARROT] オウム返しを開始します")
    
    try:
        # 最初のユーザーメッセージを取得
        message = state.get("message", "")
        char_count = state.get("char_count", 0)
        
        if not message:
            logger.warning("⚠️ [PARROT] メッセージが存在しません")
            message = "メッセージがありません"
        
        logger.info(f"📝 [PARROT] メッセージ: {message[:50]}...")
        logger.info(f"🔢 [PARROT] 合計文字数: {char_count}")
        
        # LLMにオウム返し＋文字数情報を付与してもらう
        prompt = f"""以下のユーザーメッセージをそのまま返してください。
ただし、メッセージの最後に「これまでの合計文字数は {char_count} 文字です」という情報を追加してください。
メッセージ自体は変更せず、そのまま返してください。

ユーザーメッセージ: {message}"""
        
        system_message = SystemMessage(
            content="あなたはユーザーのメッセージをそのまま返すオウム返しアシスタントです。"
        )
        human_message = HumanMessage(content=prompt)
        
        logger.debug("🤖 [PARROT] LLMを呼び出しています...")
        response = llm.invoke([system_message, human_message])
        response_text = response.content.strip()
        
        logger.info(f"✅ [PARROT] オウム返しが完了しました: {response_text[:100]}...")
        
        # messages へ追加
        return {
            "messages": [AIMessage(content=response_text)]
        }
    except Exception as e:
        logger.error(f"❌ [PARROT] オウム返し中にエラーが発生しました: {e}", exc_info=True)
        raise


"""
ノード関数の実装
"""
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def extract_topic(state: State):
    """メッセージからトピックを抽出するノード"""
    logger.info("📝 [EXTRACT] トピック抽出を開始します")
    logger.debug(f"📊 [EXTRACT] 現在の状態: messages数={len(state.get('messages', []))}")
    
    try:
        # メッセージが存在する場合、最後のユーザーメッセージからトピックを抽出
        if state.get("messages") and len(state["messages"]) > 0:
            # 最後のメッセージの内容をトピックとして使用
            last_message = state["messages"][-1]
            if hasattr(last_message, "content"):
                topic = last_message.content.strip()
            else:
                topic = str(last_message).strip()
            logger.info(f"✅ [EXTRACT] メッセージからトピックを抽出しました: {topic[:50]}...")
        else:
            # メッセージがない場合は、既存のtopicを使用（後方互換性のため）
            topic = state.get("topic", "")
            logger.info(f"📝 [EXTRACT] 既存のトピックを使用します: {topic[:50] if topic else 'なし'}...")
        
        return {"topic": topic}
    except Exception as e:
        logger.error(f"❌ [EXTRACT] トピック抽出中にエラーが発生しました: {e}", exc_info=True)
        raise


def refine_topic(state: State, llm):
    """トピックを精緻化するノード（LLMを使用）"""
    logger.info("✨ [REFINE] トピック精緻化を開始します")
    
    try:
        # topicが存在しない場合は、メッセージから抽出を試みる
        topic = state.get("topic")
        if not topic:
            # メッセージからトピックを抽出
            if state.get("messages") and len(state["messages"]) > 0:
                last_message = state["messages"][-1]
                if hasattr(last_message, "content"):
                    topic = last_message.content.strip()
                else:
                    topic = str(last_message).strip()
            else:
                topic = ""
        
        logger.info(f"📝 [REFINE] 元のトピック: {topic[:50]}...")
        
        prompt = f"以下のトピックを、より面白く魅力的なトピックに精緻化してください。簡潔に1文で答えてください。\n\nトピック: {topic}"
        
        messages = [
            SystemMessage(content="あなたはトピックを面白く精緻化する専門家です。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [REFINE] LLMを呼び出しています...")
        response = llm.invoke(messages)
        refined_topic = response.content.strip()
        
        logger.info(f"✅ [REFINE] トピック精緻化が完了しました: {refined_topic[:50]}...")
        
        return {"topic": refined_topic}
    except Exception as e:
        logger.error(f"❌ [REFINE] トピック精緻化中にエラーが発生しました: {e}", exc_info=True)
        raise


def generate_joke(state: State, llm):
    """ジョークを生成するノード（LLMを使用）"""
    logger.info("😄 [GENERATE] ジョーク生成を開始します")
    
    try:
        topic = state.get("topic", "")
        if not topic:
            logger.error("❌ [GENERATE] トピックが設定されていません")
            raise ValueError("トピックが設定されていません")
        
        logger.info(f"📝 [GENERATE] トピック: {topic[:50]}...")
        
        prompt = f"以下のトピックについて、面白いジョークを1つ生成してください。\n\nトピック: {topic}"
        
        messages = [
            SystemMessage(content="あなたは面白いジョークを生成するコメディアンです。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [GENERATE] LLMを呼び出しています...")
        response = llm.invoke(messages)
        joke = response.content.strip()
        
        logger.info(f"✅ [GENERATE] ジョーク生成が完了しました (長さ: {len(joke)}文字)")
        logger.debug(f"😄 [GENERATE] 生成されたジョーク: {joke[:100]}...")
        
        # Vercel AI SDKのチャットが表示できるように、AIMessageとしてmessagesに追加
        return {
            "joke": joke,
            "messages": [AIMessage(content=joke)]  # チャットUIで表示されるメッセージ
        }
    except Exception as e:
        logger.error(f"❌ [GENERATE] ジョーク生成中にエラーが発生しました: {e}", exc_info=True)
        raise


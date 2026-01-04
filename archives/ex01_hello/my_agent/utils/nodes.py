"""
ノード関数の実装
"""
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def detect_language(state: State, llm):
    """言語を判定するLLMノード"""
    logger.info("🌐 [DETECT] 言語判定を開始します")
    
    try:
        # 最新のメッセージを取得
        messages = state.get("messages", [])
        if not messages or len(messages) == 0:
            logger.warning("⚠️ [DETECT] メッセージが存在しません")
            return {"language": "english"}  # デフォルトは英語
        
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            user_input = last_message.content.strip()
        else:
            user_input = str(last_message).strip()
        
        logger.info(f"📝 [DETECT] ユーザー入力: {user_input[:50]}...")
        
        # LLMに言語判定を依頼
        prompt = f"""以下のメッセージが日本語、英語、または終了を表すかを判定してください。
メッセージが日本語の場合は "japanese"、英語の場合は "english"、終了を表す（"quit", "終了", "exit"など）場合は "quit" とだけ答えてください。
それ以外の文字は一切含めないでください。

メッセージ: {user_input}"""
        
        system_message = SystemMessage(
            content="あなたは言語判定の専門家です。メッセージの言語を正確に判定してください。"
        )
        human_message = HumanMessage(content=prompt)
        
        logger.debug("🤖 [DETECT] LLMを呼び出しています...")
        response = llm.invoke([system_message, human_message])
        detected_language = response.content.strip().lower()
        
        # 有効な値に正規化
        if detected_language not in ["japanese", "english", "quit"]:
            logger.warning(f"⚠️ [DETECT] 無効な言語判定結果: {detected_language}。デフォルトで'english'に設定します")
            detected_language = "english"
        
        logger.info(f"✅ [DETECT] 言語判定が完了しました: {detected_language}")
        
        # メッセージと判定結果で状態を更新
        return {
            "language": detected_language,
            "messages": [AIMessage(content=f"言語を判定しました: {detected_language}")]
        }
    except Exception as e:
        logger.error(f"❌ [DETECT] 言語判定中にエラーが発生しました: {e}", exc_info=True)
        raise


def greet_in_english(state: State, llm):
    """英語で挨拶を返すLLMノード"""
    logger.info("👋 [ENGLISH] 英語での挨拶生成を開始します")
    
    try:
        # 最新のユーザーメッセージ（HumanMessage）を取得
        messages = state.get("messages", [])
        user_input = None
        
        # HumanMessageを後ろから探す
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                if hasattr(msg, "content"):
                    user_input = msg.content.strip()
                else:
                    user_input = str(msg).strip()
                break
        
        if not user_input:
            logger.warning("⚠️ [ENGLISH] ユーザーメッセージが見つかりません")
            greeting = "Hello! How can I help you?"
        else:
            logger.info(f"📝 [ENGLISH] ユーザー入力: {user_input[:50]}...")
            
            # LLMに英語で挨拶を作成してもらう
            prompt = f"""Please create a friendly greeting in English in response to the following message.
Keep it brief and natural.

Message: {user_input}"""
            
            system_message = SystemMessage(
                content="You are a friendly assistant who greets people in English."
            )
            human_message = HumanMessage(content=prompt)
            
            logger.debug("🤖 [ENGLISH] LLMを呼び出しています...")
            response = llm.invoke([system_message, human_message])
            greeting = response.content.strip()
        
        logger.info(f"✅ [ENGLISH] 英語での挨拶生成が完了しました: {greeting[:50]}...")
        
        # messages へ追加
        return {
            "messages": [AIMessage(content=greeting)]
        }
    except Exception as e:
        logger.error(f"❌ [ENGLISH] 英語での挨拶生成中にエラーが発生しました: {e}", exc_info=True)
        raise


def greet_in_japanese(state: State, llm):
    """日本語で挨拶を返すLLMノード"""
    logger.info("👋 [JAPANESE] 日本語での挨拶生成を開始します")
    
    try:
        # 最新のユーザーメッセージ（HumanMessage）を取得
        messages = state.get("messages", [])
        user_input = None
        
        # HumanMessageを後ろから探す
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                if hasattr(msg, "content"):
                    user_input = msg.content.strip()
                else:
                    user_input = str(msg).strip()
                break
        
        if not user_input:
            logger.warning("⚠️ [JAPANESE] ユーザーメッセージが見つかりません")
            greeting = "こんにちは！何かお手伝いできることはありますか？"
        else:
            logger.info(f"📝 [JAPANESE] ユーザー入力: {user_input[:50]}...")
            
            # LLMに日本語で挨拶を作成してもらう
            prompt = f"""以下のメッセージに対して、日本語で親しみやすい挨拶を作成してください。
簡潔で自然な挨拶にしてください。

メッセージ: {user_input}"""
            
            system_message = SystemMessage(
                content="あなたは日本語で親しみやすく挨拶するアシスタントです。"
            )
            human_message = HumanMessage(content=prompt)
            
            logger.debug("🤖 [JAPANESE] LLMを呼び出しています...")
            response = llm.invoke([system_message, human_message])
            greeting = response.content.strip()
        
        logger.info(f"✅ [JAPANESE] 日本語での挨拶生成が完了しました: {greeting[:50]}...")
        
        # messages へ追加
        return {
            "messages": [AIMessage(content=greeting)]
        }
    except Exception as e:
        logger.error(f"❌ [JAPANESE] 日本語での挨拶生成中にエラーが発生しました: {e}", exc_info=True)
        raise


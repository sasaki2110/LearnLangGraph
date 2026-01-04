"""
ノード関数の実装
"""
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')

# NGワードリスト
NG_WORDS = ["最高", "日本一", "絶対"]


def generator(state: State, llm):
    """キャッチコピーを生成するLLMノード"""
    logger.info("✨ [GENERATOR] キャッチコピー生成を開始します")
    
    try:
        # new_product_catchphrase_ideaが未設定なら、最後のメッセージを格納
        idea = state.get("new_product_catchphrase_idea")
        if not idea:
            # メッセージから取得
            messages = state.get("messages", [])
            if messages and len(messages) > 0:
                last_message = messages[-1]
                # 辞書形式のメッセージ（LangSmithから来る場合）にも対応
                if isinstance(last_message, dict):
                    idea = last_message.get("content", "").strip()
                elif hasattr(last_message, "content"):
                    idea = last_message.content.strip()
                else:
                    idea = str(last_message).strip()
                logger.info(f"✅ [GENERATOR] メッセージからアイデアを取得しました: {idea[:50]}...")
            else:
                idea = "新商品"
                logger.warning("⚠️ [GENERATOR] メッセージが存在しないため、デフォルト値を使用します")
        else:
            logger.info(f"📝 [GENERATOR] 既存のアイデアを使用します: {idea[:50]}...")
        
        # 改善ポイントを取得
        improvement_points = state.get("improvement_points", "")
        
        # LLMにキャッチコピーを生成してもらう
        if improvement_points:
            prompt = f"""以下の新商品について、キャッチコピーを1つ生成してください。

{improvement_points}

キャッチコピーを作成する新商品: {idea}

上記の改善点を踏まえて、魅力的なキャッチコピーを生成してください。"""
        else:
            prompt = f"""以下の新商品について、キャッチコピーを1つ生成してください。

キャッチコピーを作成する新商品: {idea}

魅力的なキャッチコピーを生成してください。"""
        
        system_message = SystemMessage(
            content="あなたは優れたキャッチコピーを生成するコピーライターです。魅力的なキャッチコピーを作成してください。"
        )
        human_message = HumanMessage(content=prompt)
        
        logger.debug("🤖 [GENERATOR] LLMを呼び出しています...")
        response = llm.invoke([system_message, human_message])
        catchphrase = response.content.strip()
        
        logger.info(f"✅ [GENERATOR] キャッチコピー生成が完了しました: {catchphrase}")
        logger.debug(f"📤 [GENERATOR] 返却する状態更新: new_product_catchphrase_idea={idea[:50] if idea else None}..., catchphrase={catchphrase[:50]}...")
        
        # 状態を更新
        result = {
            "new_product_catchphrase_idea": idea,
            "catchphrase": catchphrase
        }
        logger.debug(f"📤 [GENERATOR] 返却値: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [GENERATOR] キャッチコピー生成中にエラーが発生しました: {e}", exc_info=True)
        raise


def checker(state: State):
    """NGワードをチェックするPythonノード"""
    logger.info("🔍 [CHECKER] NGワードチェックを開始します")
    
    try:
        catchphrase = state.get("catchphrase", "")
        if not catchphrase:
            logger.warning("⚠️ [CHECKER] キャッチコピーが存在しません")
            return {
                "has_ngword": False,
                "improvement_points": None
            }
        
        logger.info(f"📝 [CHECKER] チェック対象: {catchphrase[:50]}...")
        
        # NGワードをチェック
        detected_ngwords = []
        for ng_word in NG_WORDS:
            if ng_word in catchphrase:
                detected_ngwords.append(ng_word)
                logger.warning(f"⚠️ [CHECKER] NGワードを検出: {ng_word}")
        
        if detected_ngwords:
            # NGワードが含まれている場合
            has_ngword = True
            # 改善ポイントを設定（複数の場合はカンマ区切り）
            improvement_points = "、".join([f"{word}をキャッチコピーに含めてはいけません。" for word in detected_ngwords])
            logger.info(f"❌ [CHECKER] NGワードが検出されました: {', '.join(detected_ngwords)}")
            logger.info(f"📝 [CHECKER] 改善ポイント: {improvement_points}")
        else:
            # NGワードが含まれていない場合
            has_ngword = False
            improvement_points = None
            logger.info("✅ [CHECKER] NGワードは検出されませんでした")
        
        # 最終的なキャッチコピーをmessagesに追加（NGワードがない場合のみ）
        result = {
            "has_ngword": has_ngword,
            "improvement_points": improvement_points
        }
        
        if not has_ngword:
            # NGワードがない場合のみ、messagesに追加
            aimessage = AIMessage(content=catchphrase)
            result["messages"] = [aimessage]
            logger.info(f"✅ [CHECKER] 最終キャッチコピー: {catchphrase}")
            logger.debug(f"📤 [CHECKER] messagesに追加するAIMessage: content='{aimessage.content}', type={type(aimessage).__name__}")
        else:
            logger.debug(f"📤 [CHECKER] NGワードが検出されたため、messagesには追加しません")
        
        logger.debug(f"📤 [CHECKER] 返却する状態更新: has_ngword={has_ngword}, improvement_points={improvement_points}, messages数={len(result.get('messages', []))}")
        logger.debug(f"📤 [CHECKER] 返却値: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [CHECKER] NGワードチェック中にエラーが発生しました: {e}", exc_info=True)
        raise


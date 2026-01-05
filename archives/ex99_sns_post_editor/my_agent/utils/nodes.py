"""
ノード関数の実装
"""
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from my_agent.utils.state import SNSState
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def extract_theme(state: SNSState) -> dict:
    """テーマ取得ノード: ユーザー入力をthemeへ格納する"""
    logger.info("📝 [EXTRACT_THEME] テーマ取得ノードを開始します")
    
    try:
        messages = state.get("messages", [])
        if not messages:
            logger.warning("⚠️ [EXTRACT_THEME] メッセージがありません")
            return {"theme": ""}
        
        # 最後のメッセージからテーマを取得
        last_message = messages[-1]
        if hasattr(last_message, "content"):
            theme = last_message.content.strip()
        else:
            theme = str(last_message).strip()
        
        logger.info(f"✅ [EXTRACT_THEME] テーマを取得しました: {theme[:50]}...")
        
        return {
            "theme": theme
        }
        
    except Exception as e:
        logger.error(f"❌ [EXTRACT_THEME] テーマ取得中にエラーが発生しました: {e}", exc_info=True)
        raise


def create_draft_post(state: SNSState, llm) -> dict:
    """投稿作成ノード: themeをもとに、SNSへの投稿を生成し、draft_postへ格納"""
    logger.info("✍️ [CREATE_DRAFT_POST] 投稿作成ノードを開始します")
    
    try:
        theme = state.get("theme", "")
        if not theme:
            logger.warning("⚠️ [CREATE_DRAFT_POST] テーマが設定されていません")
            return {"draft_post": ""}
        
        logger.info(f"📋 [CREATE_DRAFT_POST] テーマ: {theme[:50]}...")
        
        # LLMに投稿を作成してもらう
        prompt = f"""以下のテーマで、SNS（Twitter/X、Instagram、Facebookなど）向けの投稿を1つ作成してください。
投稿は簡潔で魅力的で、エンゲージメントを高める内容にしてください。

テーマ: {theme}
"""
        
        messages_for_llm = [
            SystemMessage(content="You are a social media content creator. Create engaging, concise posts for social media platforms."),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [CREATE_DRAFT_POST] LLMを呼び出しています...")
        response = llm.invoke(messages_for_llm)
        draft_post = response.content.strip()
        
        logger.info(f"✅ [CREATE_DRAFT_POST] 投稿下書きを作成しました (長さ: {len(draft_post)}文字)")
        logger.debug(f"📄 [CREATE_DRAFT_POST] 下書き: {draft_post[:100]}...")
        
        return {
            "draft_post": draft_post
        }
        
    except Exception as e:
        logger.error(f"❌ [CREATE_DRAFT_POST] 投稿作成中にエラーが発生しました: {e}", exc_info=True)
        raise


def request_approval(state: SNSState) -> dict:
    """中断ノード: interruptを発行し、処理継続をユーザーへ問い合わせる"""
    logger.info("⏸️ [REQUEST_APPROVAL] 承認要求ノードを開始します")
    
    try:
        draft_post = state.get("draft_post", "")
        if not draft_post:
            logger.warning("⚠️ [REQUEST_APPROVAL] 下書きがありません")
            return {
                "approved": False
            }
        
        logger.info(f"📋 [REQUEST_APPROVAL] 下書きの長さ: {len(draft_post)}文字")
        logger.debug(f"📄 [REQUEST_APPROVAL] 下書き: {draft_post[:100]}...")
        
        # interrupt()を呼び出して実行を一時停止
        logger.info("⏸️ [REQUEST_APPROVAL] 中断を要求します（ユーザー承認待ち）")
        try:
            user_input = interrupt({
                "question": "以下の投稿下書きを承認しますか？",
                "draft_post": draft_post,
                "message": "承認する場合は 'y'、拒否する場合は 'n' を入力してください"
            })
        except GraphInterrupt as e:
            # GraphInterruptは正常な動作の一部なので、エラーではなくINFOログとして記録
            logger.info(f"⏸️ [REQUEST_APPROVAL] 中断が発行されました（これは正常な動作です）")
            # 例外を再raiseして、LangGraphが正常に処理できるようにする
            raise
        
        logger.info(f"🔄 [REQUEST_APPROVAL] 中断から再開しました（ユーザー入力: {user_input}）")
        
        # 再開すると、Command(resume=...)の値がここに返される
        # 文字列を真偽値に変換（"y"またはTrueの場合のみ承認）
        if isinstance(user_input, str):
            is_approved = user_input.lower() == "y"
        else:
            is_approved = bool(user_input)
        
        logger.info(f"✅ [REQUEST_APPROVAL] 承認結果: {is_approved}")
        
        return {
            "approved": is_approved
        }
        
    except GraphInterrupt:
        # GraphInterruptは再raiseして、LangGraphが正常に処理できるようにする
        raise
    except Exception as e:
        logger.error(f"❌ [REQUEST_APPROVAL] 承認要求処理中にエラーが発生しました: {e}", exc_info=True)
        raise


def refine_final_post(state: SNSState, llm) -> dict:
    """最終投稿生成ノード: draft_postをリファインし最終ポストfinal_postを作成する"""
    logger.info("✨ [REFINE_FINAL_POST] 最終投稿生成ノードを開始します")
    
    try:
        draft_post = state.get("draft_post", "")
        if not draft_post:
            logger.warning("⚠️ [REFINE_FINAL_POST] 下書きがありません")
            return {
                "final_post": ""
            }
        
        logger.info(f"📋 [REFINE_FINAL_POST] 下書きの長さ: {len(draft_post)}文字")
        logger.debug(f"📄 [REFINE_FINAL_POST] 下書き: {draft_post[:100]}...")
        
        # LLMに下書きをリファインしてもらう
        prompt = f"""以下の投稿下書きを、より魅力的で完璧なSNS投稿にリファインしてください。
承認された下書きなので、内容を改善し、よりエンゲージメントを高める形にしてください。

投稿下書き:
{draft_post}
"""
        
        messages_for_llm = [
            SystemMessage(content="You are a social media content editor. Refine and polish social media posts to make them more engaging and perfect."),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [REFINE_FINAL_POST] LLMを呼び出しています...")
        response = llm.invoke(messages_for_llm)
        final_post = response.content.strip()
        
        logger.info(f"✅ [REFINE_FINAL_POST] 最終投稿を作成しました (長さ: {len(final_post)}文字)")
        logger.debug(f"📄 [REFINE_FINAL_POST] 最終投稿: {final_post[:100]}...")
        
        # 最終投稿をmessagesにも追加（Vercel AI SDKなどで表示するため）
        return {
            "final_post": final_post,
            "messages": [AIMessage(content=final_post)]
        }
        
    except Exception as e:
        logger.error(f"❌ [REFINE_FINAL_POST] 最終投稿生成中にエラーが発生しました: {e}", exc_info=True)
        raise


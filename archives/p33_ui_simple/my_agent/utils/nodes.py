"""
ノード関数の実装
"""
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def node_a(state: State, llm):
    """あ行で始まる20文字くらいの散文をjokesへ追加するノード"""
    logger.info("📝 [NODE_A] あ行の散文生成を開始します")
    
    try:
        prompt = "「あ」で始まる20文字程度の短い散文を1つ書いてください。"
        
        messages = [
            SystemMessage(content="あなたは短い散文を書く作家です。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [NODE_A] LLMを呼び出しています...")
        response = llm.invoke(messages)
        prose = response.content.strip()
        
        logger.info(f"✅ [NODE_A] あ行の散文生成が完了しました: {prose[:50]}...")
        
        return {"jokes": [prose]}
    except Exception as e:
        logger.error(f"❌ [NODE_A] あ行の散文生成中にエラーが発生しました: {e}", exc_info=True)
        raise


def node_k(state: State, llm):
    """か行で始まる20文字くらいの散文をjokesへ追加するノード"""
    logger.info("📝 [NODE_K] か行の散文生成を開始します")
    
    try:
        prompt = "「か」で始まる20文字程度の短い散文を1つ書いてください。"
        
        messages = [
            SystemMessage(content="あなたは短い散文を書く作家です。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [NODE_K] LLMを呼び出しています...")
        response = llm.invoke(messages)
        prose = response.content.strip()
        
        logger.info(f"✅ [NODE_K] か行の散文生成が完了しました: {prose[:50]}...")
        
        return {"jokes": [prose]}
    except Exception as e:
        logger.error(f"❌ [NODE_K] か行の散文生成中にエラーが発生しました: {e}", exc_info=True)
        raise


def node_s(state: State, llm):
    """さ行で始まる20文字くらいの散文をjokesへ追加するノード"""
    logger.info("📝 [NODE_S] さ行の散文生成を開始します")
    
    try:
        prompt = "「さ」で始まる20文字程度の短い散文を1つ書いてください。"
        
        messages = [
            SystemMessage(content="あなたは短い散文を書く作家です。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [NODE_S] LLMを呼び出しています...")
        response = llm.invoke(messages)
        prose = response.content.strip()
        
        logger.info(f"✅ [NODE_S] さ行の散文生成が完了しました: {prose[:50]}...")
        
        return {"jokes": [prose]}
    except Exception as e:
        logger.error(f"❌ [NODE_S] さ行の散文生成中にエラーが発生しました: {e}", exc_info=True)
        raise


def node_final(state: State, llm):
    """これまでの散文をまとめて、最終的なジョークを作成するノード"""
    logger.info("🎯 [NODE_FINAL] 最終ジョークの生成を開始します")
    
    try:
        prose_list = state.get("jokes", [])
        logger.info(f"📝 [NODE_FINAL] 現在の散文数: {len(prose_list)}")
        
        if not prose_list:
            logger.warning("⚠️ [NODE_FINAL] 散文が存在しません")
            final_joke = "ジョークが生成されませんでした。"
        else:
            prose_text = "\n".join([f"- {prose}" for prose in prose_list])
            prompt = f"以下の散文を参考に、これらを綺麗にまとめて面白いジョークを1つ生成してください。\n\n散文集:\n{prose_text}"
            
            messages = [
                SystemMessage(content="あなたは面白いジョークを生成するコメディアンです。複数の散文を統合して、面白いジョークを作成できます。"),
                HumanMessage(content=prompt)
            ]
            
            logger.debug("🤖 [NODE_FINAL] LLMを呼び出しています...")
            response = llm.invoke(messages)
            final_joke = response.content.strip()
            
            logger.info(f"✅ [NODE_FINAL] 最終ジョーク生成が完了しました (長さ: {len(final_joke)}文字)")
            logger.debug(f"🎯 [NODE_FINAL] 生成された最終ジョーク: {final_joke[:100]}...")
        
        # Vercel AI SDKのチャットが表示できるように、AIMessageとしてmessagesに追加
        return {
            "messages": [AIMessage(content=final_joke)]  # チャットUIで表示されるメッセージ
        }
    except Exception as e:
        logger.error(f"❌ [NODE_FINAL] 最終ジョーク生成中にエラーが発生しました: {e}", exc_info=True)
        raise


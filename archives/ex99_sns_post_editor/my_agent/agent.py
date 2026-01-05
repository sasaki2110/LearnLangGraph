"""
SNS投稿エディターエージェントのグラフ定義

Human-in-the-loopの練習：LangGraphの中断（Interrupt）と再開機能を使用
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがインストールされていない場合はスキップ

from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import SNSState
from my_agent.utils.nodes import extract_theme, create_draft_post, request_approval, refine_final_post
from my_agent.utils.logging_config import setup_logging, get_logger, get_log_level

# ロギングをセットアップ
log_level = get_log_level()
setup_logging(log_level=log_level, initialize=True)
logger = get_logger('agent')

logger.info("🚀 [AGENT] エージェントの初期化を開始します")

# OpenAI設定
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
logger.info(f"🤖 [AGENT] 使用モデル: {MODEL_NAME}")

try:
    # モデルの初期化
    logger.debug("🤖 [AGENT] チャットモデルを初期化しています...")
    llm = init_chat_model(
        MODEL_NAME,
        temperature=0.7  # クリエイティブな投稿作成のため、少し高めの温度
    )
    logger.info("✅ [AGENT] チャットモデルの初期化が完了しました")
    
    # ノード関数をラップ（llmを閉包で保持）
    def create_draft_post_node(state: SNSState):
        """投稿作成ノード（llmを閉包で保持）"""
        return create_draft_post(state, llm)
    
    def refine_final_post_node(state: SNSState):
        """最終投稿生成ノード（llmを閉包で保持）"""
        return refine_final_post(state, llm)
    
    # 条件分岐関数
    def should_refine(state: SNSState) -> str:
        """承認状態に基づいてルーティング"""
        logger.debug("🔀 [ROUTING] ルーティング判定を開始します")
        
        approved = state.get("approved", False)
        if approved:
            logger.info("🔀 [ROUTING] 承認済み - 'refine_final_post' にルーティングします")
            return "refine_final_post"
        else:
            logger.info("🔀 [ROUTING] 未承認 - 終了します")
            return END
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(SNSState)
    
    # ノードの追加
    graph.add_node("extract_theme", extract_theme)
    graph.add_node("create_draft_post", create_draft_post_node)
    graph.add_node("request_approval", request_approval)
    graph.add_node("refine_final_post", refine_final_post_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (extract_theme, create_draft_post, request_approval, refine_final_post)")
    
    # エッジの追加
    graph.add_edge(START, "extract_theme")
    graph.add_edge("extract_theme", "create_draft_post")
    graph.add_edge("create_draft_post", "request_approval")
    graph.add_conditional_edges(
        "request_approval",
        should_refine,
        {
            "refine_final_post": "refine_final_post",
            END: END
        }
    )
    graph.add_edge("refine_final_post", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


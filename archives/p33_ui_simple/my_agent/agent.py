"""
UI確認用のストリーミング対応グラフ定義

このグラフは、あ行・か行・さ行で始まる20文字程度の散文を生成し、
それらをまとめて最終的なジョークを作成します。
Vercel AI SDKのチャットから呼び出して使用できます。
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがインストールされていない場合はスキップ
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import node_a, node_k, node_s, node_final
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
        temperature=0
    )
    logger.info("✅ [AGENT] チャットモデルの初期化が完了しました")

    # ノード関数をラップ（llmを閉包で保持）
    def node_a_wrapper(state: State):
        """あ行で始まる20文字程度の散文を生成するノード"""
        return node_a(state, llm)
    
    
    def node_k_wrapper(state: State):
        """か行で始まる20文字程度の散文を生成するノード"""
        return node_k(state, llm)
    
    
    def node_s_wrapper(state: State):
        """さ行で始まる20文字程度の散文を生成するノード"""
        return node_s(state, llm)
    
    
    def node_final_wrapper(state: State):
        """これまでの散文をまとめて最終的なジョークを生成するノード"""
        return node_final(state, llm)
    
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(State)
    
    # ノードの追加
    graph.add_node("nodeA", node_a_wrapper)
    graph.add_node("nodeK", node_k_wrapper)
    graph.add_node("nodeS", node_s_wrapper)
    graph.add_node("node_final", node_final_wrapper)
    logger.info("✅ [AGENT] ノードの追加が完了しました (nodeA, nodeK, nodeS, node_final)")
    
    # エッジの追加（直列）
    graph.add_edge(START, "nodeA")
    graph.add_edge("nodeA", "nodeK")
    graph.add_edge("nodeK", "nodeS")
    graph.add_edge("nodeS", "node_final")
    graph.add_edge("node_final", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました (start→A→K→S→final→end)")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


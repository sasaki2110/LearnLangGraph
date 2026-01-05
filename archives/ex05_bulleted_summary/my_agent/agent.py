"""
箇条書きまとめ屋エージェントのグラフ定義

p31_streaming相当のロギングとストリーミングを実装した箇条書きまとめ屋エージェント
"""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import SummaryState
from my_agent.utils.nodes import extractor, refiner, writer
from my_agent.utils.logging_config import setup_logging, get_logger, get_log_level

# 環境変数の読み込み
load_dotenv()

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
    def extractor_node(state: SummaryState):
        """重要点抽出ノード（llmを閉包で保持）"""
        return extractor(state, llm)
    
    def refiner_node(state: SummaryState):
        """リスト精緻化ノード（llmを閉包で保持）"""
        return refiner(state, llm)
    
    def writer_node(state: SummaryState):
        """最終回答作成ノード（llmを閉包で保持）"""
        return writer(state, llm)
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(SummaryState)
    
    # ノードの追加
    graph.add_node("extractor", extractor_node)
    graph.add_node("refiner", refiner_node)
    graph.add_node("writer", writer_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (extractor, refiner, writer)")
    
    # エッジの追加
    graph.add_edge(START, "extractor")
    graph.add_edge("extractor", "refiner")
    graph.add_edge("refiner", "writer")
    graph.add_edge("writer", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


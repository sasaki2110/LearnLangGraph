"""
オウム返し＋文字数カウントエージェントのグラフ定義

このグラフは、文字数をカウントしてStateに保存（加算）するノードと、
入力メッセージの最後に「これまでの合計文字数は 〇〇 文字です」を付与して返すノードを
直列につなぐエージェントです。
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
from my_agent.utils.nodes import count_characters, parrot_with_count
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
    def count_characters_node(state: State):
        """文字数をカウントするノード"""
        return count_characters(state)
    
    
    def parrot_with_count_node(state: State):
        """オウム返しするノード（文字数情報付き）"""
        return parrot_with_count(state, llm)
    
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(State)
    
    # ノードの追加
    graph.add_node("count_characters", count_characters_node)
    graph.add_node("parrot_with_count", parrot_with_count_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (count_characters, parrot_with_count)")
    
    # エッジの追加
    graph.add_edge(START, "count_characters")
    graph.add_edge("count_characters", "parrot_with_count")
    graph.add_edge("parrot_with_count", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


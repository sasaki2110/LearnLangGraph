"""
挨拶エージェントのグラフ定義

このグラフは、入力された言語（日本語/英語）を判定し、適切な言語で挨拶を返すエージェントです。
基本的な Conditional Edge の練習として実装されています。
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
from my_agent.utils.nodes import detect_language, greet_in_english, greet_in_japanese
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
    def detect_language_node(state: State):
        """言語を判定するノード"""
        return detect_language(state, llm)
    
    
    def greet_in_english_node(state: State):
        """英語で挨拶を返すノード"""
        return greet_in_english(state, llm)
    
    
    def greet_in_japanese_node(state: State):
        """日本語で挨拶を返すノード"""
        return greet_in_japanese(state, llm)
    
    
    # 条件エッジ関数
    def route_by_language(state: State) -> str:
        """言語に基づいてルーティングする条件エッジ関数"""
        language = state.get("language")
        logger.info(f"🔀 [ROUTE] 言語に基づいてルーティング: {language}")
        
        if language == "japanese":
            return "greet_in_japanese"
        elif language == "english":
            return "greet_in_english"
        elif language == "quit":
            return END
        else:
            # デフォルトは英語
            logger.warning(f"⚠️ [ROUTE] 不明な言語: {language}。デフォルトで'greet_in_english'にルーティングします")
            return "greet_in_english"
    
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(State)
    
    # ノードの追加
    graph.add_node("detect_language", detect_language_node)
    graph.add_node("greet_in_english", greet_in_english_node)
    graph.add_node("greet_in_japanese", greet_in_japanese_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (detect_language, greet_in_english, greet_in_japanese)")
    
    # エッジの追加
    graph.add_edge(START, "detect_language")
    # 条件エッジ: 言語判定ノードから、言語に基づいて分岐
    graph.add_conditional_edges(
        "detect_language",
        route_by_language,
        {
            "greet_in_japanese": "greet_in_japanese",
            "greet_in_english": "greet_in_english",
            END: END
        }
    )
    graph.add_edge("greet_in_english", END)
    graph.add_edge("greet_in_japanese", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


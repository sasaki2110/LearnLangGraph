"""
検閲エージェントのグラフ定義

このグラフは、キャッチコピーを生成し、NGワードをチェックして、
NGワードがあれば再生成するループ構造のエージェントです。
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
from my_agent.utils.nodes import generator, checker
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
    def generator_node(state: State):
        """キャッチコピーを生成するノード"""
        return generator(state, llm)
    
    
    def checker_node(state: State):
        """NGワードをチェックするノード"""
        return checker(state)
    
    
    # 条件エッジ関数
    def route_by_ngword(state: State) -> str:
        """NGワードの有無に基づいてルーティングする条件エッジ関数"""
        has_ngword = state.get("has_ngword")
        catchphrase = state.get("catchphrase", "")
        improvement_points = state.get("improvement_points")
        messages_count = len(state.get("messages", []))
        
        logger.info(f"🔀 [ROUTE] NGワードチェック結果に基づいてルーティング")
        logger.debug(f"🔀 [ROUTE] 現在の状態: has_ngword={has_ngword}, catchphrase={catchphrase[:50] if catchphrase else None}..., improvement_points={improvement_points}, messages数={messages_count}")
        
        if has_ngword:
            # NGワードがある場合は、Generatorに戻って作り直し
            logger.info(f"🔀 [ROUTE] NGワードが検出されたため、generatorに戻ります")
            return "generator"
        else:
            # NGワードがない場合は終了
            logger.info(f"🔀 [ROUTE] NGワードが検出されなかったため、終了します")
            return END
    
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(State)
    
    # ノードの追加
    graph.add_node("generator", generator_node)
    graph.add_node("checker", checker_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (generator, checker)")
    
    # エッジの追加
    graph.add_edge(START, "generator")
    graph.add_edge("generator", "checker")
    # 条件エッジ: NGワードチェック結果に基づいて分岐
    graph.add_conditional_edges(
        "checker",
        route_by_ngword,
        {
            "generator": "generator",  # NGワードがある場合はGeneratorに戻る
            END: END  # NGワードがない場合は終了
        }
    )
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


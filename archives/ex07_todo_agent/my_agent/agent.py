"""
TODO管理エージェントのグラフ定義

このグラフは、ユーザーの依頼から「タスク」「期限」を抽出し、State内のリストを更新・削除するTODO管理エージェントです。
p31_streamingと同等のロギング・ストリーミング機能を実装しています。
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
from my_agent.utils.nodes import extract_operation, manage_todo_list, generate_response
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
    def extract_node(state: State):
        """ユーザーの発言から操作を抽出するノード"""
        return extract_operation(state, llm)
    
    
    def manage_node(state: State):
        """TODOリストを管理するノード（Python steps）"""
        return manage_todo_list(state)
    
    
    def response_node(state: State):
        """人間フレンドリーな返答を生成するノード（llmを閉包で保持）"""
        return generate_response(state, llm)
    
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(State)
    
    # ノードの追加
    graph.add_node("extract", extract_node)
    graph.add_node("manage", manage_node)
    graph.add_node("response", response_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (extract, manage, response)")
    
    # エッジの追加
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "manage")
    graph.add_edge("manage", "response")
    graph.add_edge("response", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


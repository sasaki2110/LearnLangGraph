"""
計算機ツールエージェントのグラフ定義

p31_streaming相当のロギングとストリーミングを実装した計算機ツールエージェント
"""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import MessagesState
from my_agent.utils.nodes import llm_steps, action_steps, llm_format_steps, should_continue
from my_agent.utils.tools import add, mul, sub, div
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
    model = init_chat_model(
        MODEL_NAME,
        temperature=0
    )
    logger.info("✅ [AGENT] チャットモデルの初期化が完了しました")
    
    # ツールをバインド
    tools = [add, mul, sub, div]
    logger.info(f"🔧 [AGENT] {len(tools)}個のツールをバインドします: {[tool.name for tool in tools]}")
    
    model_with_tools = model.bind_tools(tools)
    logger.info("✅ [AGENT] ツールのバインドが完了しました")
    
    # ノード関数をラップ（model_with_toolsを閉包で保持）
    def llm_steps_node(state: MessagesState):
        """リクエストに対処するノード（model_with_toolsを閉包で保持）"""
        return llm_steps(state, model_with_tools)
    
    def llm_format_steps_node(state: MessagesState):
        """回答整形ノード（model_with_toolsを閉包で保持）"""
        return llm_format_steps(state, model_with_tools)
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(MessagesState)
    
    # ノードの追加
    graph.add_node("llm_steps", llm_steps_node)
    graph.add_node("action_steps", action_steps)
    graph.add_node("llm_format_steps", llm_format_steps_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (llm_steps, action_steps, llm_format_steps)")
    
    # エッジの追加
    graph.add_edge(START, "llm_steps")
    graph.add_conditional_edges(
        "llm_steps",
        should_continue,
        {
            "action_steps": "action_steps",
            "llm_format_steps": "llm_format_steps"
        }
    )
    graph.add_edge("action_steps", "llm_format_steps")
    graph.add_edge("llm_format_steps", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


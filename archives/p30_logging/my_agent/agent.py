"""
計算エージェントのグラフ定義
"""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import MessagesState
from my_agent.utils.nodes import llm_call, tool_node, should_continue
from my_agent.utils.tools import add, multiply, divide
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
    tools = [add, multiply, divide]
    logger.info(f"🔧 [AGENT] {len(tools)}個のツールをバインドします: {[tool.name for tool in tools]}")
    
    model_with_tools = model.bind_tools(tools)
    logger.info("✅ [AGENT] ツールのバインドが完了しました")
    
    # LLM呼び出しノードをラップ（model_with_toolsを渡すため）
    def llm_call_node(state: MessagesState):
        """LLM呼び出しノード（model_with_toolsを閉包で保持）"""
        return llm_call(state, model_with_tools)
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(MessagesState)
    
    # ノードの追加
    graph.add_node("llm_call", llm_call_node)
    graph.add_node("tool_node", tool_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (llm_call, tool_node)")
    
    # エッジの追加
    graph.add_edge(START, "llm_call")
    graph.add_conditional_edges(
        "llm_call",
        should_continue,
        {
            "tool_node": "tool_node",
            END: END
        }
    )
    graph.add_edge("tool_node", "llm_call")
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


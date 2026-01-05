"""
P18v2: 基本的な中断（Interrupts）の例 - グラフ定義

LangSmith studioで実行する前提で、graphのコンパイルまでを実装しています。
invoke以降の処理はUIに任せます。

注意: LangGraph API（LangSmith studio）では、persistenceは自動的に処理されるため、
チェックポインターを明示的に指定する必要はありません。
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがインストールされていない場合はスキップ

from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import node_a, node_b, node_c
from my_agent.utils.logging_config import setup_logging, get_logger, get_log_level

# ロギングをセットアップ
log_level = get_log_level()
setup_logging(log_level=log_level, initialize=True)
logger = get_logger('agent')

logger.info("🚀 [AGENT] エージェントの初期化を開始します")

try:
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    workflow = StateGraph(State)
    
    # ノードの追加
    workflow.add_node("node_a", node_a)
    workflow.add_node("node_b", node_b)
    workflow.add_node("node_c", node_c)
    logger.info("✅ [AGENT] ノードの追加が完了しました (node_a, node_b, node_c)")
    
    # エッジの追加: nodeA → nodeB → nodeC
    workflow.add_edge(START, "node_a")
    workflow.add_edge("node_a", "node_b")
    workflow.add_edge("node_b", "node_c")
    workflow.add_edge("node_c", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    # 注意: LangGraph APIでは、persistenceは自動的に処理されるため、
    # チェックポインターを指定する必要はありません
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = workflow.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


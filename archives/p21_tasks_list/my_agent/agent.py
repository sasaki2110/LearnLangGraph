"""
タスクリスト提案機能を持つエージェントのグラフ定義
"""
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import (
    task_planner,
    task_executor,
    result_synthesizer,
    assign_tasks
)
from my_agent.utils.logging_config import setup_logging, get_logger, get_log_level

# ロギングをセットアップ
log_level = get_log_level()
setup_logging(log_level=log_level, initialize=True)
logger = get_logger('agent')

logger.info("🚀 [AGENT] エージェントの初期化を開始します")

try:
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    builder = StateGraph(State)
    
    # ノードの追加
    builder.add_node("task_planner", task_planner)
    builder.add_node("task_executor", task_executor)
    builder.add_node("result_synthesizer", result_synthesizer)
    logger.info("✅ [AGENT] ノードの追加が完了しました (task_planner, task_executor, result_synthesizer)")
    
    # エッジの追加
    builder.add_edge(START, "task_planner")
    builder.add_conditional_edges(
        "task_planner",
        assign_tasks,
        ["task_executor"]
    )
    builder.add_edge("task_executor", "result_synthesizer")
    builder.add_edge("result_synthesizer", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # グラフをコンパイル
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = builder.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


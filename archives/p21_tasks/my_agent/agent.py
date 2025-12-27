"""
タスクを使用したエージェントのグラフ定義
"""
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import call_api, process_with_different_tasks
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
    builder.add_node("call_api", call_api)
    builder.add_node("process_with_different_tasks", process_with_different_tasks)
    logger.info("✅ [AGENT] ノードの追加が完了しました (call_api, process_with_different_tasks)")
    
    # エッジの追加（順序を逆にする）
    builder.add_edge(START, "process_with_different_tasks")
    builder.add_edge("process_with_different_tasks", "call_api")
    builder.add_edge("call_api", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # LangGraph APIでは永続化が自動的に処理されるため、チェックポインタは不要
    # テストでは別途チェックポインタを設定する
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = builder.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


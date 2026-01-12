"""
ロボットアーム学習グラフ定義

このグラフは、ユーザーの指示に基づいてロボットアームを制御するエージェントです。
p31_streaming相当のロギング・ストリーミングを実装しています。
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
from my_agent.utils.nodes import extractor, planner, task_selector, tool_executor, task_updater, verifier, final_answer
from my_agent.utils.logging_config import setup_logging, get_logger, get_log_level

# ロギングをセットアップ
log_level = get_log_level()
setup_logging(log_level=log_level, initialize=True)
logger = get_logger('agent')

logger.info("🚀 [AGENT] ロボットアームエージェントの初期化を開始します")

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
    def extractor_node(state: State):
        """ユーザーメッセージから指示を取得するノード"""
        return extractor(state)
    
    
    def planner_node(state: State):
        """指示を分解するノード（llmを閉包で保持）"""
        return planner(state, llm)
    
    
    def task_selector_node(state: State):
        """次のタスクを選択するノード"""
        return task_selector(state)
    
    
    def tool_executor_node(state: State):
        """ツールを実行するノード"""
        return tool_executor(state)
    
    
    def task_updater_node(state: State):
        """タスクを完了済みにマークするノード"""
        return task_updater(state)
    
    
    def verifier_node(state: State):
        """状態を確認するノード"""
        return verifier(state)
    
    
    def final_answer_node(state: State):
        """最終回答を生成するノード（llmを閉包で保持）"""
        return final_answer(state, llm)
    
    
    # 条件分岐関数
    def should_continue(state: State) -> str:
        """
        タスクが完了したかどうかを判定し、次のノードを決定
        
        Returns:
            "end": 無限ループ防止（実行可能なタスクがない場合）
            "final_answer": タスクが完了した場合
            "task_selector": タスクがまだ完了していない場合
        """
        task_completed = state.get("task_completed", False)
        task_list = state.get("task_list", [])
        completed_tasks = state.get("completed_tasks", [])
        
        logger.debug(f"🔍 [AGENT] should_continue: task_completed={task_completed}")
        logger.debug(f"🔍 [AGENT] should_continue: 完了タスク数={len(completed_tasks)}, 総タスク数={len(task_list)}")
        
        if task_completed:
            logger.info("✅ [AGENT] すべてのタスクが完了しました。最終回答を生成します。")
            return "final_answer"
        
        # 実行可能なタスクがあるか確認
        # completed_tasksはoperator.addで追加されるため、リストのリストになっている可能性がある
        # フラット化する
        flat_completed_tasks = []
        for item in completed_tasks:
            if isinstance(item, list):
                flat_completed_tasks.extend(item)
            else:
                flat_completed_tasks.append(item)
        
        completed_task_ids = {task.get("task_id") for task in flat_completed_tasks if isinstance(task, dict) and "task_id" in task}
        remaining_tasks = [task for task in task_list if task.id not in completed_task_ids]
        
        # すべてのタスクが完了している場合も確認（念のため）
        if len(completed_task_ids) >= len(task_list):
            logger.info("✅ [AGENT] すべてのタスクが完了しました（再確認）。最終回答を生成します。")
            logger.info(f"✅ [AGENT] 完了タスク数: {len(completed_task_ids)}, 総タスク数: {len(task_list)}")
            return "final_answer"
        
        # 依存関係が満たされたタスクがあるか確認
        executable_tasks = []
        for task in remaining_tasks:
            dependencies = task.dependencies or []
            if all(dep_id in completed_task_ids for dep_id in dependencies):
                executable_tasks.append(task)
        
        if not executable_tasks and remaining_tasks:
            logger.warning("⚠️ [AGENT] 実行可能なタスクがありません。依存関係が満たされていない可能性があります。")
            logger.warning(f"⚠️ [AGENT] 残りのタスク: {[t.id for t in remaining_tasks]}")
            logger.warning(f"⚠️ [AGENT] 完了したタスク: {completed_task_ids}")
            return "end"
        
        logger.info(f"🔄 [AGENT] タスクがまだ完了していません。次のタスクを選択します（残り: {len(remaining_tasks)}個）。")
        return "task_selector"
    
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(State)
    
    # ノードの追加
    graph.add_node("extractor", extractor_node)
    graph.add_node("planner", planner_node)
    graph.add_node("task_selector", task_selector_node)
    graph.add_node("tool_executor", tool_executor_node)
    graph.add_node("task_updater", task_updater_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("final_answer", final_answer_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (extractor, planner, task_selector, tool_executor, task_updater, verifier, final_answer)")
    
    # エッジの追加
    graph.add_edge(START, "extractor")
    graph.add_edge("extractor", "planner")
    graph.add_edge("planner", "task_selector")
    graph.add_edge("task_selector", "tool_executor")
    graph.add_edge("tool_executor", "task_updater")
    graph.add_edge("task_updater", "verifier")
    
    # 条件付きエッジ（verifierから）
    graph.add_conditional_edges(
        "verifier",
        should_continue,
        {
            "end": END,
            "final_answer": "final_answer",
            "task_selector": "task_selector"
        }
    )
    
    # final_answerからendへのエッジ
    graph.add_edge("final_answer", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] ロボットアームエージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise

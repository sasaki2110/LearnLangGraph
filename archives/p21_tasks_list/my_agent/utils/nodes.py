"""
ノード関数の実装
"""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from langgraph.types import Send
from my_agent.utils.state import State, WorkerState, Task, TaskList
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')

# 環境変数の読み込み
load_dotenv()

# LLMの初期化
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
logger.info(f"🤖 [NODES] LLMを初期化します: {MODEL_NAME}")
llm = init_chat_model(
    MODEL_NAME,
    temperature=0
)
logger.info("✅ [NODES] LLMの初期化が完了しました")

# 構造化出力スキーマでLLMを拡張
logger.debug("🔧 [NODES] 構造化出力スキーマでLLMを拡張します")
planner = llm.with_structured_output(TaskList)
logger.info("✅ [NODES] プランナーの初期化が完了しました")


def _extract_user_request(state: State) -> str:
    """状態からユーザーの要求を抽出する（user_requestまたはmessagesから）"""
    # user_requestが存在する場合はそれを使用
    if "user_request" in state and state["user_request"]:
        return state["user_request"]
    
    # messagesが存在する場合は、最後のHumanMessageから抽出
    if "messages" in state and state["messages"]:
        messages = state["messages"]
        # 最後のHumanMessageを探す
        for msg in reversed(messages):
            # LangChainのメッセージオブジェクトの場合
            if hasattr(msg, "content"):
                content = msg.content
                if isinstance(content, str) and content.strip():
                    return content
                elif isinstance(content, list):
                    # メッセージのcontentがリストの場合（マルチモーダルなど）
                    text_parts = [item.get("text", "") if isinstance(item, dict) else str(item) 
                                 for item in content if isinstance(item, (str, dict))]
                    if text_parts:
                        return " ".join(text_parts)
            # 辞書形式のメッセージの場合
            elif isinstance(msg, dict):
                content = msg.get("content", "")
                if isinstance(content, str) and content.strip():
                    return content
                elif isinstance(content, list):
                    # メッセージのcontentがリストの場合
                    text_parts = [item.get("text", "") if isinstance(item, dict) else str(item) 
                                 for item in content if isinstance(item, (str, dict))]
                    if text_parts:
                        return " ".join(text_parts)
            # 文字列の場合
            elif isinstance(msg, str) and msg.strip():
                return msg
    
    # どちらも存在しない場合は空文字列を返す
    return ""


def task_planner(state: State) -> dict:
    """ユーザーの要求からタスクリストを生成する"""
    logger.info("📋 [NODE] task_planner ノードの実行を開始します")
    
    try:
        # ユーザーの要求を抽出
        user_request = _extract_user_request(state)
        logger.info(f"👤 [NODE] ユーザーの要求を抽出しました: {user_request[:100]}...")
        
        # LLMにタスクリストの生成を依頼
        logger.debug("🤖 [NODE] LLMにタスクリストの生成を依頼します")
        task_list = planner.invoke([
            SystemMessage(content="""ユーザーの要求を分析し、実行すべきタスクリストを生成してください。
各タスクは明確で実行可能なものにしてください。
タスク間の依存関係も考慮してください。
各タスクには以下の情報を含めてください：
- id: 一意な識別子（例: 'task_1', 'task_2'）
- title: タスクのタイトル
- description: タスクの詳細説明
- task_type: タスクのタイプ（'research', 'analysis', 'generation'のいずれか）
- dependencies: 依存するタスクのIDリスト（空でも可）
- priority: 優先度（1-5、5が最高）"""),
            HumanMessage(content=f"ユーザーの要求: {user_request}"),
        ])
        
        logger.info(f"✅ [NODE] タスクリストが生成されました: {len(task_list.tasks)}個のタスク")
        logger.debug(f"📋 [NODE] タスクID: {[task.id for task in task_list.tasks]}")
        
        return {"task_list": task_list.tasks}
    except Exception as e:
        logger.error(f"❌ [NODE] task_planner ノードの実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def task_executor(state: WorkerState) -> dict:
    """個別のタスクを実行するワーカー"""
    task = state['task']
    logger.info(f"🔧 [NODE] task_executor ノードの実行を開始します: タスクID={task.id}, タイプ={task.task_type}")
    logger.debug(f"📝 [NODE] タスク詳細: {task.title}")
    
    try:
        # タスクタイプに応じた処理を実行
        if task.task_type == "research":
            logger.debug("🔍 [NODE] リサーチタスクを実行します")
            result = execute_research_task(task)
        elif task.task_type == "analysis":
            logger.debug("📊 [NODE] 分析タスクを実行します")
            result = execute_analysis_task(task)
        elif task.task_type == "generation":
            logger.debug("✍️ [NODE] 生成タスクを実行します")
            result = execute_generation_task(task)
        else:
            logger.debug("⚙️ [NODE] デフォルトタスクを実行します")
            result = execute_default_task(task)
        
        logger.info(f"✅ [NODE] タスク '{task.id}' の実行が完了しました")
        
        # 結果を保存
        return {
            "completed_tasks": [{
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "task_type": task.task_type,
                "result": result,
                "status": "completed"
            }]
        }
    except Exception as e:
        logger.error(f"❌ [NODE] task_executor ノードの実行中にエラーが発生しました: タスクID={task.id} - {e}", exc_info=True)
        raise


def execute_research_task(task: Task) -> str:
    """リサーチタスクを実行"""
    logger.debug(f"🔍 [TASK] リサーチタスクを実行します: {task.title}")
    try:
        # 実際の実装では、Web検索やデータベース検索などを行う
        # ここでは簡易的な実装として、LLMにリサーチを依頼
        result = llm.invoke([
            SystemMessage(content="ユーザーの要求に基づいて、リサーチタスクを実行してください。"),
            HumanMessage(content=f"タスク: {task.title}\n説明: {task.description}\n\nこのタスクについて調査し、結果をまとめてください。"),
        ])
        logger.debug(f"✅ [TASK] リサーチタスクが完了しました: {task.title}")
        return result.content
    except Exception as e:
        logger.error(f"❌ [TASK] リサーチタスクの実行中にエラーが発生しました: {task.title} - {e}", exc_info=True)
        raise


def execute_analysis_task(task: Task) -> str:
    """分析タスクを実行"""
    logger.debug(f"📊 [TASK] 分析タスクを実行します: {task.title}")
    try:
        # 実際の実装では、データ分析やLLMによる分析などを行う
        result = llm.invoke([
            SystemMessage(content="ユーザーの要求に基づいて、分析タスクを実行してください。"),
            HumanMessage(content=f"タスク: {task.title}\n説明: {task.description}\n\nこのタスクについて分析し、結果をまとめてください。"),
        ])
        logger.debug(f"✅ [TASK] 分析タスクが完了しました: {task.title}")
        return result.content
    except Exception as e:
        logger.error(f"❌ [TASK] 分析タスクの実行中にエラーが発生しました: {task.title} - {e}", exc_info=True)
        raise


def execute_generation_task(task: Task) -> str:
    """生成タスクを実行"""
    logger.debug(f"✍️ [TASK] 生成タスクを実行します: {task.title}")
    try:
        # 実際の実装では、LLMによるコンテンツ生成などを行う
        result = llm.invoke([
            SystemMessage(content="ユーザーの要求に基づいて、コンテンツ生成タスクを実行してください。"),
            HumanMessage(content=f"タスク: {task.title}\n説明: {task.description}\n\nこのタスクに基づいてコンテンツを生成してください。"),
        ])
        logger.debug(f"✅ [TASK] 生成タスクが完了しました: {task.title}")
        return result.content
    except Exception as e:
        logger.error(f"❌ [TASK] 生成タスクの実行中にエラーが発生しました: {task.title} - {e}", exc_info=True)
        raise


def execute_default_task(task: Task) -> str:
    """デフォルトのタスク実行"""
    logger.debug(f"⚙️ [TASK] デフォルトタスクを実行します: {task.title}")
    try:
        result = llm.invoke([
            SystemMessage(content="ユーザーの要求に基づいて、タスクを実行してください。"),
            HumanMessage(content=f"タスク: {task.title}\n説明: {task.description}\n\nこのタスクを実行してください。"),
        ])
        logger.debug(f"✅ [TASK] デフォルトタスクが完了しました: {task.title}")
        return result.content
    except Exception as e:
        logger.error(f"❌ [TASK] デフォルトタスクの実行中にエラーが発生しました: {task.title} - {e}", exc_info=True)
        raise


def result_synthesizer(state: State) -> dict:
    """すべてのタスクの実行結果を統合"""
    logger.info("📊 [NODE] result_synthesizer ノードの実行を開始します")
    
    try:
        completed_tasks = state.get("completed_tasks", [])
        logger.info(f"📋 [NODE] {len(completed_tasks)}個の完了タスクを統合します")
        
        # ユーザーの要求を抽出
        user_request = _extract_user_request(state)
        logger.debug(f"👤 [NODE] ユーザーの要求: {user_request[:100]}...")
        
        # タスクの結果を整理
        logger.debug("📝 [NODE] タスクの結果を整理します")
        results_summary = "\n\n".join([
            f"タスク: {tr['title']}\n説明: {tr['description']}\n結果: {tr['result']}"
            for tr in completed_tasks
        ])
        
        # LLMに最終結果の統合を依頼
        logger.debug("🤖 [NODE] LLMに最終結果の統合を依頼します")
        final_result = llm.invoke([
            SystemMessage(content="タスクの実行結果を統合し、ユーザーに提示する形式で最終結果を生成してください。"),
            HumanMessage(content=f"ユーザーの要求: {user_request}\n\n実行結果:\n{results_summary}"),
        ])
        
        logger.info("✅ [NODE] result_synthesizer ノードの実行が完了しました")
        return {"final_result": final_result.content}
    except Exception as e:
        logger.error(f"❌ [NODE] result_synthesizer ノードの実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def assign_tasks(state: State):
    """タスクリストを各ワーカーに割り当てる"""
    logger.info("🔀 [ROUTING] assign_tasks ルーティング関数の実行を開始します")
    
    try:
        task_list = state.get("task_list", [])
        logger.info(f"📋 [ROUTING] {len(task_list)}個のタスクを割り当てます")
        
        # 依存関係を考慮してタスクをソート（簡易版）
        # 実際の実装では、より高度な依存関係解決が必要
        logger.debug("🔀 [ROUTING] 依存関係を考慮してタスクをソートします")
        sorted_tasks = sort_tasks_by_dependencies(task_list)
        logger.debug(f"📋 [ROUTING] ソート後のタスクID: {[task.id for task in sorted_tasks]}")
        
        # 各タスクに対してSendオブジェクトを作成
        send_objects = [Send("task_executor", {"task": task}) for task in sorted_tasks]
        logger.info(f"✅ [ROUTING] {len(send_objects)}個のSendオブジェクトを作成しました")
        return send_objects
    except Exception as e:
        logger.error(f"❌ [ROUTING] assign_tasks ルーティング関数の実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def sort_tasks_by_dependencies(tasks: list[Task]) -> list[Task]:
    """依存関係に基づいてタスクをソート"""
    logger.debug(f"🔀 [UTIL] {len(tasks)}個のタスクをソートします")
    try:
        # 簡易的な実装（トポロジカルソートなどが必要な場合もある）
        # ここでは優先度順にソート
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        logger.debug(f"✅ [UTIL] タスクのソートが完了しました")
        return sorted_tasks
    except Exception as e:
        logger.error(f"❌ [UTIL] タスクのソート中にエラーが発生しました: {e}", exc_info=True)
        raise


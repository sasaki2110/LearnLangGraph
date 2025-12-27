"""
ノード関数の実装
"""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from langgraph.types import Send
from my_agent.utils.state import State, WorkerState, Task, TaskList

# 環境変数の読み込み
load_dotenv()

# LLMの初期化
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
llm = init_chat_model(
    MODEL_NAME,
    temperature=0
)

# 構造化出力スキーマでLLMを拡張
planner = llm.with_structured_output(TaskList)


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
    # ユーザーの要求を抽出
    user_request = _extract_user_request(state)
    
    # LLMにタスクリストの生成を依頼
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
    
    return {"task_list": task_list.tasks}


def task_executor(state: WorkerState) -> dict:
    """個別のタスクを実行するワーカー"""
    task = state['task']
    
    # タスクタイプに応じた処理を実行
    if task.task_type == "research":
        result = execute_research_task(task)
    elif task.task_type == "analysis":
        result = execute_analysis_task(task)
    elif task.task_type == "generation":
        result = execute_generation_task(task)
    else:
        result = execute_default_task(task)
    
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


def execute_research_task(task: Task) -> str:
    """リサーチタスクを実行"""
    # 実際の実装では、Web検索やデータベース検索などを行う
    # ここでは簡易的な実装として、LLMにリサーチを依頼
    result = llm.invoke([
        SystemMessage(content="ユーザーの要求に基づいて、リサーチタスクを実行してください。"),
        HumanMessage(content=f"タスク: {task.title}\n説明: {task.description}\n\nこのタスクについて調査し、結果をまとめてください。"),
    ])
    return result.content


def execute_analysis_task(task: Task) -> str:
    """分析タスクを実行"""
    # 実際の実装では、データ分析やLLMによる分析などを行う
    result = llm.invoke([
        SystemMessage(content="ユーザーの要求に基づいて、分析タスクを実行してください。"),
        HumanMessage(content=f"タスク: {task.title}\n説明: {task.description}\n\nこのタスクについて分析し、結果をまとめてください。"),
    ])
    return result.content


def execute_generation_task(task: Task) -> str:
    """生成タスクを実行"""
    # 実際の実装では、LLMによるコンテンツ生成などを行う
    result = llm.invoke([
        SystemMessage(content="ユーザーの要求に基づいて、コンテンツ生成タスクを実行してください。"),
        HumanMessage(content=f"タスク: {task.title}\n説明: {task.description}\n\nこのタスクに基づいてコンテンツを生成してください。"),
    ])
    return result.content


def execute_default_task(task: Task) -> str:
    """デフォルトのタスク実行"""
    result = llm.invoke([
        SystemMessage(content="ユーザーの要求に基づいて、タスクを実行してください。"),
        HumanMessage(content=f"タスク: {task.title}\n説明: {task.description}\n\nこのタスクを実行してください。"),
    ])
    return result.content


def result_synthesizer(state: State) -> dict:
    """すべてのタスクの実行結果を統合"""
    completed_tasks = state.get("completed_tasks", [])
    
    # ユーザーの要求を抽出
    user_request = _extract_user_request(state)
    
    # タスクの結果を整理
    results_summary = "\n\n".join([
        f"タスク: {tr['title']}\n説明: {tr['description']}\n結果: {tr['result']}"
        for tr in completed_tasks
    ])
    
    # LLMに最終結果の統合を依頼
    final_result = llm.invoke([
        SystemMessage(content="タスクの実行結果を統合し、ユーザーに提示する形式で最終結果を生成してください。"),
        HumanMessage(content=f"ユーザーの要求: {user_request}\n\n実行結果:\n{results_summary}"),
    ])
    
    return {"final_result": final_result.content}


def assign_tasks(state: State):
    """タスクリストを各ワーカーに割り当てる"""
    task_list = state.get("task_list", [])
    
    # 依存関係を考慮してタスクをソート（簡易版）
    # 実際の実装では、より高度な依存関係解決が必要
    sorted_tasks = sort_tasks_by_dependencies(task_list)
    
    # 各タスクに対してSendオブジェクトを作成
    return [Send("task_executor", {"task": task}) for task in sorted_tasks]


def sort_tasks_by_dependencies(tasks: list[Task]) -> list[Task]:
    """依存関係に基づいてタスクをソート"""
    # 簡易的な実装（トポロジカルソートなどが必要な場合もある）
    # ここでは優先度順にソート
    return sorted(tasks, key=lambda t: t.priority, reverse=True)


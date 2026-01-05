"""
状態定義
"""
from typing import TypedDict, Optional, Annotated, List, Dict, Any
from langchain.messages import AnyMessage
import operator


class TodoItem(TypedDict):
    """TODOアイテム"""
    task_id: str  # UUID
    content: str  # タスク内容
    deadline: str  # 期限 (yyyy-mm-dd形式)
    status: str  # ステータス ("done" or "undone")


class State(TypedDict):
    """エージェントの状態"""
    messages: Annotated[List[AnyMessage], operator.add]  # メッセージ履歴
    todo_list: List[TodoItem]  # タスクID、内容、期限、ステータスを持つオブジェクトのリスト
    recent_change: Optional[str]  # 今回のターンで「何が追加/削除されたか」の要約（ユーザーへの報告用）
    operation: Optional[str]  # 抽出された操作の種類（"add", "delete", "update_status", "none"）
    extracted_data: Optional[Dict[str, Any]]  # 抽出されたデータ（操作、内容、期限、ステータスなど）


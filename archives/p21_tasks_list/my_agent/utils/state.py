"""
状態定義
"""
from typing import Annotated, List, NotRequired
from typing_extensions import TypedDict
import operator
from pydantic import BaseModel, Field
from langchain.messages import AnyMessage


# タスクの定義
class Task(BaseModel):
    """実行するタスク"""
    id: str = Field(description="タスクの一意な識別子")
    title: str = Field(description="タスクのタイトル")
    description: str = Field(description="タスクの詳細説明")
    task_type: str = Field(description="タスクのタイプ（例: 'research', 'analysis', 'generation'）")
    dependencies: List[str] = Field(default=[], description="依存するタスクのIDリスト")
    priority: int = Field(default=1, description="タスクの優先度（1-5）")


class TaskList(BaseModel):
    """タスクリスト"""
    tasks: List[Task] = Field(description="タスクのリスト")


# メインの状態
class State(TypedDict):
    """エージェントの状態"""
    user_request: NotRequired[str]  # ユーザーの要求（文字列形式）
    messages: NotRequired[Annotated[List[AnyMessage], operator.add]]  # メッセージリスト（Vercel AI SDK用）
    task_list: NotRequired[List[Task]]  # 生成されたタスクリスト
    completed_tasks: Annotated[List[dict], operator.add]  # 完了したタスクの結果
    final_result: NotRequired[str]  # 最終結果


# ワーカーの状態
class WorkerState(TypedDict):
    """ワーカーの状態"""
    task: Task  # 実行するタスク
    completed_tasks: Annotated[List[dict], operator.add]  # 完了したタスクの結果


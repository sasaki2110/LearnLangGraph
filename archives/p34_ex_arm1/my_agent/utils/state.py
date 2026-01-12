"""
状態定義
"""
from typing import TypedDict, Optional, Annotated, Literal, List, NotRequired
from typing_extensions import TypedDict as ExtTypedDict
from langchain.messages import AnyMessage
from pydantic import BaseModel, Field
import operator


# タスクの定義
class Task(BaseModel):
    """実行するタスク"""
    id: str = Field(description="タスクの一意な識別子（例: 'task_1', 'task_2'）")
    tool: str = Field(description="実行するツール名（'get_object_position', 'move_arm_to', 'control_gripper'のいずれか）")
    args: str = Field(
        description="ツールの引数（JSON文字列、例: '{\"item_name\": \"赤いコップ\"}' または '{\"x\": 10.0, \"y\": 20.0, \"z\": 5.0}'）"
    )
    dependencies: List[str] = Field(default=[], description="依存するタスクのIDリスト（このタスクを実行する前に完了する必要があるタスク）")
    description: str = Field(description="タスクの説明（例: '赤いコップの位置を取得する'）")


class TaskList(BaseModel):
    """タスクリスト"""
    tasks: List[Task] = Field(description="タスクのリスト")


class State(ExtTypedDict):
    """ロボットアームエージェントの状態"""
    messages: Annotated[list[AnyMessage], operator.add]  # メッセージ履歴
    gripper_position_x: Optional[float]  # グリッパーのX座標
    gripper_position_y: Optional[float]  # グリッパーのY座標
    gripper_position_z: Optional[float]  # グリッパーのZ座標
    gripper_state: Optional[Literal["open", "close"]]  # グリッパーの状態
    instruction: Optional[str]  # ユーザーからの指示
    task_list: NotRequired[List[Task]]  # 生成されたタスクリスト
    completed_tasks: Annotated[List[dict], operator.add]  # 完了したタスクの結果
    object_positions: NotRequired[dict]  # 取得済みの物体位置（例: {"赤いコップ": (10.0, 20.0, 5.0)}）
    current_task_id: NotRequired[str]  # 現在実行中のタスクID
    task_completed: bool  # すべてのタスクが完了したかどうか
    _last_task_id: NotRequired[str]  # 一時的なフィールド：最後に実行したタスクID（tool_executor -> task_updater間で使用）
    _last_tool_result: NotRequired[dict]  # 一時的なフィールド：最後のツール実行結果（tool_executor -> task_updater間で使用）

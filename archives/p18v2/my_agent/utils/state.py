"""
グラフの状態定義
"""
from typing import Annotated
from typing_extensions import TypedDict
from operator import add


class State(TypedDict):
    """グラフの状態を定義"""
    messages: Annotated[list[str], add]  # メッセージのリスト
    approved: bool  # 承認状態
    action: str  # 実行するアクション


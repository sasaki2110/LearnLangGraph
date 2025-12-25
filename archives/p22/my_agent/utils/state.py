"""
グラフの状態定義
"""
from typing import Annotated
from typing_extensions import TypedDict, NotRequired
from operator import add


class State(TypedDict):
    """グラフの状態を定義"""
    topic: NotRequired[str]  # トピック
    message: NotRequired[str]  # メッセージ
    steps: Annotated[list[str], add]  # 実行ステップの履歴（タイムトラベルで確認しやすくするため）


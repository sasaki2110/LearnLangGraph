"""
状態定義
"""
from typing import TypedDict, Optional, Annotated
from langchain.messages import AnyMessage
import operator


class State(TypedDict):
    """エージェントの状態"""
    messages: Annotated[list[AnyMessage], operator.add]  # メッセージ履歴
    jokes: Annotated[list[str], operator.add]  # ジョーク集


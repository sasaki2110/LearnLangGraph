"""
状態定義
"""
from typing_extensions import TypedDict, Annotated
from langchain.messages import AnyMessage
import operator


class MessagesState(TypedDict):
    """エージェントの状態"""
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


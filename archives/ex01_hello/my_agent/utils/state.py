"""
状態定義
"""
from typing import TypedDict, Optional, Annotated, Literal
from langchain.messages import AnyMessage
import operator


class State(TypedDict):
    """エージェントの状態"""
    messages: Annotated[list[AnyMessage], operator.add]  # Vercel AI SDKからの入力と出力
    language: Optional[Literal["japanese", "english", "quit"]]  # 判定された言語


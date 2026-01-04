"""
状態定義
"""
from typing import TypedDict, Optional, Annotated
from langchain.messages import AnyMessage
import operator


class State(TypedDict):
    """エージェントの状態"""
    messages: Annotated[list[AnyMessage], operator.add]  # メッセージ履歴
    new_product_catchphrase_idea: Optional[str]  # ユーザーが最初に提示したキャッチフレーズ案
    catchphrase: Optional[str]  # 生成されたキャッチフレーズ
    has_ngword: Optional[bool]  # NGワードが含まれるか？
    improvement_points: Optional[str]  # 改善ポイント


"""
状態定義
"""
from typing_extensions import TypedDict, Optional
from langchain.messages import AnyMessage
from typing import Annotated
from operator import add


class SNSState(TypedDict):
    """エージェントの状態"""
    messages: Annotated[list[AnyMessage], add]  # メッセージ履歴
    theme: Optional[str]  # ユーザーが指定した投稿のテーマ
    draft_post: Optional[str]  # 投稿下書き（承認前）
    final_post: Optional[str]  # 最終投稿
    approved: Optional[bool]  # 承認状態


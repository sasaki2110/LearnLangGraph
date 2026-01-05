"""
状態定義
"""
from typing import TypedDict, Optional, Annotated
from langchain.messages import AnyMessage
import operator


class State(TypedDict):
    """エージェントの状態"""
    messages: Annotated[list[AnyMessage], operator.add]  # メッセージ履歴
    theme: Optional[str]  # ユーザーが指定したリサーチ対象のテーマ
    survey_results: Annotated[list[str], operator.add]  # 調査結果を格納していく配列
    is_sufficient: Optional[bool]  # 十分かどうか
    tool_count: Annotated[int, operator.add]  # リサーチツールを呼んだ回数（モック実装で、何番目のメッセージを返すかを管理）
    llm_call_count: Annotated[int, operator.add]  # 無限ループ防止のカウンター


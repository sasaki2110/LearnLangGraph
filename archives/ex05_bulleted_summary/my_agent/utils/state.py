"""
状態定義
"""
from typing_extensions import TypedDict, Annotated, Optional
from langchain.messages import AnyMessage
import operator


class SummaryState(TypedDict):
    """エージェントの状態"""
    messages: Annotated[list[AnyMessage], operator.add]  # メッセージ履歴
    raw_text: Optional[str]  # 元の文書
    extracted_items: Optional[list[str]]  # 文書から抽出された重要なトピック・事実を箇条書きにしたもの
    refined_items: Optional[list[str]]  # 重複を削り、優先順位で並べ変えたもの
    final_report: Optional[str]  # 最終的な回答


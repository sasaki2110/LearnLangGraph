"""
状態定義
"""
from typing import NotRequired
from typing_extensions import TypedDict


class State(TypedDict):
    """エージェントの状態"""
    urls: list[str]
    results: NotRequired[list[str]]
    random_id: NotRequired[str]
    processed: NotRequired[str]
    url_result: NotRequired[str]
    task_1_result: NotRequired[str]
    task_2_result: NotRequired[str]
    task_3_result: NotRequired[str]


"""
共通フィクスチャ
"""
import pytest
from my_agent.agent import graph


@pytest.fixture
def calculator_graph():
    """計算エージェントのグラフフィクスチャ"""
    return graph


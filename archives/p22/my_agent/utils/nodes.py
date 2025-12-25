"""
ノード関数の定義
"""
import random
from datetime import datetime
from my_agent.utils.state import State


def generate_topic(state: State) -> dict:
    """トピックを生成"""
    # シンプルな例として、ランダムにトピックを選択
    topics = ["cats", "dogs", "programming", "coffee", "travel"]
    topic = random.choice(topics)
    timestamp = datetime.now().strftime("%H:%M:%S")
    step_info = f"[{timestamp}] Step 1: generate_topic → topic='{topic}'"
    return {
        "topic": topic,
        "steps": [step_info]
    }


def write_message(state: State) -> dict:
    """トピックに基づいてメッセージを生成"""
    topic = state.get("topic", "unknown")
    message = f"A message about {topic}"
    timestamp = datetime.now().strftime("%H:%M:%S")
    step_info = f"[{timestamp}] Step 2: write_message → message='{message}'"
    return {
        "message": message,
        "steps": [step_info]
    }


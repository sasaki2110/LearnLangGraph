"""
基本的なストリーミングの例

このスクリプトは、LangGraphの基本的なストリーミング機能を実装しています。
stream_mode="updates"を使用して、各ノード後のグラフ状態の更新のみをストリームします。

実際にLLMを呼び出して、トピックの精緻化とジョーク生成を行います。
"""

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from typing import TypedDict
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
print("モデル名：", MODEL_NAME)

llm = init_chat_model(
    MODEL_NAME,
    temperature=0
)


class State(TypedDict):
    topic: str
    joke: str


def refine_topic(state: State):
    """トピックを精緻化するノード（LLMを使用）"""
    prompt = f"以下のトピックを、より面白く魅力的なトピックに精緻化してください。簡潔に1文で答えてください。\n\nトピック: {state['topic']}"
    
    messages = [
        SystemMessage(content="あなたはトピックを面白く精緻化する専門家です。"),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    refined_topic = response.content.strip()
    
    return {"topic": refined_topic}


def generate_joke(state: State):
    """ジョークを生成するノード（LLMを使用）"""
    prompt = f"以下のトピックについて、面白いジョークを1つ生成してください。\n\nトピック: {state['topic']}"
    
    messages = [
        SystemMessage(content="あなたは面白いジョークを生成するコメディアンです。"),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    joke = response.content.strip()
    
    return {"joke": joke}


# グラフの構築
graph = (
    StateGraph(State)
    .add_node("refine_topic", refine_topic)
    .add_node("generate_joke", generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .add_edge("generate_joke", END)
    .compile()
)


if __name__ == "__main__":
    # stream()メソッドは、ストリーム出力を生成するイテレータを返します
    print("ストリーミング開始...")
    print("=" * 60)
    
    print("\n[モード: updates] 各ノード後の状態更新をストリーム")
    print("-" * 60)
    
    for chunk in graph.stream(
        {"topic": "アイスクリーム"},
        stream_mode="updates",  # 各ノード後のグラフ状態の更新のみをストリーム
    ):
        node_name = list(chunk.keys())[0]
        update = chunk[node_name]
        print(f"\n[ノード: {node_name}]")
        for key, value in update.items():
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("ストリーミング完了")


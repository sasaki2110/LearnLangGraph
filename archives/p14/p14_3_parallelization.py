from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
print("モデル名：",MODEL_NAME)

llm = init_chat_model(
    MODEL_NAME,
    temperature=0
)

# グラフの状態
class State(TypedDict):
    topic: str
    joke: str
    story: str
    poem: str
    combined_output: str

# ノード
def call_llm_1(state: State):
    """最初のLLM呼び出しでジョークを生成"""
    msg = llm.invoke(f"{state['topic']}についてジョークを書いてください")
    return {"joke": msg.content}

def call_llm_2(state: State):
    """2回目のLLM呼び出しでストーリーを生成"""
    msg = llm.invoke(f"{state['topic']}についてストーリーを書いてください")
    return {"story": msg.content}

def call_llm_3(state: State):
    """3回目のLLM呼び出しで詩を生成"""
    msg = llm.invoke(f"{state['topic']}について詩を書いてください")
    return {"poem": msg.content}

def aggregator(state: State):
    """ジョークとストーリーを1つの出力に結合"""
    combined = f"{state['topic']}についてのストーリー、ジョーク、詩です！\n\n"
    combined += f"ストーリー:\n{state['story']}\n\n"
    combined += f"ジョーク:\n{state['joke']}\n\n"
    combined += f"詩:\n{state['poem']}"
    return {"combined_output": combined}

# ワークフローの構築
parallel_builder = StateGraph(State)
parallel_builder.add_node("call_llm_1", call_llm_1)
parallel_builder.add_node("call_llm_2", call_llm_2)
parallel_builder.add_node("call_llm_3", call_llm_3)
parallel_builder.add_node("aggregator", aggregator)

# ノードを接続するエッジを追加（並列実行）
parallel_builder.add_edge(START, "call_llm_1")
parallel_builder.add_edge(START, "call_llm_2")
parallel_builder.add_edge(START, "call_llm_3")
parallel_builder.add_edge("call_llm_1", "aggregator")
parallel_builder.add_edge("call_llm_2", "aggregator")
parallel_builder.add_edge("call_llm_3", "aggregator")
parallel_builder.add_edge("aggregator", END)

parallel_workflow = parallel_builder.compile()

state = parallel_workflow.invoke({"topic": "飴ちゃん"})
print("="*50)
print(state["combined_output"])
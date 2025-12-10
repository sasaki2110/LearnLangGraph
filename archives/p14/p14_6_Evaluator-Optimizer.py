from typing_extensions import Literal, TypedDict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
print("モデル名：", MODEL_NAME)

llm = init_chat_model(
    MODEL_NAME,
    temperature=0
)

# グラフの状態
class State(TypedDict):
    joke: str
    topic: str
    feedback: str
    funny_or_not: str

# 評価に使用する構造化出力のスキーマ
class Feedback(BaseModel):
    grade: Literal["funny", "not funny"] = Field(
        description="ジョークが面白いかどうかを決定してください。"
    )
    feedback: str = Field(
        description="ジョークが面白くない場合、改善方法についてフィードバックを提供してください。"
    )

# 構造化出力スキーマでLLMを拡張
evaluator = llm.with_structured_output(Feedback)

# ノード
def llm_call_generator(state: State):
    """LLMがジョークを生成"""
    if state.get("feedback"):
        msg = llm.invoke(
            f"{state['topic']}についてジョークを書いてください。ただし、フィードバックを考慮してください: {state['feedback']}"
        )
    else:
        msg = llm.invoke(f"{state['topic']}についてジョークを書いてください")
    return {"joke": msg.content}

def llm_call_evaluator(state: State):
    """LLMがジョークを評価"""
    grade = evaluator.invoke(f"ジョークを評価してください {state['joke']}")
    print("="*50)
    print("funny_or_not:", grade.grade, "feedback:", grade.feedback)
    return {"funny_or_not": grade.grade, "feedback": grade.feedback}

# 評価者のフィードバックに基づいてジョーク生成器にルーティングするか、終了する条件付きエッジ関数
def route_joke(state: State):
    """評価者のフィードバックに基づいてジョーク生成器にルーティングするか、終了する"""
    if state["funny_or_not"] == "funny":
        return "Accepted"
    elif state["funny_or_not"] == "not funny":
        return "Rejected + Feedback"

# ワークフローの構築
optimizer_builder = StateGraph(State)
optimizer_builder.add_node("llm_call_generator", llm_call_generator)
optimizer_builder.add_node("llm_call_evaluator", llm_call_evaluator)

# ノードを接続するエッジを追加
optimizer_builder.add_edge(START, "llm_call_generator")
optimizer_builder.add_edge("llm_call_generator", "llm_call_evaluator")
optimizer_builder.add_conditional_edges(
    "llm_call_evaluator",
    route_joke,
    {  # route_jokeが返す名前: 次に訪問するノード名
        "Accepted": END,
        "Rejected + Feedback": "llm_call_generator",
    },
)

# ワークフローをコンパイル
optimizer_workflow = optimizer_builder.compile()

# 実行
state = optimizer_workflow.invoke({"topic": "プログラミング"})
print("="*50)
print("生成されたジョーク:")
print(state["joke"])
print("="*50)
print("評価結果:", state["funny_or_not"])
if state.get("feedback"):
    print("フィードバック:", state["feedback"])

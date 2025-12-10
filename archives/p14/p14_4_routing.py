from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
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
# ルーティングロジックとして使用する構造化出力のスキーマ
class Route(BaseModel):
    step: Literal["poem", "story", "joke"] = Field(
        None, description="ルーティングプロセスの次のステップ"
    )

# 構造化出力スキーマでLLMを拡張
router = llm.with_structured_output(Route)

# 状態
class State(TypedDict):
    input: str
    decision: str
    output: str

# ノード
def llm_call_1(state: State):
    """ストーリーを書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_2(state: State):
    """ジョークを書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_3(state: State):
    """詩を書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_router(state: State):
    """入力を適切なノードにルーティング"""
    # ルーティングロジックとして機能する構造化出力で拡張LLMを実行
    decision = router.invoke([
        SystemMessage(content="ユーザーのリクエストに基づいて、ストーリー、ジョーク、または詩にルーティングしてください。"),
        HumanMessage(content=state["input"]),
    ])
    return {"decision": decision.step}

# 適切なノードにルーティングする条件付きエッジ関数
def route_decision(state: State):
    print("decision:", state["decision"])
    # 次に訪問したいノード名を返す
    if state["decision"] == "story":
        return "llm_call_1"
    elif state["decision"] == "joke":
        return "llm_call_2"
    elif state["decision"] == "poem":
        return "llm_call_3"

# ワークフローの構築
router_builder = StateGraph(State)
router_builder.add_node("llm_call_1", llm_call_1)
router_builder.add_node("llm_call_2", llm_call_2)
router_builder.add_node("llm_call_3", llm_call_3)
router_builder.add_node("llm_call_router", llm_call_router)

# ノードを接続するエッジを追加
router_builder.add_edge(START, "llm_call_router")
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {  # route_decisionが返す名前: 次に訪問するノード名
        "llm_call_1": "llm_call_1",
        "llm_call_2": "llm_call_2",
        "llm_call_3": "llm_call_3",
    },
)
router_builder.add_edge("llm_call_1", END)
router_builder.add_edge("llm_call_2", END)
router_builder.add_edge("llm_call_3", END)

# ワークフローをコンパイル
router_workflow = router_builder.compile()

#state = router_workflow.invoke({"input": "story"})
state = router_workflow.invoke({"input": "飴ちゃんを主題にした論文"})
print("="*50)
print(state["output"])
from typing import Annotated, List
import operator
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
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

# 計画に使用する構造化出力のスキーマ
class Section(BaseModel):
    name: str = Field(description="レポートのこのセクションの名前")
    description: str = Field(description="このセクションでカバーされる主要なトピックと概念の概要")

class Sections(BaseModel):
    sections: List[Section] = Field(description="レポートのセクション")

# 構造化出力スキーマでLLMを拡張
planner = llm.with_structured_output(Sections)

# グラフの状態
class State(TypedDict):
    topic: str  # レポートのトピック
    sections: list[Section]  # レポートセクションのリスト
    completed_sections: Annotated[list, operator.add]  # すべてのワーカーが並列にこのキーに書き込む
    final_report: str  # 最終レポート

# ワーカーの状態
class WorkerState(TypedDict):
    section: Section
    completed_sections: Annotated[list, operator.add]

# ノード
def orchestrator(state: State):
    """レポートの計画を生成するオーケストレーター"""
    # クエリを生成
    report_sections = planner.invoke([
        SystemMessage(content="レポートの計画を生成してください。"),
        HumanMessage(content=f"レポートのトピックは次のとおりです: {state['topic']}"),
    ])
    return {"sections": report_sections.sections}

def llm_call(state: WorkerState):
    """ワーカーがレポートのセクションを書く"""
    # セクションを生成
    section = llm.invoke([
        SystemMessage(
            content="提供された名前と説明に従ってレポートセクションを書いてください。各セクションに前書きを含めないでください。マークダウン形式を使用してください。"
        ),
        HumanMessage(
            content=f"セクション名: {state['section'].name}、説明: {state['section'].description}"
        ),
    ])
    # 更新されたセクションを完了したセクションに書き込む
    return {"completed_sections": [section.content]}

def synthesizer(state: State):
    """セクションから完全なレポートを統合"""
    # 完了したセクションのリスト
    completed_sections = state["completed_sections"]
    # 完了したセクションを文字列にフォーマットして、最終セクションのコンテキストとして使用
    completed_report_sections = "\n\n---\n\n".join(completed_sections)
    return {"final_report": completed_report_sections}

# 各セクションにワーカーを割り当てる条件付きエッジ関数
def assign_workers(state: State):
    """計画の各セクションにワーカーを割り当てる"""
    # Send() API経由で並列にセクション書き込みを開始
    return [Send("llm_call", {"section": s}) for s in state["sections"]]

# ワークフローの構築
orchestrator_worker_builder = StateGraph(State)
orchestrator_worker_builder.add_node("orchestrator", orchestrator)
orchestrator_worker_builder.add_node("llm_call", llm_call)
orchestrator_worker_builder.add_node("synthesizer", synthesizer)

# ノードを接続するエッジを追加
orchestrator_worker_builder.add_edge(START, "orchestrator")
orchestrator_worker_builder.add_conditional_edges(
    "orchestrator", assign_workers, ["llm_call"]
)
orchestrator_worker_builder.add_edge("llm_call", "synthesizer")
orchestrator_worker_builder.add_edge("synthesizer", END)

# ワークフローをコンパイル
orchestrator_worker = orchestrator_worker_builder.compile()

# 実行
state = orchestrator_worker.invoke({"topic": "人工知能の歴史と未来"})
print("="*50)
print(state["final_report"])

from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

llm = init_chat_model(
    MODEL_NAME,
    temperature=0
)

# グラフの状態
class State(TypedDict):
    topic: str
    joke: str
    improved_joke: str
    final_joke: str

# ノード
def generate_joke(state: State):
    """最初のLLM呼び出しで初期ジョークを生成"""
    print("="*50)
    print(f"generate_joke: {state['topic']}について短いジョークを書いてください")
    msg = llm.invoke(f"{state['topic']}について短いジョークを書いてください")
    print(msg.content)
    return {"joke": msg.content}

def check_punchline(state: State):
    """ジョークにオチがあるかチェックするゲート関数"""
    # シンプルなチェック - ジョークに「?」や「!」が含まれているか
    if "?" in state["joke"] or "!" in state["joke"]:
        return "Pass"
    return "Fail"

def improve_joke(state: State):
    """2回目のLLM呼び出しでジョークを改善"""
    print("="*50)
    print(f"このジョークをより面白くするために言葉遊びを追加してください: {state['joke']}")
    msg = llm.invoke(f"このジョークをより面白くするために言葉遊びを追加してください: {state['joke']}")
    print(msg.content)
    return {"improved_joke": msg.content}

def polish_joke(state: State):
    """3回目のLLM呼び出しで最終的な仕上げ"""
    print("="*50)
    print(f"このジョークに驚きの展開を追加してください: {state['improved_joke']}")
    msg = llm.invoke(f"このジョークに驚きの展開を追加してください: {state['improved_joke']}")
    print(msg.content)
    return {"final_joke": msg.content}

# ワークフローの構築
workflow = StateGraph(State)
workflow.add_node("generate_joke", generate_joke)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)

# ノードを接続するエッジを追加
workflow.add_edge(START, "generate_joke")
workflow.add_conditional_edges(
    "generate_joke", 
    check_punchline, 
    {"Fail": "improve_joke", "Pass": END}
)
workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)

# コンパイル
chain = workflow.compile()

state = chain.invoke({"topic": "飴ちゃん"})
print("="*50)
print(state["final_joke"])
"""
計算エージェントのグラフ定義
"""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import MessagesState
from my_agent.utils.nodes import llm_call, tool_node, should_continue
from my_agent.utils.tools import add, multiply, divide

# 環境変数の読み込み
load_dotenv()

# OpenAI設定
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# モデルの初期化
model = init_chat_model(
    MODEL_NAME,
    temperature=0
)

# ツールをバインド
tools = [add, multiply, divide]
model_with_tools = model.bind_tools(tools)

# LLM呼び出しノードをラップ（model_with_toolsを渡すため）
def llm_call_node(state: MessagesState):
    """LLM呼び出しノード（model_with_toolsを閉包で保持）"""
    return llm_call(state, model_with_tools)


# グラフの構築
graph = StateGraph(MessagesState)

# ノードの追加
graph.add_node("llm_call", llm_call_node)
graph.add_node("tool_node", tool_node)

# エッジの追加
graph.add_edge(START, "llm_call")
graph.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",
        END: END
    }
)
graph.add_edge("tool_node", "llm_call")

# コンパイルしてモジュールレベルの変数に代入
# langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
graph = graph.compile()

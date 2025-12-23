"""
ノード関数の実装
"""
from typing import Literal
from langchain.messages import SystemMessage, ToolMessage
from langgraph.graph import END
from my_agent.utils.state import MessagesState
from my_agent.utils.tools import add, multiply, divide


# ツールを名前でマッピング
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}


def llm_call(state: MessagesState, model_with_tools):
    """LLMがツールを呼び出すかどうかを決定します。"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }


def tool_node(state: MessagesState):
    """ツール呼び出しを実行します。"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


def should_continue(state: MessagesState):
    """LLMがツールを呼び出したかどうかを確認します。"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # LLMがツールを呼び出した場合、アクションを実行
    if last_message.tool_calls:
        return "tool_node"
    # それ以外の場合、停止（ユーザーに返信）
    return END

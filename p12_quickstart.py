"""
LangGraph クイックスタート
公式ドキュメント: https://docs.langchain.com/oss/python/langgraph/quickstart

この例では、Graph APIを使用して計算エージェントを構築します。
OpenAI API（gpt-4o-mini）を使用します。
"""

from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage, SystemMessage, ToolMessage, HumanMessage
from typing_extensions import TypedDict, Annotated
from typing import Literal
from langgraph.graph import StateGraph, START, END
import operator
import os
from dotenv import load_dotenv

# ============================================
# 環境変数の読み込み
# ============================================
# .envファイルから環境変数を読み込む
load_dotenv()

# ============================================
# OpenAI設定
# ============================================
# 使用するモデル名（環境変数で変更可能）
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

print("="*50)
print("OpenAI API設定")
print("="*50)
print(f"Model: {MODEL_NAME}")
print("API Key: .envファイルから読み込み")
print("="*50)

# APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print("\n⚠️  警告: OPENAI_API_KEY が設定されていません。")
    print(".envファイルに以下のように設定してください:")
    print('OPENAI_API_KEY="your-api-key-here"')
    print("\n.env.exampleを参考に.envファイルを作成してください。")
    print()

# ============================================
# 1. ツールとモデルの定義
# ============================================
print("\n1. ツールとモデルの定義中...")

# OpenAI APIを使用
model = init_chat_model(
    MODEL_NAME,
    temperature=0
)

# ツールの定義
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.
    
    Args:
        a: First int
        b: Second int
    """
    return a * b

@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.
    
    Args:
        a: First int
        b: Second int
    """
    return a + b

@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.
    
    Args:
        a: First int
        b: Second int
    """
    return a / b

# LLMにツールをバインド
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

print("✓ ツールとモデルの定義が完了しました")

# ============================================
# 2. 状態の定義
# ============================================
print("\n2. 状態の定義中...")

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

print("✓ 状態の定義が完了しました")

# ============================================
# 3. モデルノードの定義
# ============================================
print("\n3. モデルノードの定義中...")

def llm_call(state: dict):
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

print("✓ モデルノードの定義が完了しました")

# ============================================
# 4. ツールノードの定義
# ============================================
print("\n4. ツールノードの定義中...")

def tool_node(state: dict):
    """ツール呼び出しを実行します。"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

print("✓ ツールノードの定義が完了しました")

# ============================================
# 5. 終了ロジックの定義
# ============================================
print("\n5. 終了ロジックの定義中...")

def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """LLMがツールを呼び出したかどうかを確認します。"""
    messages = state["messages"]
    last_message = messages[-1]
    
    # LLMがツールを呼び出した場合、アクションを実行
    if last_message.tool_calls:
        return "tool_node"
    # それ以外の場合、停止（ユーザーに返信）
    return END

print("✓ 終了ロジックの定義が完了しました")

# ============================================
# 6. エージェントの構築とコンパイル
# ============================================
print("\n6. エージェントの構築とコンパイル中...")

# ワークフローの構築
agent_builder = StateGraph(MessagesState)

# ノードの追加
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# ノードを接続するエッジの追加
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# エージェントのコンパイル
agent = agent_builder.compile()

print("✓ エージェントの構築とコンパイルが完了しました")

# ============================================
# 7. エージェントの実行
# ============================================
print("\n" + "="*50)
print("エージェントの実行")
print("="*50)

# テストケース0: 挨拶
print("\n【テストケース0】こんにちは")
messages = [HumanMessage(content="こんにちは")]
result = agent.invoke({"messages": messages, "llm_calls": 0})

print("\n結果:")
for m in result["messages"]:
    m.pretty_print()

print(f"\nLLM呼び出し回数: {result['llm_calls']}")

# テストケース1: 加算
print("\n【テストケース1】3 + 4 を計算")
messages = [HumanMessage(content="Add 3 and 4.")]
result = agent.invoke({"messages": messages, "llm_calls": 0})

print("\n結果:")
for m in result["messages"]:
    m.pretty_print()

print(f"\nLLM呼び出し回数: {result['llm_calls']}")

# テストケース2: 乗算
print("\n" + "-"*50)
print("\n【テストケース2】5 × 6 を計算")
messages = [HumanMessage(content="Multiply 5 and 6.")]
result = agent.invoke({"messages": messages, "llm_calls": 0})

print("\n結果:")
for m in result["messages"]:
    m.pretty_print()

print(f"\nLLM呼び出し回数: {result['llm_calls']}")

# テストケース3: 除算
print("\n" + "-"*50)
print("\n【テストケース3】10 ÷ 2 を計算")
messages = [HumanMessage(content="Divide 10 by 2.")]
result = agent.invoke({"messages": messages, "llm_calls": 0})

print("\n結果:")
for m in result["messages"]:
    m.pretty_print()

print(f"\nLLM呼び出し回数: {result['llm_calls']}")

print("\n" + "="*50)
print("クイックスタートが完了しました！")
print("="*50)


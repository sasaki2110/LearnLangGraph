"""
基本的なLLMトークンストリーミングの例

このスクリプトは、LangGraphのLLMトークンストリーミング機能を実装しています。
stream_mode="messages"を使用して、LLMの出力をトークン単位でリアルタイムに取得します。

messagesモードでは、LLMが呼び出される任意のグラフノードから、
2タプル（LLMトークン、メタデータ）をストリームします。
"""

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from typing import TypedDict, Annotated
import operator
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
    messages: Annotated[list, operator.add]


def llm_node(state: State):
    """LLMを呼び出すノード"""
    # システムメッセージを追加（オプション）
    messages = [
        SystemMessage(content="あなたは親切で知識豊富なアシスタントです。"),
    ] + state["messages"]
    
    response = llm.invoke(messages)
    return {"messages": [response]}


# グラフの構築
graph = (
    StateGraph(State)
    .add_node("llm", llm_node)
    .add_edge(START, "llm")
    .add_edge("llm", END)
    .compile()
)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("【基本的なLLMトークンストリーミング】")
    print("=" * 80)
    print("\nstream_mode='messages'を使用して、LLMの出力をトークン単位で取得します。")
    print("各トークンはリアルタイムで表示されます。\n")
    print("-" * 80)
    
    # LLMトークンをストリーム
    print("\n[ユーザー] プログラミングについて面白いジョークを教えてください。\n")
    print("[AI] ", end="", flush=True)
    
    for token, metadata in graph.stream(
        {"messages": [HumanMessage(content="プログラミングについて面白いジョークを教えてください。")]},
        stream_mode="messages",  # messagesモードでトークン単位のストリーミング
    ):
        # tokenはAIMessageオブジェクトなので、content属性からテキストを取得
        token_text = token.content if hasattr(token, 'content') else str(token)
        # トークンを逐次表示（改行なし、即座にフラッシュ）
        print(token_text, end="", flush=True)
        # metadataにはノード名、LLM呼び出し情報などが含まれる
    
    print("\n")  # 最後に改行
    print("-" * 80)
    
    print("\n" + "=" * 80)
    print("【メタデータの確認例】")
    print("=" * 80)
    print("\nメタデータには、ノード名やLLM呼び出し情報などが含まれます。")
    print("以下は、メタデータの内容を確認する例です。\n")
    print("-" * 80)
    
    print("\n[ユーザー] 短い詩を書いてください。\n")
    print("[AI] ", end="", flush=True)
    
    token_count = 0
    for token, metadata in graph.stream(
        {"messages": [HumanMessage(content="AIについて短い詩を書いてください。")]},
        stream_mode="messages",
    ):
        # tokenはAIMessageオブジェクトなので、content属性からテキストを取得
        token_text = token.content if hasattr(token, 'content') else str(token)
        print(token_text, end="", flush=True)
        token_count += 1
        
        # 最初のトークンでメタデータを表示（デモ用）
        if token_count == 1:
            print("\n\n[メタデータの例]")
            print(f"  ノード名: {metadata.get('node', 'N/A')}")
            print(f"  メタデータ全体: {metadata}")
            print("\n[AI] ", end="", flush=True)
    
    print("\n")
    print("-" * 80)
    print(f"\n総トークン数: {token_count}")
    print("=" * 80)
    print("\nストリーミング完了")


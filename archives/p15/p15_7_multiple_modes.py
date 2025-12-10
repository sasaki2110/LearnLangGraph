"""
複数のモードとLLMトークンの組み合わせの例

このスクリプトは、LangGraphで複数のストリームモードを同時に使用する方法を示します。
stream_mode=["updates", "messages"]を使用して、ノードの更新情報とLLMトークンを
同時にストリームします。

これにより、ノードの実行状況とLLMの出力を同時に監視できます。
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
    print("【複数のモードとLLMトークンの組み合わせ】")
    print("=" * 80)
    print("\nstream_mode=['updates', 'messages']を使用して、")
    print("ノードの更新情報とLLMトークンを同時にストリームします。\n")
    print("-" * 80)
    
    print("\n[ユーザー] プログラミングについて面白いジョークを教えてください。\n")
    
    # ノードの更新とLLMトークンを同時にストリーム
    update_count = 0
    token_count = 0
    
    for mode, chunk in graph.stream(
        {"messages": [HumanMessage(content="プログラミングについて面白いジョークを教えてください。")]},
        stream_mode=["updates", "messages"],  # 複数のモードを同時にストリーム
    ):
        if mode == "updates":
            # updatesモード: ノードの更新情報
            update_count += 1
            node_name = list(chunk.keys())[0]
            update = chunk[node_name]
            print(f"\n[Node Update #{update_count}]")
            print(f"  ノード名: {node_name}")
            print(f"  更新内容: {update}")
        
        elif mode == "messages":
            # messagesモード: LLMトークン
            token, metadata = chunk
            token_count += 1
            
            # 最初のトークンで開始を表示
            if token_count == 1:
                node_name = metadata.get("langgraph_node", "unknown")
                print(f"\n[LLM Tokens from '{node_name}'] ", end="", flush=True)
            
            # tokenはAIMessageオブジェクトなので、content属性からテキストを取得
            token_text = token.content if hasattr(token, 'content') else str(token)
            print(token_text, end="", flush=True)
    
    print("\n")  # 最後に改行
    print("-" * 80)
    print(f"\n[集計]")
    print(f"  ノード更新数: {update_count}")
    print(f"  トークン数: {token_count}")
    
    print("\n" + "=" * 80)
    print("【詳細な動作確認】")
    print("=" * 80)
    print("\n各モードの出力を区別して表示します。\n")
    print("-" * 80)
    
    print("\n[ユーザー] AIについて短い説明を書いてください。\n")
    
    update_events = []
    token_events = []
    
    for mode, chunk in graph.stream(
        {"messages": [HumanMessage(content="AIについて短い説明を書いてください。")]},
        stream_mode=["updates", "messages"],
    ):
        if mode == "updates":
            node_name = list(chunk.keys())[0]
            update_events.append({
                "node": node_name,
                "update": chunk[node_name]
            })
            print(f"[UPDATE] ノード '{node_name}' が実行されました")
        
        elif mode == "messages":
            token, metadata = chunk
            token_text = token.content if hasattr(token, 'content') else str(token)
            token_events.append({
                "token": token_text,
                "node": metadata.get("langgraph_node", "unknown")
            })
            # トークンは連続して表示
            print(token_text, end="", flush=True)
    
    print("\n\n" + "-" * 80)
    print(f"\n[詳細な集計]")
    print(f"  ノード更新イベント数: {len(update_events)}")
    print(f"  トークンイベント数: {len(token_events)}")
    
    if update_events:
        print(f"\n[ノード更新の詳細]")
        for i, event in enumerate(update_events, 1):
            print(f"  {i}. ノード: {event['node']}")
            # 更新内容の一部を表示
            update_str = str(event['update'])
            if len(update_str) > 100:
                update_str = update_str[:100] + "..."
            print(f"     更新: {update_str}")
    
    if token_events:
        print(f"\n[トークンの詳細]")
        node_name = token_events[0]['node'] if token_events else "unknown"
        print(f"  ノード: {node_name}")
        print(f"  総トークン数: {len(token_events)}")
        # 最初の10トークンを表示
        if len(token_events) > 0:
            first_tokens = "".join([e['token'] for e in token_events[:10]])
            print(f"  最初の10トークン: {first_tokens}...")
    
    print("\n" + "=" * 80)
    print("【まとめ】")
    print("=" * 80)
    print("""
複数のモードを同時にストリームすることで、以下のことが可能になります：

1. updatesモード:
   - ノードの実行タイミングを把握
   - ノードがどのような状態更新を行ったかを確認
   - グラフの実行フローを追跡

2. messagesモード:
   - LLMの出力をトークン単位でリアルタイムに取得
   - ユーザーに即座にフィードバックを提供
   - チャットUIなどでの表示に適している

3. 組み合わせの利点:
   - ノードの実行状況とLLMの出力を同時に監視
   - デバッグ時に詳細な情報を取得
   - より柔軟なデータ処理が可能
    """)
    print("=" * 80)
    print("\nストリーミング完了")


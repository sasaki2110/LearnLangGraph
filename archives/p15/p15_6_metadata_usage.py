"""
メタデータの活用例

このスクリプトは、LLMトークンストリーミングにおけるメタデータの活用方法を示します。
メタデータには、ノード名やLLM呼び出し情報などが含まれ、これらを活用することで
より高度なストリーミング処理が可能になります。
"""

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from typing import TypedDict, Annotated
import operator
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
print("モデル名：", MODEL_NAME)

llm = init_chat_model(
    MODEL_NAME,
    temperature=0
)


class State(TypedDict):
    messages: Annotated[list, operator.add]
    topic: str
    summary: str


def refine_topic_node(state: State):
    """トピックを精緻化するノード"""
    prompt = f"以下のトピックを、より面白く魅力的なトピックに精緻化してください。簡潔に1文で答えてください。\n\nトピック: {state.get('topic', '')}"
    
    messages = [
        SystemMessage(content="あなたはトピックを面白く精緻化する専門家です。"),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    refined_topic = response.content.strip()
    
    return {"topic": refined_topic}


def generate_summary_node(state: State):
    """要約を生成するノード"""
    prompt = f"以下のトピックについて、短い要約を生成してください。\n\nトピック: {state.get('topic', '')}"
    
    messages = [
        SystemMessage(content="あなたは要約を生成する専門家です。"),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    summary = response.content.strip()
    
    return {"summary": summary}


# グラフの構築（複数のLLMノードを含む）
graph = (
    StateGraph(State)
    .add_node("refine_topic", refine_topic_node)
    .add_node("generate_summary", generate_summary_node)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_summary")
    .add_edge("generate_summary", END)
    .compile()
)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("【例1】メタデータが全トークンで同じかどうかを確認")
    print("=" * 80)
    print("\n各トークンのメタデータを確認して、同じ内容が設定されているか確認します。\n")
    print("-" * 80)
    
    print("\n[ユーザー] プログラミングについて教えてください。\n")
    print("[AI] ", end="", flush=True)
    
    metadata_samples = []
    token_count = 0
    
    for token, metadata in graph.stream(
        {"messages": [], "topic": "プログラミング", "summary": ""},
        stream_mode="messages",
    ):
        token_text = token.content if hasattr(token, 'content') else str(token)
        print(token_text, end="", flush=True)
        token_count += 1
        
        # 最初、中間、最後のトークンでメタデータを記録
        if token_count == 1:
            metadata_samples.append(("最初のトークン", metadata.copy()))
        elif token_count == 10:
            metadata_samples.append(("10番目のトークン", metadata.copy()))
        elif token_count % 20 == 0:  # 20トークンごと
            metadata_samples.append((f"{token_count}番目のトークン", metadata.copy()))
    
    print("\n\n[メタデータの比較]")
    print("-" * 80)
    for label, meta in metadata_samples:
        print(f"\n{label}:")
        print(f"  ノード名: {meta.get('langgraph_node', 'N/A')}")
        print(f"  メタデータキー: {list(meta.keys())}")
    
    print("\n" + "=" * 80)
    print("【例2】ノード名でフィルタリング（どのノードからのトークンかを表示）")
    print("=" * 80)
    print("\n複数のノードがある場合、どのノードからのトークンかを表示します。\n")
    print("-" * 80)
    
    print("\n[処理開始]\n")
    
    for token, metadata in graph.stream(
        {"messages": [], "topic": "AI", "summary": ""},
        stream_mode="messages",
    ):
        token_text = token.content if hasattr(token, 'content') else str(token)
        node_name = metadata.get("langgraph_node", "unknown")
        
        # ノード名を表示（最初のトークンのみ）
        if token_text and not token_text.isspace():
            print(f"[{node_name}] ", end="", flush=True)
            print(token_text, end="", flush=True)
    
    print("\n\n" + "=" * 80)
    print("【例3】ノードごとにトークンを集計")
    print("=" * 80)
    print("\n各ノードから生成されたトークン数を集計します。\n")
    print("-" * 80)
    
    print("\n[処理開始]\n")
    
    node_token_counts = defaultdict(int)
    node_texts = defaultdict(str)
    
    for token, metadata in graph.stream(
        {"messages": [], "topic": "機械学習", "summary": ""},
        stream_mode="messages",
    ):
        token_text = token.content if hasattr(token, 'content') else str(token)
        node_name = metadata.get("langgraph_node", "unknown")
        
        node_token_counts[node_name] += 1
        node_texts[node_name] += token_text
        
        # トークンを表示
        print(token_text, end="", flush=True)
    
    print("\n\n[集計結果]")
    print("-" * 80)
    for node_name, count in node_token_counts.items():
        text_preview = node_texts[node_name][:50] + "..." if len(node_texts[node_name]) > 50 else node_texts[node_name]
        print(f"\nノード: {node_name}")
        print(f"  トークン数: {count}")
        print(f"  テキスト（一部）: {text_preview}")
    
    print("\n" + "=" * 80)
    print("【例4】特定のノードからのトークンのみを処理")
    print("=" * 80)
    print("\n特定のノード（例: generate_summary）からのトークンのみを表示します。\n")
    print("-" * 80)
    
    print("\n[処理開始]")
    print("（refine_topicノードのトークンは表示しません）\n")
    print("[generate_summary] ", end="", flush=True)
    
    target_node = "generate_summary"
    
    for token, metadata in graph.stream(
        {"messages": [], "topic": "Python", "summary": ""},
        stream_mode="messages",
    ):
        node_name = metadata.get("langgraph_node", "unknown")
        
        # 特定のノードからのトークンのみを処理
        if node_name == target_node:
            token_text = token.content if hasattr(token, 'content') else str(token)
            print(token_text, end="", flush=True)
        # 他のノードからのトークンは無視
    
    print("\n\n" + "=" * 80)
    print("【例5】メタデータの詳細情報を活用")
    print("=" * 80)
    print("\nメタデータに含まれる詳細情報（LLM呼び出し情報など）を活用します。\n")
    print("-" * 80)
    
    print("\n[ユーザー] 短い説明を書いてください。\n")
    print("[AI] ", end="", flush=True)
    
    first_token_metadata = None
    
    for token, metadata in graph.stream(
        {"messages": [], "topic": "データサイエンス", "summary": ""},
        stream_mode="messages",
    ):
        token_text = token.content if hasattr(token, 'content') else str(token)
        print(token_text, end="", flush=True)
        
        # 最初のトークンでメタデータの詳細を記録
        if first_token_metadata is None:
            first_token_metadata = metadata
    
    print("\n\n[メタデータの詳細]")
    print("-" * 80)
    if first_token_metadata:
        print(f"利用可能なキー: {list(first_token_metadata.keys())}")
        for key, value in first_token_metadata.items():
            # 値が長すぎる場合は一部のみ表示
            if isinstance(value, dict):
                print(f"\n{key}:")
                for sub_key, sub_value in list(value.items())[:3]:  # 最初の3つだけ
                    print(f"  {sub_key}: {sub_value}")
                if len(value) > 3:
                    print(f"  ... (他 {len(value) - 3} 個のキー)")
            else:
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"{key}: {value_str}")
    
    print("\n" + "=" * 80)
    print("ストリーミング完了")
    print("=" * 80)


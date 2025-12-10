"""
values vs updates の違いを比較する例

このスクリプトは、stream_mode="values"と"updates"の違いを
実際の動作で示します。
"""

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from typing import TypedDict
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
    topic: str
    joke: str
    step_count: int


def refine_topic(state: State):
    """トピックを精緻化するノード（LLMを使用）"""
    prompt = f"以下のトピックを、より面白く魅力的なトピックに精緻化してください。簡潔に1文で答えてください。\n\nトピック: {state['topic']}"
    
    messages = [
        SystemMessage(content="あなたはトピックを面白く精緻化する専門家です。"),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    refined_topic = response.content.strip()
    
    return {
        "topic": refined_topic,
        "step_count": state.get("step_count", 0) + 1
    }


def generate_joke(state: State):
    """ジョークを生成するノード（LLMを使用）"""
    prompt = f"以下のトピックについて、面白いジョークを1つ生成してください。\n\nトピック: {state['topic']}"
    
    messages = [
        SystemMessage(content="あなたは面白いジョークを生成するコメディアンです。"),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    joke = response.content.strip()
    
    return {
        "joke": joke,
        "step_count": state.get("step_count", 0) + 1
    }


# グラフの構築
graph = (
    StateGraph(State)
    .add_node("refine_topic", refine_topic)
    .add_node("generate_joke", generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .add_edge("generate_joke", END)
    .compile()
)


if __name__ == "__main__":
    initial_state = {"topic": "アイスクリーム", "joke": "", "step_count": 0}
    
    print("\n" + "=" * 80)
    print("【比較1】stream_mode='updates' の動作")
    print("=" * 80)
    print("\n特徴: 各ノードで更新された部分のみが返される")
    print("形式: {ノード名: {更新されたフィールド: 値}}")
    print("\n" + "-" * 80)
    
    for chunk in graph.stream(initial_state, stream_mode="updates"):
        node_name = list(chunk.keys())[0]
        update = chunk[node_name]
        print(f"\n[ノード: {node_name}]")
        print(f"  更新内容: {update}")
        print(f"  → このノードで変更されたフィールドのみが表示される")
    
    print("\n" + "=" * 80)
    print("【比較2】stream_mode='values' の動作")
    print("=" * 80)
    print("\n特徴: 各ステップ後の完全な状態全体が返される")
    print("形式: {全フィールド: 値} (状態の完全なスナップショット)")
    print("\n" + "-" * 80)
    
    for chunk in graph.stream(initial_state, stream_mode="values"):
        print(f"\n[ステップ後の完全な状態]")
        for key, value in chunk.items():
            if key == "joke" and value:
                # ジョークが長い場合は一部のみ表示
                display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"  {key}: {display_value}")
            else:
                print(f"  {key}: {value}")
        print(f"  → 状態の全フィールドが表示される（更新されていないものも含む）")
    
    print("\n" + "=" * 80)
    print("【主な違いのまとめ】")
    print("=" * 80)
    print("""
1. updates モード:
   - 返されるデータ: 更新された部分のみ（差分）
   - メモリ効率: 良い（差分のみ）
   - 使用例: どのノードが何を変更したかを追跡したい場合
   - 出力例: {'refine_topic': {'topic': '...', 'step_count': 1}}

2. values モード:
   - 返されるデータ: 完全な状態全体（スナップショット）
   - メモリ効率: やや悪い（全状態を毎回送信）
   - 使用例: 各ステップでの状態全体を確認したい場合、状態の履歴を保存したい場合
   - 出力例: {'topic': '...', 'joke': '', 'step_count': 1}

【いつ values を使うべきか？】
- 状態の完全なスナップショットが必要な場合
- 状態の履歴を保存・ログに記録したい場合
- デバッグ時に全状態を確認したい場合
- 状態の復元やロールバックが必要な場合

【いつ updates を使うべきか？】
- 通常のストリーミング表示（変更点のみ表示）
- メモリ効率を重視する場合
- リアルタイムで変更を追跡したい場合
- ほとんどの一般的な用途

結論: 特別な理由がない限り、updates を使うのが推奨されます。
    """)
    print("=" * 80)


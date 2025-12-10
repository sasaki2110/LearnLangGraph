"""
同期ストリーミング vs 非同期ストリーミングの比較

このスクリプトは、同期と非同期の違いと使い分けを示します。
"""

import asyncio
import time
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


def refine_topic(state: State):
    """トピックを精緻化するノード（LLMを使用）"""
    prompt = f"以下のトピックを、より面白く魅力的なトピックに精緻化してください。簡潔に1文で答えてください。\n\nトピック: {state['topic']}"
    
    messages = [
        SystemMessage(content="あなたはトピックを面白く精緻化する専門家です。"),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    refined_topic = response.content.strip()
    
    return {"topic": refined_topic}


def generate_joke(state: State):
    """ジョークを生成するノード（LLMを使用）"""
    prompt = f"以下のトピックについて、面白いジョークを1つ生成してください。\n\nトピック: {state['topic']}"
    
    messages = [
        SystemMessage(content="あなたは面白いジョークを生成するコメディアンです。"),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    joke = response.content.strip()
    
    return {"joke": joke}


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


def sync_streaming_example():
    """同期ストリーミングの例"""
    print("\n" + "=" * 80)
    print("【同期ストリーミング】")
    print("=" * 80)
    
    start_time = time.time()
    
    for chunk in graph.stream(
        {"topic": "プログラミング"},
        stream_mode="updates",
    ):
        node_name = list(chunk.keys())[0]
        update = chunk[node_name]
        print(f"[ノード: {node_name}] {list(update.keys())[0]}: {str(list(update.values())[0])[:50]}...")
    
    elapsed = time.time() - start_time
    print(f"\n実行時間: {elapsed:.2f}秒")


async def async_streaming_example():
    """非同期ストリーミングの例（単一タスク）"""
    print("\n" + "=" * 80)
    print("【非同期ストリーミング（単一タスク）】")
    print("=" * 80)
    
    start_time = time.time()
    
    async for chunk in graph.astream(
        {"topic": "プログラミング"},
        stream_mode="updates",
    ):
        node_name = list(chunk.keys())[0]
        update = chunk[node_name]
        print(f"[ノード: {node_name}] {list(update.keys())[0]}: {str(list(update.values())[0])[:50]}...")
    
    elapsed = time.time() - start_time
    print(f"\n実行時間: {elapsed:.2f}秒")


async def async_parallel_example():
    """非同期ストリーミングの例（複数タスクを並列実行）"""
    print("\n" + "=" * 80)
    print("【非同期ストリーミング（複数タスクを並列実行）】")
    print("=" * 80)
    print("3つの異なるトピックを同時に処理します...")
    
    async def process_topic(topic: str, task_id: int):
        """1つのトピックを処理する非同期関数"""
        print(f"\n[タスク {task_id}] 開始: {topic}")
        async for chunk in graph.astream(
            {"topic": topic},
            stream_mode="updates",
        ):
            node_name = list(chunk.keys())[0]
            update = chunk[node_name]
            print(f"[タスク {task_id} - {node_name}] 完了")
        print(f"[タスク {task_id}] 完了: {topic}")
    
    start_time = time.time()
    
    # 3つのタスクを並列実行
    await asyncio.gather(
        process_topic("プログラミング", 1),
        process_topic("料理", 2),
        process_topic("旅行", 3),
    )
    
    elapsed = time.time() - start_time
    print(f"\n全タスクの実行時間: {elapsed:.2f}秒")
    print("（並列実行により、個別に実行するより大幅に短縮されます）")


def sync_sequential_example():
    """同期ストリーミングの例（複数タスクを順次実行）"""
    print("\n" + "=" * 80)
    print("【同期ストリーミング（複数タスクを順次実行）】")
    print("=" * 80)
    print("3つの異なるトピックを順番に処理します...")
    
    topics = ["プログラミング", "料理", "旅行"]
    start_time = time.time()
    
    for i, topic in enumerate(topics, 1):
        print(f"\n[タスク {i}] 開始: {topic}")
        for chunk in graph.stream(
            {"topic": topic},
            stream_mode="updates",
        ):
            node_name = list(chunk.keys())[0]
            update = chunk[node_name]
            print(f"[タスク {i} - {node_name}] 完了")
        print(f"[タスク {i}] 完了: {topic}")
    
    elapsed = time.time() - start_time
    print(f"\n全タスクの実行時間: {elapsed:.2f}秒")
    print("（順次実行のため、各タスクの時間が合計されます）")


async def main():
    """メイン関数"""
    print("\n" + "=" * 80)
    print("同期 vs 非同期ストリーミングの比較")
    print("=" * 80)
    
    # 1. 同期ストリーミング（単一タスク）
    sync_streaming_example()
    
    # 2. 非同期ストリーミング（単一タスク）
    await async_streaming_example()
    
    # 3. 同期ストリーミング（複数タスクを順次実行）
    sync_sequential_example()
    
    # 4. 非同期ストリーミング（複数タスクを並列実行）
    await async_parallel_example()
    
    print("\n" + "=" * 80)
    print("【まとめ】")
    print("=" * 80)
    print("""
【同期ストリーミング (stream)】
- 単一タスクの処理に適している
- シンプルで理解しやすい
- 複数タスクは順次実行される（時間が合計される）
- スクリプトやCLIツールに適している

【非同期ストリーミング (astream)】
- 単一タスクでも使用可能（同期とほぼ同じ）
- 複数タスクを並列実行できる（asyncio.gather）
- Webアプリケーション（FastAPI、Flask等）との統合に必須
- I/O待機中に他の処理を実行できる

【使い分けの指針】
1. 単一タスクのスクリプト/CLIツール → 同期 (stream)
2. Webアプリケーション（FastAPI等） → 非同期 (astream)
3. 複数タスクを並列処理したい場合 → 非同期 (astream)
4. 既存の同期コードベース → 同期 (stream)

【推奨】
- 一般的なスクリプト: 同期 (stream) で十分
- Webアプリケーション: 非同期 (astream) を推奨
- パフォーマンスが重要な場合: 非同期 (astream) を検討
    """)


if __name__ == "__main__":
    asyncio.run(main())


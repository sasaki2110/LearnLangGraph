"""
カスタムデータのストリーミング: 進行状況の報告

このスクリプトは、LangGraphのカスタムデータストリーミング機能を実装しています。
get_stream_writer()を使用して、ノード内から進行状況をストリームします。

長時間処理の進捗状況をリアルタイムで報告する実践的な例です。
"""

from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
import time


class TaskState(TypedDict):
    task_id: str
    status: str
    items_processed: int
    total_items: int


def process_items(state: TaskState):
    """アイテムを処理し、進行状況をカスタムストリームで報告するノード"""
    writer = get_stream_writer()
    total = state["total_items"]
    
    for i in range(total):
        # アイテムの処理（シミュレーション）
        time.sleep(0.1)  # 処理のシミュレーション
        
        # 進行状況をストリーム
        if writer:
            progress = int((i + 1) / total * 100)
            writer({
                "progress": progress,
                "items_processed": i + 1,
                "status": f"Processing item {i + 1}/{total}"
            })
    
    return {
        "status": "completed",
        "items_processed": total
    }


# グラフの構築
graph = (
    StateGraph(TaskState)
    .add_node("process", process_items)
    .add_edge(START, "process")
    .add_edge("process", END)
    .compile()
)


if __name__ == "__main__":
    print("カスタムデータストリーミング: 進行状況の報告")
    print("=" * 60)
    print("\n[モード: custom] 処理の進行状況をリアルタイムでストリーム")
    print("-" * 60)
    
    # 進行状況を監視
    for chunk in graph.stream(
        {
            "task_id": "task_1",
            "status": "pending",
            "items_processed": 0,
            "total_items": 10
        },
        stream_mode="custom",
    ):
        progress = chunk.get("progress", 0)
        items_processed = chunk.get("items_processed", 0)
        status = chunk.get("status", "")
        print(f"[{progress:3d}%] {status} (処理済み: {items_processed}件)")
    
    print("\n" + "=" * 60)
    print("ストリーミング完了")
    
    # 最終状態を確認
    final_state = graph.invoke({
        "task_id": "task_1",
        "status": "pending",
        "items_processed": 0,
        "total_items": 10
    })
    print(f"\n最終状態:")
    print(f"  task_id: {final_state['task_id']}")
    print(f"  status: {final_state['status']}")
    print(f"  items_processed: {final_state['items_processed']}")
    print(f"  total_items: {final_state['total_items']}")


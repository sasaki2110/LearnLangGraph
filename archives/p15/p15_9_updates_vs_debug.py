"""
updates vs debug の違いを比較する例

このスクリプトは、stream_mode="updates"と"debug"の違いを
実際の動作で示します。

debugモードは、可能な限り多くの情報（ノード名、完全な状態、実行フローなど）
をストリームしますが、LLMトークンは含まれません。
"""

from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from typing import TypedDict
import os
import json
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


def format_debug_chunk(chunk):
    """debugモードのチャンクを読みやすくフォーマット"""
    if isinstance(chunk, dict):
        formatted = {}
        for key, value in chunk.items():
            if isinstance(value, dict):
                formatted[key] = format_debug_chunk(value)
            elif isinstance(value, str) and len(value) > 100:
                formatted[key] = value[:100] + "..."
            else:
                formatted[key] = value
        return formatted
    return chunk


if __name__ == "__main__":
    initial_state = {"topic": "アイスクリーム", "joke": "", "step_count": 0}
    
    print("\n" + "=" * 80)
    print("【比較1】stream_mode='updates' の動作")
    print("=" * 80)
    print("\n特徴: 各ノードで更新された部分のみが返される")
    print("形式: {ノード名: {更新されたフィールド: 値}}")
    print("メモリ効率: 良い（差分のみ）")
    print("\n" + "-" * 80)
    
    update_count = 0
    for chunk in graph.stream(initial_state, stream_mode="updates"):
        update_count += 1
        node_name = list(chunk.keys())[0]
        update = chunk[node_name]
        print(f"\n[更新 #{update_count}] ノード: {node_name}")
        for key, value in update.items():
            if isinstance(value, str) and len(value) > 80:
                display_value = value[:80] + "..."
                print(f"  {key}: {display_value}")
            else:
                print(f"  {key}: {value}")
        print(f"  → このノードで変更されたフィールドのみが表示される")
    
    print("\n" + "=" * 80)
    print("【比較2】stream_mode='debug' の動作")
    print("=" * 80)
    print("\n特徴: 可能な限り多くの情報（ノード名、完全な状態、実行フローなど）")
    print("形式: 詳細なデバッグ情報（構造は複雑）")
    print("メモリ効率: やや悪い（詳細情報が多い）")
    print("\n" + "-" * 80)
    
    debug_count = 0
    for chunk in graph.stream(initial_state, stream_mode="debug"):
        debug_count += 1
        
        # debugモードの構造: {step, timestamp, type, payload}
        if isinstance(chunk, dict):
            event_type = chunk.get("type", "unknown")
            step = chunk.get("step", "?")
            timestamp = chunk.get("timestamp", "")
            payload = chunk.get("payload", {})
            node_name = payload.get("name", "unknown")
            
            if event_type == "task":
                # ノードの実行開始
                print(f"\n[デバッグ情報 #{debug_count}] ノード実行開始")
                print(f"  ステップ: {step}")
                print(f"  ノード名: {node_name}")
                print(f"  タイムスタンプ: {timestamp}")
                input_data = payload.get("input", {})
                print(f"  入力データのキー: {list(input_data.keys())}")
                # 入力データの一部を表示
                for key, value in list(input_data.items())[:2]:
                    if isinstance(value, str) and len(value) > 60:
                        print(f"    {key}: {value[:60]}...")
                    else:
                        print(f"    {key}: {value}")
                if len(input_data) > 2:
                    print(f"    ... (他 {len(input_data) - 2} 個のキー)")
            
            elif event_type == "task_result":
                # ノードの実行結果
                print(f"\n[デバッグ情報 #{debug_count}] ノード実行完了")
                print(f"  ステップ: {step}")
                print(f"  ノード名: {node_name}")
                print(f"  タイムスタンプ: {timestamp}")
                result = payload.get("result", {})
                error = payload.get("error")
                
                if error:
                    print(f"  エラー: {error}")
                else:
                    if isinstance(result, dict):
                        print(f"  結果のキー: {list(result.keys())}")
                        # 結果の一部を表示
                        for key, value in list(result.items())[:2]:
                            if isinstance(value, str) and len(value) > 60:
                                print(f"    {key}: {value[:60]}...")
                            else:
                                print(f"    {key}: {value}")
                        if len(result) > 2:
                            print(f"    ... (他 {len(result) - 2} 個のキー)")
                    else:
                        print(f"  結果: {result}")
            
            else:
                # その他のイベントタイプ
                print(f"\n[デバッグ情報 #{debug_count}] イベントタイプ: {event_type}")
                print(f"  ステップ: {step}")
                print(f"  タイムスタンプ: {timestamp}")
                print(f"  ペイロードのキー: {list(payload.keys())}")
        
        print(f"  → 実行フローの詳細なトレース情報")
    
    print("\n" + "=" * 80)
    print("【主な違いのまとめ】")
    print("=" * 80)
    print("""
1. updates モード:
   - 返されるデータ: 更新された部分のみ（差分）
   - ノード名: 含まれる（どのノードが更新したか分かる）
   - メモリ効率: 良い
   - 使用例: 通常のストリーミング表示、変更点の追跡
   - 出力例: {'refine_topic': {'topic': '...', 'step_count': 1}}

2. debug モード:
   - 返されるデータ: 実行フローの詳細なトレース情報
   - 構造: {step, timestamp, type, payload}
   - イベントタイプ: 
     * "task": ノードの実行開始（入力データを含む）
     * "task_result": ノードの実行完了（結果データを含む）
   - 含まれる情報:
     * ステップ番号
     * タイムスタンプ（各イベントの実行時刻）
     * ノード名
     * 入力データ（taskイベント）
     * 結果データ（task_resultイベント）
     * エラー情報（エラーが発生した場合）
   - メモリ効率: やや悪い（詳細情報が多い）
   - 使用例: デバッグ、実行フローの詳細な追跡、問題の調査
   - LLMトークン: 含まれない（messagesモードが必要）
   - 出力例: 
     * task: {'step': 1, 'type': 'task', 'payload': {'name': 'refine_topic', 'input': {...}}}
     * task_result: {'step': 1, 'type': 'task_result', 'payload': {'name': 'refine_topic', 'result': {...}}}

【重要な注意点】
- debugモードは、updatesやvaluesと重複する情報を含む可能性がある
- debugモードとupdates/valuesを同時に指定するのは非推奨（重複する）
- LLMトークンも取得したい場合は、stream_mode=["debug", "messages"]を使用

【いつ updates を使うべきか？】
- 通常のストリーミング表示
- メモリ効率を重視する場合
- リアルタイムで変更を追跡したい場合
- ほとんどの一般的な用途

【いつ debug を使うべきか？】
- デバッグ時に詳細な情報が必要な場合
- 実行フローを詳細に追跡したい場合
- 問題の原因を調査したい場合
- 開発・テスト段階

結論: 通常は updates を使い、デバッグが必要な場合のみ debug を使用する。
    """)
    print("=" * 80)


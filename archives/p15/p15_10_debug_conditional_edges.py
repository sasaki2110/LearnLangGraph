"""
debugモードで条件付きエッジのtriggers情報を表示する例

このスクリプトは、debugモードを使用して条件付きエッジの判定結果を
可視化する方法を示します。

条件付きエッジの判定結果は、次のノードのtaskイベントのtriggersに
'branch:to:ノード名'という形式で含まれます。
"""

from typing_extensions import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
print("モデル名：", MODEL_NAME)

llm = init_chat_model(
    MODEL_NAME,
    temperature=0
)

# ルーティングロジックとして使用する構造化出力のスキーマ
class Route(BaseModel):
    step: Literal["poem", "story", "joke"] = Field(
        None, description="ルーティングプロセスの次のステップ"
    )

# 構造化出力スキーマでLLMを拡張
router = llm.with_structured_output(Route)

# 状態
class State(TypedDict):
    input: str
    decision: str
    output: str

# ノード
def llm_call_1(state: State):
    """ストーリーを書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_2(state: State):
    """ジョークを書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_3(state: State):
    """詩を書く"""
    result = llm.invoke(state["input"])
    return {"output": result.content}

def llm_call_router(state: State):
    """入力を適切なノードにルーティング"""
    # ルーティングロジックとして機能する構造化出力で拡張LLMを実行
    decision = router.invoke([
        SystemMessage(content="ユーザーのリクエストに基づいて、ストーリー、ジョーク、または詩にルーティングしてください。"),
        HumanMessage(content=state["input"]),
    ])
    return {"decision": decision.step}

# 適切なノードにルーティングする条件付きエッジ関数
def route_decision(state: State):
    # 次に訪問したいノード名を返す
    if state["decision"] == "story":
        return "llm_call_1"
    elif state["decision"] == "joke":
        return "llm_call_2"
    elif state["decision"] == "poem":
        return "llm_call_3"

# ワークフローの構築
router_builder = StateGraph(State)
router_builder.add_node("llm_call_1", llm_call_1)
router_builder.add_node("llm_call_2", llm_call_2)
router_builder.add_node("llm_call_3", llm_call_3)
router_builder.add_node("llm_call_router", llm_call_router)

# ノードを接続するエッジを追加
router_builder.add_edge(START, "llm_call_router")
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {  # route_decisionが返す名前: 次に訪問するノード名
        "llm_call_1": "llm_call_1",
        "llm_call_2": "llm_call_2",
        "llm_call_3": "llm_call_3",
    },
)
router_builder.add_edge("llm_call_1", END)
router_builder.add_edge("llm_call_2", END)
router_builder.add_edge("llm_call_3", END)

# ワークフローをコンパイル
router_workflow = router_builder.compile()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("【debugモードで条件付きエッジのtriggers情報を表示】")
    print("=" * 80)
    print("\n条件付きエッジの判定結果は、次のノードのtaskイベントの")
    print("triggersに'branch:to:ノード名'という形式で含まれます。")
    print("\n" + "-" * 80)
    
    # テストケース1: ストーリーを生成
    print("\n[テストケース1] ストーリーを生成")
    print("入力: '飴ちゃんを主題にしたストーリー'")
    print("-" * 80)
    
    for chunk in router_workflow.stream(
        {"input": "飴ちゃんを主題にしたストーリー", "decision": "", "output": ""},
        stream_mode="debug"
    ):
        event_type = chunk.get("type")
        step = chunk.get("step")
        payload = chunk.get("payload", {})
        node_name = payload.get("name", "")
        
        if event_type == "task":
            print(f"\n[ステップ {step}] ノード '{node_name}' の実行開始")
            triggers = payload.get("triggers", [])
            if triggers:
                print(f"  Triggers: {triggers}")
                # 条件付きエッジの判定結果を抽出
                for trigger in triggers:
                    if "branch:to:" in str(trigger):
                        next_node = str(trigger).split("branch:to:")[-1].rstrip("'")
                        print(f"  → 条件付きエッジの判定結果: '{next_node}' に遷移")
        
        elif event_type == "task_result":
            print(f"[ステップ {step}] ノード '{node_name}' の実行完了")
            result = payload.get("result", {})
            if "decision" in result:
                print(f"  判定結果: {result['decision']}")
            if "output" in result:
                output_preview = result["output"][:100] + "..." if len(result["output"]) > 100 else result["output"]
                print(f"  出力: {output_preview}")
    
    print("\n" + "=" * 80)
    print("[テストケース2] ジョークを生成")
    print("入力: 'プログラミングについて面白いジョーク'")
    print("-" * 80)
    
    for chunk in router_workflow.stream(
        {"input": "プログラミングについて面白いジョーク", "decision": "", "output": ""},
        stream_mode="debug"
    ):
        event_type = chunk.get("type")
        step = chunk.get("step")
        payload = chunk.get("payload", {})
        node_name = payload.get("name", "")
        
        if event_type == "task":
            print(f"\n[ステップ {step}] ノード '{node_name}' の実行開始")
            triggers = payload.get("triggers", [])
            if triggers:
                print(f"  Triggers: {triggers}")
                for trigger in triggers:
                    if "branch:to:" in str(trigger):
                        next_node = str(trigger).split("branch:to:")[-1].rstrip("'")
                        print(f"  → 条件付きエッジの判定結果: '{next_node}' に遷移")
        
        elif event_type == "task_result":
            print(f"[ステップ {step}] ノード '{node_name}' の実行完了")
            result = payload.get("result", {})
            if "decision" in result:
                print(f"  判定結果: {result['decision']}")
            if "output" in result:
                output_preview = result["output"][:100] + "..." if len(result["output"]) > 100 else result["output"]
                print(f"  出力: {output_preview}")
    
    print("\n" + "=" * 80)
    print("【まとめ】")
    print("=" * 80)
    print("""
debugモードを使用することで、条件付きエッジの判定結果を可視化できます：

1. 条件判定のタイミング:
   - llm_call_routerノードの実行完了後、route_decision関数が呼ばれる
   - 判定結果に基づいて、次のノードが決定される

2. triggers情報の取得:
   - 次のノードのtaskイベントのtriggersに'branch:to:ノード名'が含まれる
   - これにより、実際にどのノードに遷移したかが分かる

3. デバッグの利点:
   - 条件判定の結果を確認できる
   - 実行フローを詳細に追跡できる
   - 問題の原因を特定しやすい

注意: 条件判定関数の戻り値（例: 'llm_call_1'）そのものは直接取得できませんが、
      実際に遷移したノードはtriggersから分かります。
    """)
    print("=" * 80)


from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class WorkflowState(TypedDict):
    data: list
    processed_data: list
    result: str

# 処理用モック　データ抽出
def fetch_data() -> list:
    return [1, 2, 3]

# 処理用モック　データ変換
def process(item: int) -> int:
    return item * 2

# 処理用モック　データ保存
def save_data(data: list) -> str:
    return str(data)

# データ抽出ノード
def extract(state: WorkflowState) -> dict:
    """データ抽出"""
    # データを抽出
    data = fetch_data()
    return {"data": data}

# データ変換ノード
def transform(state: WorkflowState) -> dict:
    """データ変換"""
    # データを変換
    processed = [process(item) for item in state["data"]]
    return {"processed_data": processed}

# データ保存ノード
def load(state: WorkflowState) -> dict:
    """データロード"""
    # データをロード
    result = save_data(state["processed_data"])
    return {"result": result}

# ワークフローの構築
workflow = StateGraph(WorkflowState)
workflow.add_node("extract", extract)
workflow.add_node("transform", transform)
workflow.add_node("load", load)

# 固定されたフロー
workflow.add_edge(START, "extract")
workflow.add_edge("extract", "transform")
workflow.add_edge("transform", "load")
workflow.add_edge("load", END)

compiled_workflow = workflow.compile()

print("ワークフローの実行")
workflow_result = compiled_workflow.invoke({"data": [1, 2, 3], "processed_data": [], "result": ""})
print("ワークフローの実行結果:")
print(workflow_result)
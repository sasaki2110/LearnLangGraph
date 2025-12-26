"""
ノード関数の実装
"""
import requests
import random
from langgraph.func import task
from langgraph.types import interrupt
from my_agent.utils.state import State


@task
def _make_request(url: str) -> str:
    """リクエストを行うタスク（副作用を持つ操作）"""
    return requests.get(url).text[:100]


@task
def _generate_random_id() -> str:
    """ランダムIDを生成するタスク（非決定的な操作）"""
    return f"id_{random.randint(1000, 9999)}"


@task
def _process_data(data: str) -> str:
    """データを処理するタスク（例：外部サービスへの書き込みなど）"""
    # 実際の実装では、データベースへの書き込みや外部API呼び出しなど
    return f"Processed: {data[:50]}"


@task
def task_1() -> str:
    """タスク1（テスト用）"""
    return "task_1_result"


@task
def task_2() -> str:
    """タスク2（テスト用）"""
    return "task_2_result"


@task
def task_3() -> str:
    """タスク3（テスト用）"""
    return "task_3_result"


def call_api(state: State) -> dict:
    """APIリクエストを行うノードの例
    
    このノードの先頭で中断し、ユーザーの承認を求める。
    承認後、同じ処理（_make_request）を複数回実行します。
    """
    # 中断してユーザーの承認を求める
    # 再開時、interrupt()の戻り値として承認結果が返される
    user_response = interrupt({
        "message": "API呼び出しを実行しますか？ (y/n)",
        "urls": state['urls']
    })
    
    # ユーザーの応答を確認
    # user_responseは文字列（"y", "yes"など）または辞書（{"approved": True}など）の可能性がある
    approved = False
    if isinstance(user_response, dict):
        approved = user_response.get("approved", False)
    elif isinstance(user_response, str):
        # 文字列の場合は "y" や "yes" を承認として扱う
        approved = user_response.lower() in ["y", "yes", "true", "1"]
    elif isinstance(user_response, bool):
        approved = user_response
    
    # 承認されなかった場合は空の結果を返す
    if not approved:
        return {"results": []}
    
    # 同じ処理を複数回実行する例
    tasks = [_make_request(url) for url in state['urls']]
    results = [task.result() for task in tasks]
    return {
        "results": results
    }


def process_with_different_tasks(state: State) -> dict:
    """異なる処理をタスクとして並べる例
    
    この例では、以下の異なるタスクを組み合わせています：
    1. API呼び出し（副作用を持つ操作）
    2. ランダムID生成（非決定的な操作）
    3. データ処理（副作用を持つ操作）
    
    各タスクは独立して実行され、再実行時には永続化レイヤーから
    結果が取得されるため、一貫性が保証されます。
    """
    # 異なる処理をタスクとして並べる
    url_task = _make_request(state['urls'][0]) if state['urls'] else None
    id_task = _generate_random_id()
    process_task = _process_data("sample data")
    
    # 各タスクの結果を取得
    results = {}
    if url_task:
        results['url_result'] = url_task.result()
    results['random_id'] = id_task.result()
    results['processed'] = process_task.result()
    
    return results


def node_with_multiple_tasks_and_interrupt(state: State) -> dict:
    """複数のタスクを実行し、途中で中断する例
    
    このノードは、task_1, task_2, task_3を順番に実行しますが、
    task_2の後に中断が発生します。
    
    再開時、task_1とtask_2は再実行されず、永続化された結果が使用されます。
    task_3のみが新しく実行されます。
    """
    # task_1を実行（結果は永続化される）
    t1 = task_1()
    result1 = t1.result()
    
    # task_2を実行（結果は永続化される）
    t2 = task_2()
    result2 = t2.result()
    
    # ここで中断（task_1とtask_2の結果は既に永続化されている）
    user_response = interrupt({
        "message": "task_1とtask_2が完了しました。続行しますか？ (y/n)",
        "task_1_result": result1,
        "task_2_result": result2
    })
    
    # ユーザーの応答を確認
    approved = False
    if isinstance(user_response, dict):
        approved = user_response.get("approved", False)
    elif isinstance(user_response, str):
        approved = user_response.lower() in ["y", "yes", "true", "1"]
    elif isinstance(user_response, bool):
        approved = user_response
    
    if not approved:
        return {
            "task_1_result": result1,
            "task_2_result": result2,
            "task_3_result": None
        }
    
    # task_3を実行（再開時、task_1とtask_2は再実行されず、永続化された結果が使用される）
    t3 = task_3()
    result3 = t3.result()
    
    return {
        "task_1_result": result1,
        "task_2_result": result2,
        "task_3_result": result3
    }

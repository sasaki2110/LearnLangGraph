"""
ノード関数の実装
"""
import requests
import random
from langgraph.func import task
from langgraph.types import interrupt
from langgraph.errors import GraphInterrupt
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


@task
def _make_request(url: str) -> str:
    """リクエストを行うタスク（副作用を持つ操作）"""
    logger.info(f"🌐 [TASK] APIリクエストを実行します: {url}")
    try:
        result = requests.get(url).text[:100]
        logger.info(f"✅ [TASK] APIリクエストが完了しました: {url[:50]}...")
        return result
    except Exception as e:
        logger.error(f"❌ [TASK] APIリクエスト中にエラーが発生しました: {url} - {e}", exc_info=True)
        raise


@task
def _generate_random_id() -> str:
    """ランダムIDを生成するタスク（非決定的な操作）"""
    logger.debug("🎲 [TASK] ランダムIDを生成します")
    try:
        result = f"id_{random.randint(1000, 9999)}"
        logger.debug(f"✅ [TASK] ランダムIDが生成されました: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [TASK] ランダムID生成中にエラーが発生しました: {e}", exc_info=True)
        raise


@task
def _process_data(data: str) -> str:
    """データを処理するタスク（例：外部サービスへの書き込みなど）"""
    logger.debug(f"⚙️ [TASK] データを処理します: {data[:50]}...")
    try:
        result = f"Processed: {data[:50]}"
        logger.debug(f"✅ [TASK] データ処理が完了しました")
        return result
    except Exception as e:
        logger.error(f"❌ [TASK] データ処理中にエラーが発生しました: {e}", exc_info=True)
        raise


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
    logger.info("🌐 [NODE] call_api ノードの実行を開始します")
    logger.debug(f"📊 [NODE] 状態: URLs数={len(state.get('urls', []))}")
    
    try:
        # 中断してユーザーの承認を求める
        # 再開時、interrupt()の戻り値として承認結果が返される
        logger.info("⏸️ [NODE] ユーザーの承認を待機します")
        user_response = interrupt({
            "message": "API呼び出しを実行しますか？ (y/n)",
            "urls": state['urls']
        })
        
        logger.info(f"👤 [NODE] ユーザーの応答を受信しました: {type(user_response).__name__}")
        
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
            logger.warning("⚠️ [NODE] ユーザーが承認しませんでした。空の結果を返します")
            return {"results": []}
        
        logger.info(f"✅ [NODE] 承認されました。{len(state['urls'])}個のURLに対してAPIリクエストを実行します")
        
        # 同じ処理を複数回実行する例
        tasks = [_make_request(url) for url in state['urls']]
        logger.debug(f"🔧 [NODE] {len(tasks)}個のタスクを作成しました")
        
        results = [task.result() for task in tasks]
        logger.info(f"✅ [NODE] call_api ノードの実行が完了しました ({len(results)}個の結果)")
        
        return {
            "results": results
        }
    except GraphInterrupt:
        # GraphInterruptは正常な中断処理なので、エラーとして扱わない
        logger.debug("⏸️ [NODE] グラフが中断されました（正常な動作）")
        raise
    except Exception as e:
        logger.error(f"❌ [NODE] call_api ノードの実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def process_with_different_tasks(state: State) -> dict:
    """異なる処理をタスクとして並べる例
    
    この例では、以下の異なるタスクを組み合わせています：
    1. API呼び出し（副作用を持つ操作）
    2. ランダムID生成（非決定的な操作）
    3. データ処理（副作用を持つ操作）
    
    各タスクは独立して実行され、再実行時には永続化レイヤーから
    結果が取得されるため、一貫性が保証されます。
    """
    logger.info("⚙️ [NODE] process_with_different_tasks ノードの実行を開始します")
    logger.debug(f"📊 [NODE] 状態: URLs数={len(state.get('urls', []))}")
    
    try:
        # 異なる処理をタスクとして並べる
        logger.debug("🔧 [NODE] 複数のタスクを作成します")
        url_task = _make_request(state['urls'][0]) if state['urls'] else None
        id_task = _generate_random_id()
        process_task = _process_data("sample data")
        
        logger.debug(f"📋 [NODE] タスク作成完了: URLタスク={'あり' if url_task else 'なし'}, IDタスク=あり, 処理タスク=あり")
        
        # 各タスクの結果を取得
        results = {}
        if url_task:
            logger.debug("🌐 [NODE] URLタスクの結果を取得します")
            results['url_result'] = url_task.result()
        logger.debug("🎲 [NODE] ランダムIDタスクの結果を取得します")
        results['random_id'] = id_task.result()
        logger.debug("⚙️ [NODE] データ処理タスクの結果を取得します")
        results['processed'] = process_task.result()
        
        logger.info(f"✅ [NODE] process_with_different_tasks ノードの実行が完了しました ({len(results)}個の結果)")
        return results
    except Exception as e:
        logger.error(f"❌ [NODE] process_with_different_tasks ノードの実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def node_with_multiple_tasks_and_interrupt(state: State) -> dict:
    """複数のタスクを実行し、途中で中断する例
    
    このノードは、task_1, task_2, task_3を順番に実行しますが、
    task_2の後に中断が発生します。
    
    再開時、task_1とtask_2は再実行されず、永続化された結果が使用されます。
    task_3のみが新しく実行されます。
    """
    logger.info("🔄 [NODE] node_with_multiple_tasks_and_interrupt ノードの実行を開始します")
    
    try:
        # task_1を実行（結果は永続化される）
        logger.info("📝 [NODE] task_1を実行します")
        t1 = task_1()
        result1 = t1.result()
        logger.info(f"✅ [NODE] task_1が完了しました: {result1}")
        
        # task_2を実行（結果は永続化される）
        logger.info("📝 [NODE] task_2を実行します")
        t2 = task_2()
        result2 = t2.result()
        logger.info(f"✅ [NODE] task_2が完了しました: {result2}")
        
        # ここで中断（task_1とtask_2の結果は既に永続化されている）
        logger.info("⏸️ [NODE] 中断してユーザーの承認を待機します")
        user_response = interrupt({
            "message": "task_1とtask_2が完了しました。続行しますか？ (y/n)",
            "task_1_result": result1,
            "task_2_result": result2
        })
        
        logger.info(f"👤 [NODE] ユーザーの応答を受信しました: {type(user_response).__name__}")
        
        # ユーザーの応答を確認
        approved = False
        if isinstance(user_response, dict):
            approved = user_response.get("approved", False)
        elif isinstance(user_response, str):
            approved = user_response.lower() in ["y", "yes", "true", "1"]
        elif isinstance(user_response, bool):
            approved = user_response
        
        if not approved:
            logger.warning("⚠️ [NODE] ユーザーが続行を承認しませんでした")
            return {
                "task_1_result": result1,
                "task_2_result": result2,
                "task_3_result": None
            }
        
        # task_3を実行（再開時、task_1とtask_2は再実行されず、永続化された結果が使用される）
        logger.info("📝 [NODE] task_3を実行します")
        t3 = task_3()
        result3 = t3.result()
        logger.info(f"✅ [NODE] task_3が完了しました: {result3}")
        
        logger.info("✅ [NODE] node_with_multiple_tasks_and_interrupt ノードの実行が完了しました")
        return {
            "task_1_result": result1,
            "task_2_result": result2,
            "task_3_result": result3
        }
    except GraphInterrupt:
        # GraphInterruptは正常な中断処理なので、エラーとして扱わない
        logger.debug("⏸️ [NODE] グラフが中断されました（正常な動作）")
        raise
    except Exception as e:
        logger.error(f"❌ [NODE] node_with_multiple_tasks_and_interrupt ノードの実行中にエラーが発生しました: {e}", exc_info=True)
        raise

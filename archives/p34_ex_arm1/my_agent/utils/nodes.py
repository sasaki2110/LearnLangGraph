"""
ノード関数の実装
"""
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from my_agent.utils.state import State, Task, TaskList
from my_agent.utils.logging_config import get_logger
from my_agent.utils.tools import get_object_position, move_arm_to, control_gripper
from typing import Dict, Any, List
import json

# ロガーを取得
logger = get_logger('nodes')


def extractor(state: State) -> Dict[str, Any]:
    """
    ユーザーメッセージから指示を取得するノード
    
    Args:
        state: 現在の状態
        
    Returns:
        更新された状態
    """
    logger.info("📝 [EXTRACTOR] ユーザー指示の抽出を開始します")
    
    try:
        # メッセージが存在する場合、最後のユーザーメッセージから指示を抽出
        if state.get("messages") and len(state["messages"]) > 0:
            last_message = state["messages"][-1]
            if hasattr(last_message, "content"):
                instruction = last_message.content.strip()
            else:
                instruction = str(last_message).strip()
            logger.info(f"✅ [EXTRACTOR] 指示を抽出しました: {instruction[:100]}...")
        else:
            instruction = state.get("instruction", "")
            logger.warning(f"⚠️ [EXTRACTOR] メッセージが見つかりません。既存の指示を使用: {instruction}")
        
        return {"instruction": instruction}
    except Exception as e:
        logger.error(f"❌ [EXTRACTOR] 指示抽出中にエラーが発生しました: {e}", exc_info=True)
        raise


def planner(state: State, llm) -> Dict[str, Any]:
    """
    ユーザーの指示を受け取り、全体のタスクリストを生成するノード（LLM使用）
    
    Args:
        state: 現在の状態
        llm: LLMインスタンス
        
    Returns:
        更新された状態（タスクリストを含む）
    """
    logger.info("🧠 [PLANNER] タスクリストの生成を開始します")
    
    try:
        instruction = state.get("instruction", "")
        if not instruction:
            logger.error("❌ [PLANNER] 指示が設定されていません")
            raise ValueError("指示が設定されていません")
        
        logger.info(f"📝 [PLANNER] 指示: {instruction[:100]}...")
        
        # 構造化出力スキーマでLLMを拡張
        # methodを指定しない場合、OpenAIは自動的に最適な方法を選択します
        # dict型のargsフィールドがあるため、json_schemaメソッドが使用される可能性があります
        planner_llm = llm.with_structured_output(TaskList)
        
        # LLMにタスクリストの生成を依頼
        system_prompt = """あなたはロボットアームの動作を計画する専門家です。
ユーザーの指示に基づいて、タスクを完了するために必要なすべてのステップを分解し、タスクリストを生成してください。

利用可能なツール:
1. get_object_position(item_name): 指定した物体の3次元座標を返す
   - 引数: {"item_name": "物体名"}
   - **重要**: 物体名は日本語で指定してください（例: "赤いコップ", "青いトレイ"）
2. move_arm_to(x, y, z): アームの先端（グリッパー）を指定座標へ移動させる
   - 引数: {"x": float, "y": float, "z": float}
   - または: {"item_name": "物体名"} （get_object_positionで取得済みの物体名を指定）
3. control_gripper(action): グリッパーの開閉を行う
   - 引数: {"action": "open" または "close"}

タスクの依存関係を考慮してください。例えば：
- 物体の位置を取得する前に、その位置に移動することはできません
- 物体を掴む前に、その位置に移動する必要があります
- 物体を置く前に、その物体を掴んでいる必要があります

**重要**: get_object_positionのitem_name引数には、必ず日本語の物体名を使用してください。
例: "赤いコップ", "青いトレイ", "ボール", "箱"

各タスクには以下を含めてください：
- id: 一意な識別子（例: 'task_1', 'task_2'）
- tool: 実行するツール名
- args: ツールの引数（**JSON文字列形式**、例: '{"item_name": "赤いコップ"}' または '{"x": 10.0, "y": 20.0, "z": 5.0}'）
  **重要**: argsは必ずJSON文字列として返してください。item_nameは日本語で指定してください。
- dependencies: 依存するタスクのIDリスト（このタスクを実行する前に完了する必要があるタスク）
- description: タスクの説明"""
        
        user_prompt = f"ユーザーの指示: {instruction}\n\nこの指示を完了するために必要なすべてのタスクを生成してください。"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        logger.debug("🤖 [PLANNER] LLMを呼び出しています...")
        task_list_result = planner_llm.invoke(messages)
        
        logger.info(f"✅ [PLANNER] タスクリストが生成されました: {len(task_list_result.tasks)}個のタスク")
        for i, task in enumerate(task_list_result.tasks, 1):
            logger.info(f"  {i}. {task.id}: {task.description} (依存: {task.dependencies})")
        
        return {
            "task_list": task_list_result.tasks,
            "object_positions": {},  # 初期化
            "completed_tasks": []  # 初期化
        }
    except Exception as e:
        logger.error(f"❌ [PLANNER] タスクリスト生成中にエラーが発生しました: {e}", exc_info=True)
        raise


def task_selector(state: State) -> Dict[str, Any]:
    """
    依存関係が満たされた次のタスクを選択するノード
    
    Args:
        state: 現在の状態
        
    Returns:
        更新された状態（current_task_idを含む）
    """
    logger.info("🎯 [TASK_SELECTOR] 次のタスクを選択します")
    
    try:
        task_list = state.get("task_list", [])
        completed_tasks = state.get("completed_tasks", [])
        
        if not task_list:
            logger.error("❌ [TASK_SELECTOR] タスクリストが存在しません")
            raise ValueError("タスクリストが存在しません")
        
        # 完了したタスクのIDセット
        # completed_tasksはoperator.addで追加されるため、リストのリストになっている可能性がある
        # フラット化する
        flat_completed_tasks = []
        for item in completed_tasks:
            if isinstance(item, list):
                flat_completed_tasks.extend(item)
            else:
                flat_completed_tasks.append(item)
        
        completed_task_ids = {task.get("task_id") for task in flat_completed_tasks if isinstance(task, dict) and "task_id" in task}
        
        # 依存関係が満たされたタスクを探す
        for task in task_list:
            task_id = task.id
            
            # 既に完了しているタスクはスキップ
            if task_id in completed_task_ids:
                continue
            
            # 依存関係をチェック
            dependencies = task.dependencies or []
            all_dependencies_met = all(dep_id in completed_task_ids for dep_id in dependencies)
            
            if all_dependencies_met:
                logger.info(f"✅ [TASK_SELECTOR] タスク '{task_id}' を選択しました: {task.description}")
                logger.info(f"  - ツール: {task.tool}")
                logger.info(f"  - 引数: {task.args}")
                return {"current_task_id": task_id}
        
        # 実行可能なタスクが見つからない場合
        logger.warning("⚠️ [TASK_SELECTOR] 実行可能なタスクが見つかりません")
        return {}
    except Exception as e:
        logger.error(f"❌ [TASK_SELECTOR] タスク選択中にエラーが発生しました: {e}", exc_info=True)
        raise


def tool_executor(state: State) -> Dict[str, Any]:
    """
    選択されたタスクを実行するノード
    
    Args:
        state: 現在の状態
        
    Returns:
        更新された状態（ツール実行結果を含む）
    """
    logger.info("⚙️ [TOOL_EXECUTOR] ツール実行を開始します")
    
    try:
        task_list = state.get("task_list", [])
        current_task_id = state.get("current_task_id")
        object_positions = state.get("object_positions", {})
        
        if not current_task_id:
            # task_selectorがタスクを選択しなかった場合（すべてのタスクが完了している可能性）
            logger.warning("⚠️ [TOOL_EXECUTOR] 実行するタスクが指定されていません。verifierに遷移します。")
            # 空の状態を返して、verifierに遷移させる
            return {}
        
        # 現在のタスクを取得
        current_task = None
        for task in task_list:
            if task.id == current_task_id:
                current_task = task
                break
        
        if not current_task:
            logger.error(f"❌ [TOOL_EXECUTOR] タスク '{current_task_id}' が見つかりません")
            raise ValueError(f"タスク '{current_task_id}' が見つかりません")
        
        tool_name = current_task.tool
        tool_args_raw = current_task.args
        
        # JSON文字列をdictに変換
        if isinstance(tool_args_raw, str):
            try:
                tool_args = json.loads(tool_args_raw)
            except json.JSONDecodeError as e:
                logger.error(f"❌ [TOOL_EXECUTOR] argsのJSONパースに失敗: {tool_args_raw}, エラー: {e}")
                raise ValueError(f"argsのJSONパースに失敗: {tool_args_raw}")
        else:
            # 既にdictの場合はそのまま使用（後方互換性）
            tool_args = tool_args_raw
        
        logger.info(f"🔧 [TOOL_EXECUTOR] タスク '{current_task_id}': {current_task.description}")
        logger.info(f"  - ツール: {tool_name}")
        logger.info(f"  - 引数（生）: {tool_args_raw}")
        logger.info(f"  - 引数（パース後）: {tool_args}")
        
        result = None
        updated_state = {}
        
        if tool_name == "get_object_position":
            item_name = tool_args.get("item_name", "")
            position = get_object_position(item_name)
            # 位置情報を状態に保存
            updated_state["object_positions"] = {**object_positions, item_name: position}
            result = {"position": position}
            logger.info(f"✅ [TOOL_EXECUTOR] 物体位置を取得: {item_name} -> {position}")
            
        elif tool_name == "move_arm_to":
            # 座標が直接指定されている場合と、物体名から取得する場合を考慮
            if "x" in tool_args and "y" in tool_args and "z" in tool_args:
                x = tool_args.get("x", 0.0)
                y = tool_args.get("y", 0.0)
                z = tool_args.get("z", 0.0)
            elif "item_name" in tool_args:
                # 物体名から位置を取得
                item_name = tool_args.get("item_name")
                if item_name in object_positions:
                    x, y, z = object_positions[item_name]
                else:
                    logger.error(f"❌ [TOOL_EXECUTOR] 物体 '{item_name}' の位置が取得されていません")
                    raise ValueError(f"物体 '{item_name}' の位置が取得されていません")
            else:
                logger.error("❌ [TOOL_EXECUTOR] move_arm_toの引数が不正です")
                raise ValueError("move_arm_toの引数が不正です")
            
            success = move_arm_to(x, y, z)
            if success:
                updated_state = {
                    "gripper_position_x": x,
                    "gripper_position_y": y,
                    "gripper_position_z": z
                }
                logger.info(f"✅ [TOOL_EXECUTOR] アームを移動: ({x}, {y}, {z})")
            result = {"success": success, "position": (x, y, z)}
            
        elif tool_name == "control_gripper":
            action = tool_args.get("action", "open")
            success = control_gripper(action)
            if success:
                updated_state = {
                    "gripper_state": action
                }
                logger.info(f"✅ [TOOL_EXECUTOR] グリッパーを操作: {action}")
            result = {"success": success, "action": action}
            
        else:
            logger.error(f"❌ [TOOL_EXECUTOR] 未知のツール: {tool_name}")
            raise ValueError(f"未知のツール: {tool_name}")
        
        # 実行結果を状態に保存（task_updaterで使用）
        updated_state["_last_tool_result"] = result
        updated_state["_last_task_id"] = current_task_id
        
        return updated_state
    except Exception as e:
        logger.error(f"❌ [TOOL_EXECUTOR] ツール実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def task_updater(state: State) -> Dict[str, Any]:
    """
    実行完了したタスクを完了済みにマークするノード
    
    Args:
        state: 現在の状態
        
    Returns:
        更新された状態（completed_tasksに追加）
    """
    logger.info("📝 [TASK_UPDATER] タスクを完了済みにマークします")
    
    try:
        current_task_id = state.get("_last_task_id")
        tool_result = state.get("_last_tool_result", {})
        completed_tasks = state.get("completed_tasks", [])
        
        if not current_task_id:
            # tool_executorがタスクを実行しなかった場合（すべてのタスクが完了している可能性）
            logger.warning("⚠️ [TASK_UPDATER] 完了するタスクIDが指定されていません。verifierに遷移します。")
            # 空の状態を返して、verifierに遷移させる
            return {}
        
        # 完了したタスクの情報を追加
        completed_task_info = {
            "task_id": current_task_id,
            "result": tool_result
        }
        
        logger.info(f"✅ [TASK_UPDATER] タスク '{current_task_id}' を完了済みにマークしました")
        
        # 完了したタスクの情報を追加
        # completed_tasksはoperator.addで追加されるため、リストとして返す
        # 一時的なフィールドは戻り値から除外（NotRequiredフィールドなので、除外すると更新されない）
        return {
            "completed_tasks": [completed_task_info]
        }
    except Exception as e:
        logger.error(f"❌ [TASK_UPDATER] タスク更新中にエラーが発生しました: {e}", exc_info=True)
        raise


def verifier(state: State) -> Dict[str, Any]:
    """
    すべてのタスクが完了したかどうかを確認するノード
    
    Args:
        state: 現在の状態
        
    Returns:
        更新された状態（task_completedを含む）
    """
    logger.info("🔍 [VERIFIER] タスク完了状況を確認します")
    
    try:
        task_list = state.get("task_list", [])
        completed_tasks = state.get("completed_tasks", [])
        gripper_x = state.get("gripper_position_x", 0.0)
        gripper_y = state.get("gripper_position_y", 0.0)
        gripper_z = state.get("gripper_position_z", 0.0)
        gripper_state = state.get("gripper_state", "open")
        
        logger.info(f"📊 [VERIFIER] 現在の状態:")
        logger.info(f"  - 総タスク数: {len(task_list)}")
        logger.info(f"  - 完了タスク数: {len(completed_tasks)}")
        logger.info(f"  - グリッパー位置: ({gripper_x}, {gripper_y}, {gripper_z})")
        logger.info(f"  - グリッパー状態: {gripper_state}")
        
        if not task_list:
            logger.warning("⚠️ [VERIFIER] タスクリストが存在しません")
            return {"task_completed": False}
        
        # 完了したタスクのIDセット
        # completed_tasksはoperator.addで追加されるため、リストのリストになっている可能性がある
        # フラット化する
        flat_completed_tasks = []
        for item in completed_tasks:
            if isinstance(item, list):
                flat_completed_tasks.extend(item)
            else:
                flat_completed_tasks.append(item)
        
        completed_task_ids = {task.get("task_id") for task in flat_completed_tasks if isinstance(task, dict) and "task_id" in task}
        
        # デバッグ: 完了したタスクIDをログに出力
        logger.debug(f"🔍 [VERIFIER] completed_tasksの構造: {type(completed_tasks)}, 長さ: {len(completed_tasks)}")
        logger.debug(f"🔍 [VERIFIER] flat_completed_tasksの長さ: {len(flat_completed_tasks)}")
        logger.debug(f"🔍 [VERIFIER] 完了したタスクID: {completed_task_ids}")
        logger.debug(f"🔍 [VERIFIER] 全タスクID: {[task.id for task in task_list]}")
        
        # すべてのタスクが完了しているか確認
        all_tasks_completed = len(completed_task_ids) >= len(task_list)
        
        if all_tasks_completed:
            logger.info("✅ [VERIFIER] すべてのタスクが完了しました")
            logger.info(f"✅ [VERIFIER] 完了タスク数: {len(completed_task_ids)}, 総タスク数: {len(task_list)}")
        else:
            remaining_tasks = [task.id for task in task_list if task.id not in completed_task_ids]
            logger.info(f"⏳ [VERIFIER] 未完了のタスク: {remaining_tasks}")
            logger.info(f"⏳ [VERIFIER] 完了タスク数: {len(completed_task_ids)}, 総タスク数: {len(task_list)}")
        
        return {"task_completed": all_tasks_completed}
    except Exception as e:
        logger.error(f"❌ [VERIFIER] 検証中にエラーが発生しました: {e}", exc_info=True)
        raise


def final_answer(state: State, llm) -> Dict[str, Any]:
    """
    結果をもとに、LLMを利用して最終結果を整形して返却するノード
    
    Args:
        state: 現在の状態
        llm: LLMインスタンス
        
    Returns:
        更新された状態（最終回答を含む）
    """
    logger.info("📝 [FINAL_ANSWER] 最終回答を生成します")
    
    try:
        instruction = state.get("instruction", "")
        task_list = state.get("task_list", [])
        completed_tasks = state.get("completed_tasks", [])
        gripper_x = state.get("gripper_position_x", 0.0)
        gripper_y = state.get("gripper_position_y", 0.0)
        gripper_z = state.get("gripper_position_z", 0.0)
        gripper_state = state.get("gripper_state", "open")
        object_positions = state.get("object_positions", {})
        
        logger.info(f"📊 [FINAL_ANSWER] 最終状態:")
        logger.info(f"  - 指示: {instruction}")
        logger.info(f"  - 完了タスク数: {len(completed_tasks)}/{len(task_list)}")
        logger.info(f"  - グリッパー位置: ({gripper_x}, {gripper_y}, {gripper_z})")
        logger.info(f"  - グリッパー状態: {gripper_state}")
        
        # 完了したタスクの詳細を収集
        completed_tasks_summary = []
        for completed_task in completed_tasks:
            task_id = completed_task.get("task_id")
            result = completed_task.get("result", {})
            # 対応するタスク情報を取得
            task_info = next((t for t in task_list if t.id == task_id), None)
            if task_info:
                completed_tasks_summary.append({
                    "id": task_id,
                    "description": task_info.description,
                    "tool": task_info.tool,
                    "result": result
                })
        
        # LLMに最終回答を生成させる
        system_prompt = """あなたはロボットアームの操作結果を報告する専門家です。
ユーザーの指示と実行結果に基づいて、わかりやすく簡潔な最終報告を作成してください。"""
        
        user_prompt = f"""ユーザーの指示: {instruction}

実行されたタスク:
{chr(10).join([f"- {t['id']}: {t['description']} ({t['tool']})" for t in completed_tasks_summary])}

最終状態:
- グリッパー位置: ({gripper_x}, {gripper_y}, {gripper_z})
- グリッパー状態: {gripper_state}
- 取得した物体位置: {object_positions}

上記の情報に基づいて、タスクの実行結果を簡潔に報告してください。"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        logger.debug("🤖 [FINAL_ANSWER] LLMを呼び出しています...")
        response = llm.invoke(messages)
        final_answer_text = response.content.strip()
        
        logger.info(f"✅ [FINAL_ANSWER] 最終回答が生成されました: {final_answer_text[:100]}...")
        
        # 最終回答をmessagesに追加
        return {
            "messages": [AIMessage(content=final_answer_text)]
        }
    except Exception as e:
        logger.error(f"❌ [FINAL_ANSWER] 最終回答生成中にエラーが発生しました: {e}", exc_info=True)
        raise

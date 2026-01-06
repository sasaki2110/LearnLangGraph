"""
ノード関数の実装
"""
import json
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from my_agent.utils.state import State, TodoItem
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def convert_relative_date(deadline_str: str, base_date: Optional[str] = None) -> Optional[str]:
    """
    相対的な日付表現（「明日」「3日後」など）をyyyy-mm-dd形式に変換
    既存の期限を基準にした相対的な変更（「1日伸ばす」など）にも対応
    
    Args:
        deadline_str: 期限の文字列（相対的な日付表現またはyyyy-mm-dd形式）
        base_date: 基準となる日付（yyyy-mm-dd形式）。既存の期限がある場合に指定
        
    Returns:
        yyyy-mm-dd形式の日付文字列、変換できない場合はNone
    """
    if not deadline_str:
        return None
    
    deadline_str = deadline_str.strip()
    
    # 基準日を決定（既存の期限がある場合はそれを使用、ない場合は今日）
    if base_date:
        try:
            base = datetime.strptime(base_date, "%Y-%m-%d").date()
        except ValueError:
            base = datetime.now().date()
    else:
        base = datetime.now().date()
    
    # 既にyyyy-mm-dd形式の場合はそのまま返す
    try:
        datetime.strptime(deadline_str, "%Y-%m-%d")
        return deadline_str
    except ValueError:
        pass  # yyyy-mm-dd形式ではないので、相対日付として処理
    
    # 相対的な日付表現を処理
    deadline_lower = deadline_str.lower()
    
    # 「N日伸ばす」「N日延ばす」「N日後に」のパターン（既存の期限を基準に加算）
    match = re.search(r'(\d+)\s*日\s*(?:伸ばす|延ばす|後に|後)', deadline_lower)
    if match:
        days = int(match.group(1))
        target_date = base + timedelta(days=days)
        return target_date.strftime("%Y-%m-%d")
    
    # 「N日前に」「N日早く」のパターン（既存の期限を基準に減算）
    match = re.search(r'(\d+)\s*日\s*(?:前に|早く|前)', deadline_lower)
    if match:
        days = int(match.group(1))
        target_date = base - timedelta(days=days)
        return target_date.strftime("%Y-%m-%d")
    
    # 「N週間伸ばす」「N週間延ばす」のパターン
    match = re.search(r'(\d+)\s*週間\s*(?:伸ばす|延ばす|後に|後)', deadline_lower)
    if match:
        weeks = int(match.group(1))
        target_date = base + timedelta(weeks=weeks)
        return target_date.strftime("%Y-%m-%d")
    
    # 「N週間前に」「N週間早く」のパターン
    match = re.search(r'(\d+)\s*週間\s*(?:前に|早く|前)', deadline_lower)
    if match:
        weeks = int(match.group(1))
        target_date = base - timedelta(weeks=weeks)
        return target_date.strftime("%Y-%m-%d")
    
    # 以下は今日を基準とした絶対的な日付表現
    today = datetime.now().date()
    
    # 「明日」「あした」（今日を基準）
    if deadline_lower in ["明日", "あした", "あす", "tomorrow"]:
        target_date = today + timedelta(days=1)
        return target_date.strftime("%Y-%m-%d")
    
    # 「明後日」「あさって」
    if deadline_lower in ["明後日", "あさって", "day after tomorrow"]:
        target_date = today + timedelta(days=2)
        return target_date.strftime("%Y-%m-%d")
    
    # 「N日後」のパターン（数字 + 日後）
    match = re.search(r'(\d+)\s*日後', deadline_lower)
    if match:
        days = int(match.group(1))
        target_date = today + timedelta(days=days)
        return target_date.strftime("%Y-%m-%d")
    
    # 「N週間後」のパターン
    match = re.search(r'(\d+)\s*週間後', deadline_lower)
    if match:
        weeks = int(match.group(1))
        target_date = today + timedelta(weeks=weeks)
        return target_date.strftime("%Y-%m-%d")
    
    # 「来週」
    if deadline_lower in ["来週", "らいしゅう", "next week"]:
        target_date = today + timedelta(weeks=1)
        return target_date.strftime("%Y-%m-%d")
    
    # 「来月」
    if deadline_lower in ["来月", "らいげつ", "next month"]:
        # 来月の同じ日（存在しない場合は来月の最終日）
        if today.month == 12:
            next_month_first = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_first = today.replace(month=today.month + 1, day=1)
        
        # 来月の最終日を計算
        if next_month_first.month == 12:
            next_month_last = next_month_first.replace(year=next_month_first.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            next_month_last = next_month_first.replace(month=next_month_first.month + 1, day=1) - timedelta(days=1)
        
        # 来月の同じ日が存在する場合はそれを使用、存在しない場合は来月の最終日を使用
        if today.day <= next_month_last.day:
            target_date = next_month_first.replace(day=today.day)
        else:
            target_date = next_month_last
        return target_date.strftime("%Y-%m-%d")
    
    # 「来年」
    if deadline_lower in ["来年", "らいねん", "next year"]:
        target_date = today.replace(year=today.year + 1)
        return target_date.strftime("%Y-%m-%d")
    
    # 変換できない場合はNoneを返す
    logger.warning(f"⚠️ [EXTRACT] 相対日付の変換に失敗しました: {deadline_str}")
    return None


def extract_operation(state: State, llm):
    """
    ユーザーの発言から「操作の種類（追加/削除/更新など）」と「タスク内容・期限」をJSONで抽出するノード
    
    Args:
        state: 現在の状態
        llm: LLMインスタンス
        
    Returns:
        抽出された操作情報を含む状態の更新
    """
    logger.info("📝 [EXTRACT] 操作抽出を開始します")
    logger.debug(f"📊 [EXTRACT] 現在の状態: messages数={len(state.get('messages', []))}")
    
    try:
        # メッセージが存在する場合、最後のユーザーメッセージから操作を抽出
        if not state.get("messages") or len(state["messages"]) == 0:
            logger.warning("⚠️ [EXTRACT] メッセージが存在しません")
            return {
                "operation": None,
                "extracted_data": None
            }
        
        # 最後のメッセージの内容を取得
        last_message = state["messages"][-1]
        if hasattr(last_message, "content"):
            user_input = last_message.content.strip()
        else:
            user_input = str(last_message).strip()
        
        logger.info(f"📝 [EXTRACT] ユーザー入力: {user_input[:100]}...")
        
        # 現在のTODOリストの情報も含める（更新や削除の際に参照するため）
        todo_list = state.get("todo_list", [])
        todo_list_summary = ""
        if todo_list:
            todo_list_summary = "\n現在のTODOリスト:\n"
            for todo in todo_list:
                todo_list_summary += f"- ID: {todo['task_id']}, 内容: {todo['content']}, 期限: {todo['deadline']}, ステータス: {todo['status']}\n"
        else:
            todo_list_summary = "\n現在のTODOリスト: 空です\n"
        
        # LLMに抽出を依頼
        prompt = f"""ユーザーの発言から、TODO管理の操作を抽出してください。

操作の種類は以下のいずれかです：
- "add": 新しいタスクを追加
- "delete": タスクを削除（内容の部分一致で検索）
- "update": タスクを更新（内容、期限、ステータスのいずれかまたは複数を更新）
- "none": 操作なし

抽出する情報：
- operation: 操作の種類（"add", "delete", "update", "none"のいずれか）
- content: タスク内容（追加・削除・更新の対象となるタスクの内容。update時は検索キーとして使用）
- new_content: 新しいタスク内容（update時のみ、内容を変更する場合に指定）
- deadline: 期限（yyyy-mm-dd形式、または「明日」「3日後」などの絶対的な日付表現、または「1日伸ばす」「2日延ばす」などの既存期限を基準にした相対的な変更表現。add時は必須、update時は変更する場合に指定）
- status: ステータス（"done"または"undone"。update時は変更する場合に指定）

JSON形式で返答してください。例：
{{
    "operation": "add",
    "content": "資料作成",
    "new_content": null,
    "deadline": "2024-01-10",
    "status": null
}}

または

{{
    "operation": "delete",
    "content": "資料作成",
    "new_content": null,
    "deadline": null,
    "status": null
}}

または

{{
    "operation": "update",
    "content": "資料作成",
    "new_content": null,
    "deadline": "2024-01-15",
    "status": "done"
}}

または（複数フィールドを同時に更新）

{{
    "operation": "update",
    "content": "資料作成",
    "new_content": "報告書作成",
    "deadline": "2024-01-15",
    "status": "done"
}}

または（既存期限を基準にした相対的な変更）

{{
    "operation": "update",
    "content": "資料作成",
    "new_content": null,
    "deadline": "1日伸ばす",
    "status": null
}}

{todo_list_summary}

ユーザーの発言: {user_input}"""
        
        messages = [
            SystemMessage(content="あなたはユーザーの発言からTODO管理の操作を正確に抽出する専門家です。JSON形式で返答してください。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [EXTRACT] LLMを呼び出しています...")
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        logger.info(f"✅ [EXTRACT] LLM応答を受信しました: {response_text[:200]}...")
        
        # JSONを抽出（コードブロックがある場合は除去）
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # JSONをパース
        try:
            extracted_data = json.loads(response_text)
            
            # 期限が相対的な日付表現の場合は変換
            if extracted_data.get("deadline"):
                original_deadline = extracted_data.get("deadline")
                
                # update操作の場合、既存の期限を基準にする
                base_date = None
                if extracted_data.get("operation") == "update":
                    # 該当するタスクの既存の期限を取得
                    search_content = extracted_data.get("content", "").strip()
                    if search_content:
                        todo_list = state.get("todo_list", [])
                        for todo in todo_list:
                            if search_content in todo.get("content", ""):
                                existing_deadline = todo.get("deadline", "")
                                if existing_deadline:
                                    base_date = existing_deadline
                                    logger.debug(f"📅 [EXTRACT] 既存の期限を基準にします: {base_date}")
                                break
                
                converted_deadline = convert_relative_date(original_deadline, base_date=base_date)
                if converted_deadline:
                    if converted_deadline != original_deadline:
                        logger.info(f"📅 [EXTRACT] 相対日付を変換しました: {original_deadline} → {converted_deadline}")
                    extracted_data["deadline"] = converted_deadline
                else:
                    logger.warning(f"⚠️ [EXTRACT] 期限の変換に失敗しました: {original_deadline}")
            
            logger.info(f"✅ [EXTRACT] 操作抽出が完了しました: operation={extracted_data.get('operation')}, content={extracted_data.get('content', '')[:50]}...")
            
            return {
                "operation": extracted_data.get("operation"),
                "extracted_data": extracted_data
            }
        except json.JSONDecodeError as e:
            logger.error(f"❌ [EXTRACT] JSON解析エラー: {e}, 応答: {response_text}")
            # デフォルト値を返す
            return {
                "operation": "none",
                "extracted_data": None
            }
        
    except Exception as e:
        logger.error(f"❌ [EXTRACT] 操作抽出中にエラーが発生しました: {e}", exc_info=True)
        return {
            "operation": "none",
            "extracted_data": None
        }


def manage_todo_list(state: State):
    """
    抽出された情報に基づき、Pythonコードで State["todo_list"] を更新するノード
    
    Args:
        state: 現在の状態
        
    Returns:
        更新されたtodo_listとrecent_changeを含む状態の更新
    """
    logger.info("🔧 [MANAGER] TODOリスト管理を開始します")
    
    try:
        operation = state.get("operation")
        extracted_data = state.get("extracted_data")
        todo_list = state.get("todo_list", []).copy()  # コピーを作成
        recent_change = ""
        
        if not operation or operation == "none" or not extracted_data:
            logger.info("ℹ️ [MANAGER] 操作なし、またはデータなし")
            return {
                "todo_list": todo_list,
                "recent_change": "変更はありませんでした。"
            }
        
        content = extracted_data.get("content", "").strip()
        if not content:
            logger.warning("⚠️ [MANAGER] タスク内容が空です")
            return {
                "todo_list": todo_list,
                "recent_change": "タスク内容が指定されていませんでした。"
            }
        
        if operation == "add":
            # 新しいタスクを追加
            deadline = extracted_data.get("deadline", "")
            if not deadline:
                logger.warning("⚠️ [MANAGER] 期限が指定されていませんが、追加を続行します")
                deadline = ""  # 空文字列を許可
            
            # 期限の形式を検証（yyyy-mm-dd形式）
            if deadline:
                try:
                    datetime.strptime(deadline, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"⚠️ [MANAGER] 期限の形式が不正です: {deadline}。空文字列に設定します。")
                    deadline = ""
            
            new_todo: TodoItem = {
                "task_id": str(uuid.uuid4()),
                "content": content,
                "deadline": deadline,
                "status": "undone"
            }
            todo_list.append(new_todo)
            recent_change = f"「{content}」を期限{deadline if deadline else '（期限なし）'}で追加しました。"
            logger.info(f"✅ [MANAGER] タスクを追加しました: {content[:50]}... (ID: {new_todo['task_id']})")
        
        elif operation == "delete":
            # 内容の部分一致でタスクを削除
            deleted_count = 0
            deleted_contents = []
            remaining_todos = []
            for todo in todo_list:
                if content in todo["content"]:
                    deleted_count += 1
                    deleted_contents.append(todo["content"])
                else:
                    remaining_todos.append(todo)
            todo_list = remaining_todos
            
            if deleted_count > 0:
                recent_change = f"「{content}」を含むタスクを{deleted_count}件削除しました。"
                logger.info(f"✅ [MANAGER] タスクを削除しました: {content[:50]}... ({deleted_count}件)")
            else:
                recent_change = f"「{content}」を含むタスクが見つかりませんでした。"
                logger.warning(f"⚠️ [MANAGER] 削除対象のタスクが見つかりませんでした: {content[:50]}...")
        
        elif operation == "update":
            # タスクを更新（内容、期限、ステータスのいずれかまたは複数を更新）
            new_content = extracted_data.get("new_content", "").strip() if extracted_data.get("new_content") else None
            new_deadline = extracted_data.get("deadline", "").strip() if extracted_data.get("deadline") else None
            new_status = extracted_data.get("status", "").strip().lower() if extracted_data.get("status") else None
            
            # 更新するフィールドがない場合はエラー
            if not new_content and not new_deadline and not new_status:
                logger.warning("⚠️ [MANAGER] 更新するフィールドが指定されていません")
                return {
                    "todo_list": todo_list,
                    "recent_change": "更新するフィールドが指定されていませんでした。"
                }
            
            # ステータスの検証
            if new_status and new_status not in ["done", "undone"]:
                logger.warning(f"⚠️ [MANAGER] 無効なステータス: {new_status}")
                return {
                    "todo_list": todo_list,
                    "recent_change": f"無効なステータスが指定されました: {new_status}"
                }
            
            # 期限の形式を検証（yyyy-mm-dd形式）
            if new_deadline:
                try:
                    datetime.strptime(new_deadline, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"⚠️ [MANAGER] 期限の形式が不正です: {new_deadline}")
                    return {
                        "todo_list": todo_list,
                        "recent_change": f"期限の形式が不正です: {new_deadline}"
                    }
            
            updated_count = 0
            changes = []
            
            for todo in todo_list:
                if content in todo["content"]:
                    # 各フィールドを更新
                    if new_content:
                        old_content = todo["content"]
                        todo["content"] = new_content
                        changes.append(f"内容を「{old_content}」から「{new_content}」に変更")
                        logger.info(f"✅ [MANAGER] タスクの内容を更新しました: {old_content[:50]}... -> {new_content[:50]}...")
                    
                    if new_deadline:
                        old_deadline = todo["deadline"]
                        todo["deadline"] = new_deadline
                        changes.append(f"期限を{old_deadline if old_deadline else '（期限なし）'}から{new_deadline}に変更")
                        logger.info(f"✅ [MANAGER] タスクの期限を更新しました: {todo['content'][:50]}... ({old_deadline} -> {new_deadline})")
                    
                    if new_status:
                        old_status = todo["status"]
                        todo["status"] = new_status
                        status_text = "完了" if new_status == "done" else "未完了"
                        changes.append(f"ステータスを{status_text}に変更")
                        logger.info(f"✅ [MANAGER] タスクのステータスを更新しました: {todo['content'][:50]}... ({old_status} -> {new_status})")
                    
                    updated_count += 1
            
            if updated_count > 0:
                recent_change = f"「{content}」を含むタスクを{updated_count}件更新しました。"
                if changes:
                    recent_change += " " + "、".join(changes) + "。"
            else:
                recent_change = f"「{content}」を含むタスクが見つかりませんでした。"
                logger.warning(f"⚠️ [MANAGER] 更新対象のタスクが見つかりませんでした: {content[:50]}...")
        
        else:
            logger.warning(f"⚠️ [MANAGER] 未知の操作: {operation}")
            recent_change = f"未知の操作が指定されました: {operation}"
        
        logger.info(f"✅ [MANAGER] TODOリスト管理が完了しました。現在のタスク数: {len(todo_list)}")
        
        return {
            "todo_list": todo_list,
            "recent_change": recent_change
        }
        
    except Exception as e:
        logger.error(f"❌ [MANAGER] TODOリスト管理中にエラーが発生しました: {e}", exc_info=True)
        return {
            "todo_list": state.get("todo_list", []),
            "recent_change": f"エラーが発生しました: {str(e)}"
        }


def generate_response(state: State, llm):
    """
    人間フレンドリーな返答を作成するノード
    
    Args:
        state: 現在の状態
        llm: LLMインスタンス
        
    Returns:
        生成された返答を含む状態の更新
    """
    logger.info("💬 [RESPONSE] 返答生成を開始します")
    
    try:
        recent_change = state.get("recent_change", "")
        todo_list = state.get("todo_list", [])
        
        # 現在のTODOリストの要約を作成
        todo_summary = ""
        if todo_list:
            undone_todos = [todo for todo in todo_list if todo["status"] == "undone"]
            done_todos = [todo for todo in todo_list if todo["status"] == "done"]
            
            todo_summary = f"\n現在のTODOリスト:\n"
            todo_summary += f"- 未完了: {len(undone_todos)}件\n"
            for todo in undone_todos:
                deadline_text = f"（期限: {todo['deadline']}）" if todo['deadline'] else "（期限なし）"
                todo_summary += f"  • {todo['content']} {deadline_text}\n"
            
            if done_todos:
                todo_summary += f"- 完了: {len(done_todos)}件\n"
                for todo in done_todos:
                    deadline_text = f"（期限: {todo['deadline']}）" if todo['deadline'] else "（期限なし）"
                    todo_summary += f"  • {todo['content']} {deadline_text}\n"
        else:
            todo_summary = "\n現在のTODOリスト: 空です\n"
        
        # LLMに返答を生成させる
        prompt = f"""以下の情報を基に、ユーザーに対して自然で親しみやすい返答を生成してください。

{recent_change}

{todo_summary}

返答は簡潔で、親しみやすい口調でお願いします。"""
        
        messages = [
            SystemMessage(content="あなたは親しみやすいTODO管理アシスタントです。ユーザーに対して自然で親切な返答を生成してください。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [RESPONSE] LLMを呼び出しています...")
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        logger.info(f"✅ [RESPONSE] 返答生成が完了しました (長さ: {len(response_text)}文字)")
        logger.debug(f"💬 [RESPONSE] 生成された返答: {response_text[:100]}...")
        
        # Vercel AI SDKのチャットが表示できるように、AIMessageとしてmessagesに追加
        return {
            "messages": [AIMessage(content=response_text)]  # チャットUIで表示されるメッセージ
        }
        
    except Exception as e:
        logger.error(f"❌ [RESPONSE] 返答生成中にエラーが発生しました: {e}", exc_info=True)
        error_message = f"申し訳ございません。エラーが発生しました: {str(e)}"
        return {
            "messages": [AIMessage(content=error_message)]
        }


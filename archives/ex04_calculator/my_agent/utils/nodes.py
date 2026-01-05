"""
ノード関数の実装
"""
from langchain.messages import SystemMessage, ToolMessage
from langgraph.graph import END
from my_agent.utils.state import MessagesState
from my_agent.utils.tools import add, mul, sub, div
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')

# ツールを名前でマッピング
tools = [add, mul, sub, div]
tools_by_name = {tool.name: tool for tool in tools}


def llm_steps(state: MessagesState, model_with_tools):
    """リクエストに対処するノード：ユーザーリクエストをmodel_with_toolsへ渡す"""
    logger.info("🤖 [LLM_STEPS] リクエストに対処するノードを開始します")
    logger.debug(f"📊 [LLM_STEPS] 現在のメッセージ数: {len(state.get('messages', []))}")
    
    try:
        # システムメッセージとユーザーメッセージを結合
        messages = [
            SystemMessage(
                content="You are a helpful assistant tasked with performing arithmetic on a set of inputs. Use the available tools to perform calculations."
            )
        ] + state["messages"]
        
        logger.debug(f"💬 [LLM_STEPS] LLMに送信するメッセージ数: {len(messages)}")
        
        # LLMを呼び出し
        result = model_with_tools.invoke(messages)
        
        logger.info(f"✅ [LLM_STEPS] LLM呼び出しが完了しました")
        
        # ツール呼び出しがあるかチェック
        if hasattr(result, 'tool_calls') and result.tool_calls:
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"🔧 [LLM_STEPS] ツール呼び出しを検出: {', '.join(tool_names)}")
        else:
            logger.info("💬 [LLM_STEPS] ツール呼び出しなし - 通常の応答を返します")
        
        return {
            "messages": [result]
        }
    except Exception as e:
        logger.error(f"❌ [LLM_STEPS] LLM呼び出し中にエラーが発生しました: {e}", exc_info=True)
        raise


def action_steps(state: MessagesState):
    """ツール実行ノード：指定のツールを実行する（複数指定された場合は全部実行）"""
    logger.info("🔧 [ACTION_STEPS] ツール実行ノードの実行を開始します")
    
    try:
        last_message = state["messages"][-1]
        
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            logger.warning("⚠️ [ACTION_STEPS] ツール呼び出しが見つかりませんでした")
            return {"messages": []}
        
        tool_calls = last_message.tool_calls
        logger.info(f"🔧 [ACTION_STEPS] {len(tool_calls)}個のツール呼び出しを処理します")
        
        result = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("args", {})
            
            logger.info(f"🔧 [ACTION_STEPS] ツール '{tool_name}' を実行します (引数: {tool_args})")
            
            if tool_name not in tools_by_name:
                logger.error(f"❌ [ACTION_STEPS] 未知のツール名: {tool_name}")
                continue
            
            tool = tools_by_name[tool_name]
            
            try:
                observation = tool.invoke(tool_args)
                logger.info(f"✅ [ACTION_STEPS] ツール '{tool_name}' の実行が完了しました (結果: {observation})")
                result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
            except Exception as e:
                logger.error(f"❌ [ACTION_STEPS] ツール '{tool_name}' の実行中にエラーが発生しました: {e}", exc_info=True)
                error_message = f"エラーが発生しました: {str(e)}"
                result.append(ToolMessage(content=error_message, tool_call_id=tool_call["id"]))
        
        logger.info(f"✅ [ACTION_STEPS] ツール実行ノードの実行が完了しました ({len(result)}個の結果)")
        return {"messages": result}
        
    except Exception as e:
        logger.error(f"❌ [ACTION_STEPS] ツール実行ノードの実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def llm_format_steps(state: MessagesState, model_with_tools):
    """回答整形ノード：ツール（あるいはLLM）の回答を整形して、ユーザーへのリザルトに追加する"""
    logger.info("📝 [LLM_FORMAT_STEPS] 回答整形ノードを開始します")
    
    try:
        # システムメッセージとメッセージ履歴を結合
        messages = [
            SystemMessage(
                content="You are a helpful assistant. Format the tool results into a clear, user-friendly response."
            )
        ] + state["messages"]
        
        logger.debug(f"💬 [LLM_FORMAT_STEPS] LLMに送信するメッセージ数: {len(messages)}")
        
        # LLMを呼び出して回答を整形
        result = model_with_tools.invoke(messages)
        
        logger.info(f"✅ [LLM_FORMAT_STEPS] 回答整形が完了しました")
        logger.debug(f"💬 [LLM_FORMAT_STEPS] 整形された回答: {result.content[:100] if hasattr(result, 'content') else 'N/A'}...")
        
        return {
            "messages": [result]
        }
    except Exception as e:
        logger.error(f"❌ [LLM_FORMAT_STEPS] 回答整形中にエラーが発生しました: {e}", exc_info=True)
        raise


def should_continue(state: MessagesState):
    """LLMがツールを呼び出したかどうかを確認する条件エッジ関数"""
    logger.debug("🔀 [ROUTING] ルーティング判定を開始します")
    
    try:
        messages = state["messages"]
        if not messages:
            logger.warning("⚠️ [ROUTING] メッセージがありません")
            return "llm_format_steps"
        
        last_message = messages[-1]
        
        # LLMがツールを呼び出した場合、アクションを実行
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.info(f"🔀 [ROUTING] ツール呼び出しを検出 - 'action_steps' にルーティングします")
            return "action_steps"
        
        # それ以外の場合、回答整形ノードへ
        logger.info("🔀 [ROUTING] ツール呼び出しなし - 'llm_format_steps' にルーティングします")
        return "llm_format_steps"
        
    except Exception as e:
        logger.error(f"❌ [ROUTING] ルーティング判定中にエラーが発生しました: {e}", exc_info=True)
        return "llm_format_steps"


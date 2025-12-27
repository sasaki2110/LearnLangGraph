"""
ノード関数の実装
"""
from typing import Literal
from langchain.messages import SystemMessage, ToolMessage
from langgraph.graph import END
from my_agent.utils.state import MessagesState
from my_agent.utils.tools import add, multiply, divide
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')

# ツールを名前でマッピング
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}


def llm_call(state: MessagesState, model_with_tools):
    """LLMがツールを呼び出すかどうかを決定します。"""
    logger.info("🤖 [LLM] LLM呼び出しを開始します")
    logger.debug(f"📊 [LLM] 現在の状態: llm_calls={state.get('llm_calls', 0)}, messages数={len(state.get('messages', []))}")
    
    try:
        # システムメッセージとユーザーメッセージを結合
        messages = [
            SystemMessage(
                content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
            )
        ] + state["messages"]
        
        logger.debug(f"💬 [LLM] LLMに送信するメッセージ数: {len(messages)}")
        
        # LLMを呼び出し
        result = model_with_tools.invoke(messages)
        
        logger.info(f"✅ [LLM] LLM呼び出しが完了しました (llm_calls: {state.get('llm_calls', 0) + 1})")
        
        # ツール呼び出しがあるかチェック
        if hasattr(result, 'tool_calls') and result.tool_calls:
            tool_names = [tc.get('name', 'unknown') for tc in result.tool_calls]
            logger.info(f"🔧 [LLM] ツール呼び出しを検出: {', '.join(tool_names)}")
        else:
            logger.info("💬 [LLM] ツール呼び出しなし - 通常の応答を返します")
        
        return {
            "messages": [result],
            "llm_calls": state.get('llm_calls', 0) + 1
        }
    except Exception as e:
        logger.error(f"❌ [LLM] LLM呼び出し中にエラーが発生しました: {e}", exc_info=True)
        raise


def tool_node(state: MessagesState):
    """ツール呼び出しを実行します。"""
    logger.info("🔧 [TOOL] ツールノードの実行を開始します")
    
    try:
        last_message = state["messages"][-1]
        
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            logger.warning("⚠️ [TOOL] ツール呼び出しが見つかりませんでした")
            return {"messages": []}
        
        tool_calls = last_message.tool_calls
        logger.info(f"🔧 [TOOL] {len(tool_calls)}個のツール呼び出しを処理します")
        
        result = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "unknown")
            tool_args = tool_call.get("args", {})
            
            logger.info(f"🔧 [TOOL] ツール '{tool_name}' を実行します (引数: {tool_args})")
            
            if tool_name not in tools_by_name:
                logger.error(f"❌ [TOOL] 未知のツール名: {tool_name}")
                continue
            
            tool = tools_by_name[tool_name]
            
            try:
                observation = tool.invoke(tool_args)
                logger.info(f"✅ [TOOL] ツール '{tool_name}' の実行が完了しました (結果: {observation})")
                result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
            except Exception as e:
                logger.error(f"❌ [TOOL] ツール '{tool_name}' の実行中にエラーが発生しました: {e}", exc_info=True)
                error_message = f"エラーが発生しました: {str(e)}"
                result.append(ToolMessage(content=error_message, tool_call_id=tool_call["id"]))
        
        logger.info(f"✅ [TOOL] ツールノードの実行が完了しました ({len(result)}個の結果)")
        return {"messages": result}
        
    except Exception as e:
        logger.error(f"❌ [TOOL] ツールノードの実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def should_continue(state: MessagesState):
    """LLMがツールを呼び出したかどうかを確認します。"""
    logger.debug("🔀 [ROUTING] ルーティング判定を開始します")
    
    try:
        messages = state["messages"]
        if not messages:
            logger.warning("⚠️ [ROUTING] メッセージがありません")
            return END
        
        last_message = messages[-1]
        
        # LLMがツールを呼び出した場合、アクションを実行
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.info(f"🔀 [ROUTING] ツール呼び出しを検出 - 'tool_node' にルーティングします")
            return "tool_node"
        
        # それ以外の場合、停止（ユーザーに返信）
        logger.info("🔀 [ROUTING] ツール呼び出しなし - 終了します")
        return END
        
    except Exception as e:
        logger.error(f"❌ [ROUTING] ルーティング判定中にエラーが発生しました: {e}", exc_info=True)
        return END


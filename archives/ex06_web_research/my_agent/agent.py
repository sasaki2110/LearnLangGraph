"""
自律的なWebリサーチエージェント（Tool + Loop）

このグラフは、ユーザーから「最新のAIニュースについて調べてまとめて」といった依頼を受け、
満足いくまで調査を続けるエージェントです。
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがインストールされていない場合はスキップ
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from typing import Literal
from my_agent.utils.state import State
from my_agent.utils.nodes import (
    extract_theme,
    think_and_action,
    tool_node,
    observe,
    format_final_answer,
    search_web
)
from my_agent.utils.logging_config import setup_logging, get_logger, get_log_level

# ロギングをセットアップ
log_level = get_log_level()
setup_logging(log_level=log_level, initialize=True)
logger = get_logger('agent')

logger.info("🚀 [AGENT] エージェントの初期化を開始します")

# OpenAI設定
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
logger.info(f"🤖 [AGENT] 使用モデル: {MODEL_NAME}")

try:
    # モデルの初期化
    logger.debug("🤖 [AGENT] チャットモデルを初期化しています...")
    llm = init_chat_model(
        MODEL_NAME,
        temperature=0
    )
    logger.info("✅ [AGENT] チャットモデルの初期化が完了しました")
    
    # ツールをバインド
    tools = [search_web]
    llm_with_tools = llm.bind_tools(tools)
    logger.info("✅ [AGENT] ツールのバインドが完了しました")
    
    # ノード関数をラップ（llmを閉包で保持）
    def extract_theme_node(state: State):
        """ユーザー指定テーマ抽出ノード"""
        return extract_theme(state)
    
    def think_and_action_node(state: State):
        """思考＋Actionノード（llm_with_toolsを閉包で保持）"""
        return think_and_action(state, llm_with_tools)
    
    def tool_node_wrapper(state: State):
        """ツールノード"""
        return tool_node(state)
    
    def observe_node(state: State):
        """観察ノード（llmを閉包で保持）"""
        return observe(state, llm)
    
    def format_final_answer_node(state: State):
        """最終回答整形ノード（llmを閉包で保持）"""
        return format_final_answer(state, llm)
    
    # 条件分岐関数: 思考＋Actionノードから
    def should_use_tool(state: State) -> Literal["tool_node", "observe"]:
        """
        思考＋Actionノードからの条件分岐
        ツール呼び出しが必要ならtool_node、不要ならobserve
        """
        logger.debug("🔀 [ROUTING] ツール使用判定を開始します")
        
        try:
            messages = state.get("messages", [])
            if not messages:
                logger.warning("⚠️ [ROUTING] メッセージがありません")
                return "observe"
            
            last_message = messages[-1]
            
            # LLMがツールを呼び出した場合、ツールノードへ
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                logger.info(f"🔀 [ROUTING] ツール呼び出しを検出 - 'tool_node' にルーティングします")
                return "tool_node"
            
            # それ以外の場合、観察ノードへ
            logger.info("🔀 [ROUTING] ツール呼び出しなし - 'observe' にルーティングします")
            return "observe"
            
        except Exception as e:
            logger.error(f"❌ [ROUTING] ルーティング判定中にエラーが発生しました: {e}", exc_info=True)
            return "observe"
    
    # 条件分岐関数: 観察ノードから
    def should_continue_research(state: State) -> Literal["think_and_action", "format_final_answer"]:
        """
        観察ノードからの条件分岐
        is_sufficient=trueならformat_final_answer、falseならthink_and_action
        llm_call_count>10ならformat_final_answer
        """
        logger.debug("🔀 [ROUTING] リサーチ継続判定を開始します")
        
        try:
            # llm_call_count > 10 の場合は終了
            llm_call_count = state.get("llm_call_count", 0)
            if llm_call_count > 10:
                logger.info(f"🔀 [ROUTING] 試行回数オーバー (llm_call_count: {llm_call_count}) - 'format_final_answer' にルーティングします")
                return "format_final_answer"
            
            # is_sufficientがTrueの場合は終了
            is_sufficient = state.get("is_sufficient", False)
            if is_sufficient:
                logger.info("🔀 [ROUTING] 調査結果が十分 - 'format_final_answer' にルーティングします")
                return "format_final_answer"
            
            # それ以外の場合、リサーチを継続
            logger.info("🔀 [ROUTING] 調査結果が不十分 - 'think_and_action' にルーティングします")
            return "think_and_action"
            
        except Exception as e:
            logger.error(f"❌ [ROUTING] ルーティング判定中にエラーが発生しました: {e}", exc_info=True)
            return "format_final_answer"
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(State)
    
    # ノードの追加
    graph.add_node("extract_theme", extract_theme_node)
    graph.add_node("think_and_action", think_and_action_node)
    graph.add_node("tool_node", tool_node_wrapper)
    graph.add_node("observe", observe_node)
    graph.add_node("format_final_answer", format_final_answer_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました (extract_theme, think_and_action, tool_node, observe, format_final_answer)")
    
    # エッジの追加
    graph.add_edge(START, "extract_theme")
    graph.add_edge("extract_theme", "think_and_action")
    
    # 条件分岐エッジ: 思考＋Actionノードから
    graph.add_conditional_edges(
        "think_and_action",
        should_use_tool,
        {
            "tool_node": "tool_node",
            "observe": "observe"
        }
    )
    
    # ツールノードから観察ノードへ
    graph.add_edge("tool_node", "observe")
    
    # 条件分岐エッジ: 観察ノードから
    graph.add_conditional_edges(
        "observe",
        should_continue_research,
        {
            "think_and_action": "think_and_action",
            "format_final_answer": "format_final_answer"
        }
    )
    
    # 最終回答整形ノードから終了へ
    graph.add_edge("format_final_answer", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


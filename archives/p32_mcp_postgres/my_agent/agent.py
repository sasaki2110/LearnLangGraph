"""
MCPサーバー統合のグラフ定義

このグラフは、MCPサーバーを通じてPostgreSQLに接続し、
ユーザーのクエリに基づいてデータベースから情報を取得するエージェントです。
Vercel AI SDKのチャットから呼び出して使用できます。
"""
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenvがインストールされていない場合はスキップ

from langchain.chat_models import init_chat_model
from langchain.messages import ToolMessage
from langgraph.graph import StateGraph, START, END
from my_agent.utils.state import State
from my_agent.utils.nodes import extract_query_intent, execute_postgres_query, format_response
from my_agent.utils.logging_config import setup_logging, get_logger, get_log_level
import asyncio

# MCPアダプターのインポート
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_mcp_adapters.tools import load_mcp_tools
    import asyncio
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ langchain-mcp-adaptersがインストールされていません。MCP機能は使用できません。")

# ロギングをセットアップ
log_level = get_log_level()
setup_logging(log_level=log_level, initialize=True)
logger = get_logger('agent')

logger.info("🚀 [AGENT] エージェントの初期化を開始します")

# OpenAI設定
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
logger.info(f"🤖 [AGENT] 使用モデル: {MODEL_NAME}")

# MCPサーバー設定
MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "postgres-mcp-server")
MCP_SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND", "npx")
MCP_SERVER_ARGS = os.getenv("MCP_SERVER_ARGS", "-y @modelcontextprotocol/server-postgres").split()

try:
    # モデルの初期化
    logger.debug("🤖 [AGENT] チャットモデルを初期化しています...")
    llm = init_chat_model(
        MODEL_NAME,
        temperature=0
    )
    logger.info("✅ [AGENT] チャットモデルの初期化が完了しました")

    # MCPツールの作成
    mcp_tools = []
    if MCP_AVAILABLE:
        try:
            logger.debug("🔧 [AGENT] MCPクライアントを作成しています...")
            logger.info(f"📡 [AGENT] MCPサーバー: {MCP_SERVER_NAME}")
            logger.debug(f"📡 [AGENT] MCPコマンド: {MCP_SERVER_COMMAND} {' '.join(MCP_SERVER_ARGS)}")
            
            # MCPクライアントを作成
            # langchain-mcp-adaptersのAPIに基づく実装
            # 環境変数からPostgreSQL接続文字列を取得
            postgres_connection_string = os.getenv("POSTGRES_CONNECTION_STRING")
            if not postgres_connection_string:
                logger.warning("⚠️ [AGENT] POSTGRES_CONNECTION_STRINGが設定されていません")
                logger.warning("⚠️ [AGENT] MCPツールなしで続行します")
                mcp_tools = []
            else:
                try:
                    # MCPクライアントを作成
                    # langchain-mcp-adaptersの実際のAPIを使用
                    # 接続設定は辞書形式で渡す必要があります
                    # @modelcontextprotocol/server-postgresは、データベースURLをコマンドライン引数として受け取る
                    logger.debug("🔧 [AGENT] MCP接続設定を作成しています...")
                    # 接続文字列をコマンドライン引数として追加
                    mcp_args = MCP_SERVER_ARGS + [postgres_connection_string]
                    connection_config = {
                        "command": MCP_SERVER_COMMAND,
                        "args": mcp_args,
                        "transport": "stdio",  # stdioトランスポートを指定
                        # 環境変数も設定（サーバーが環境変数から読み取る場合に備えて）
                        "env": {"POSTGRES_CONNECTION_STRING": postgres_connection_string}
                    }
                    
                    logger.debug("🔧 [AGENT] MultiServerMCPClientを作成しています...")
                    mcp_client = MultiServerMCPClient(
                        connections={MCP_SERVER_NAME: connection_config}
                    )
                    
                    # 非同期でツールを読み込む
                    # connectionを渡すことで、ツール実行時に新しいセッションが作成される
                    logger.debug("🔧 [AGENT] MCPツールを読み込んでいます...")
                    async def load_tools():
                        # connectionを渡すことで、ツール実行時に新しいセッションが作成される
                        return await load_mcp_tools(
                            session=None,  # sessionはNoneにして、connectionを使用
                            connection=connection_config,
                            server_name=MCP_SERVER_NAME
                        )
                    
                    # 同期的に非同期関数を実行
                    mcp_tools = asyncio.run(load_tools())
                    
                    # MCPクライアントも保持（必要に応じて使用）
                    # ツールはconnectionを使用するため、クライアントは保持しなくても良いが、
                    # 将来的に使用する可能性があるため保持
                    
                    if mcp_tools:
                        logger.info(f"✅ [AGENT] MCPツールの作成が完了しました ({len(mcp_tools)}個のツール)")
                        
                        # 各ツールの情報をログに記録
                        for tool in mcp_tools:
                            tool_name = getattr(tool, 'name', 'N/A')
                            tool_desc = getattr(tool, 'description', 'N/A')
                            logger.debug(f"  - {tool_name}: {tool_desc[:50]}...")
                    else:
                        logger.warning("⚠️ [AGENT] MCPツールが読み込めませんでした")
                except Exception as mcp_error:
                    logger.error(f"❌ [AGENT] MCPクライアント/ツール作成エラー: {mcp_error}", exc_info=True)
                    logger.warning("⚠️ [AGENT] MCPツールなしで続行します")
                    mcp_tools = []
        except Exception as e:
            logger.error(f"❌ [AGENT] MCPツールの作成中にエラーが発生しました: {e}", exc_info=True)
            logger.warning("⚠️ [AGENT] MCPツールなしで続行します")
            mcp_tools = []
    else:
        logger.warning("⚠️ [AGENT] MCP機能が利用できません。MCPツールなしで続行します")

    # LLMにツールをバインド
    if mcp_tools:
        logger.debug("🔗 [AGENT] LLMにMCPツールをバインドしています...")
        llm_with_tools = llm.bind_tools(mcp_tools)
        logger.info("✅ [AGENT] LLMにMCPツールをバインドしました")
    else:
        logger.warning("⚠️ [AGENT] MCPツールがないため、通常のLLMを使用します")
        llm_with_tools = llm

    # ノード関数をラップ（llmを閉包で保持）
    def extract_query_intent_node(state: State):
        """クエリ意図を抽出するノード"""
        return extract_query_intent(state)
    
    
    def execute_postgres_query_node(state: State):
        """PostgreSQLクエリを実行するノード（MCPツールを使用）"""
        return execute_postgres_query(state, llm_with_tools)
    
    
    def format_response_node(state: State):
        """最終応答を生成するノード"""
        return format_response(state, llm)
    
    
    # グラフの構築
    logger.debug("📊 [AGENT] グラフの構築を開始します")
    graph = StateGraph(State)
    
    # ノードの追加
    graph.add_node("extract_query_intent", extract_query_intent_node)
    graph.add_node("execute_postgres_query", execute_postgres_query_node)
    
    # MCPツールがある場合はカスタムツールノードを追加
    # MCPツールは非同期なので、同期的に実行するラッパーが必要
    if mcp_tools:
        # ツール名でツールを検索できるように辞書を作成
        tools_by_name = {tool.name: tool for tool in mcp_tools}
        
        def mcp_tool_node(state: State):
            """MCPツールを実行するカスタムノード（非同期ツールを同期的に実行）"""
            logger.info("🔧 [TOOLS] MCPツールノードの実行を開始します")
            
            try:
                messages = state.get("messages", [])
                last_message = messages[-1] if messages else None
                
                if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                    logger.warning("⚠️ [TOOLS] ツール呼び出しが見つかりませんでした")
                    return {"messages": []}
                
                tool_calls = last_message.tool_calls
                logger.info(f"🔧 [TOOLS] {len(tool_calls)}個のツール呼び出しを処理します")
                
                # 非同期でツールを実行する関数
                async def execute_tools_async():
                    results = []
                    for tool_call in tool_calls:
                        tool_name = tool_call.get("name", "unknown")
                        tool_args = tool_call.get("args", {})
                        tool_call_id = tool_call.get("id", "")
                        
                        logger.info(f"🔧 [TOOLS] ツール '{tool_name}' を実行します")
                        
                        if tool_name not in tools_by_name:
                            logger.error(f"❌ [TOOLS] 未知のツール名: {tool_name}")
                            results.append(ToolMessage(
                                content=f"エラー: ツール '{tool_name}' が見つかりません",
                                tool_call_id=tool_call_id
                            ))
                            continue
                        
                        tool = tools_by_name[tool_name]
                        
                        try:
                            # 非同期ツールを実行
                            if hasattr(tool, 'ainvoke'):
                                observation = await tool.ainvoke(tool_args)
                            elif hasattr(tool, 'invoke'):
                                # 同期的なツールの場合
                                observation = tool.invoke(tool_args)
                            else:
                                # コルーチンの場合
                                observation = await tool(tool_args)
                            
                            logger.info(f"✅ [TOOLS] ツール '{tool_name}' の実行が完了しました")
                            results.append(ToolMessage(
                                content=str(observation),
                                tool_call_id=tool_call_id
                            ))
                        except Exception as e:
                            logger.error(f"❌ [TOOLS] ツール '{tool_name}' の実行中にエラーが発生しました: {e}", exc_info=True)
                            error_message = f"エラーが発生しました: {str(e)}"
                            results.append(ToolMessage(
                                content=error_message,
                                tool_call_id=tool_call_id
                            ))
                    
                    return results
                
                # 非同期関数を同期的に実行
                results = asyncio.run(execute_tools_async())
                
                logger.info(f"✅ [TOOLS] MCPツールノードの実行が完了しました ({len(results)}個の結果)")
                return {"messages": results}
                
            except Exception as e:
                logger.error(f"❌ [TOOLS] MCPツールノードの実行中にエラーが発生しました: {e}", exc_info=True)
                raise
        
        graph.add_node("tools", mcp_tool_node)
        logger.info("✅ [AGENT] MCPツールノードを追加しました")
    
    graph.add_node("format_response", format_response_node)
    logger.info("✅ [AGENT] ノードの追加が完了しました")
    
    # エッジの追加
    graph.add_edge(START, "extract_query_intent")
    graph.add_edge("extract_query_intent", "execute_postgres_query")
    
    # MCPツールがある場合の条件分岐
    if mcp_tools:
        # execute_postgres_queryから、ツール呼び出しがある場合はtoolsノードへ、ない場合はformat_responseへ
        def should_continue(state: State) -> str:
            """ツール呼び出しがあるかどうかを判定"""
            messages = state.get("messages", [])
            last_message = messages[-1] if messages else None
            
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                logger.debug(f"🔧 [AGENT] ツール呼び出しを検出: {len(last_message.tool_calls)}個")
                return "tools"
            else:
                logger.debug("📝 [AGENT] ツール呼び出しなし、最終応答へ")
                return "format_response"
        
        graph.add_conditional_edges(
            "execute_postgres_query",
            should_continue,
            {
                "tools": "tools",
                "format_response": "format_response"
            }
        )
        graph.add_edge("tools", "format_response")  # ツール実行後は最終応答へ
    else:
        # MCPツールがない場合は直接format_responseへ
        graph.add_edge("execute_postgres_query", "format_response")
    
    graph.add_edge("format_response", END)
    logger.info("✅ [AGENT] エッジの追加が完了しました")
    
    # コンパイルしてモジュールレベルの変数に代入
    # langgraph.jsonでは "./my_agent/agent.py:graph" として参照可能
    logger.debug("🔨 [AGENT] グラフをコンパイルしています...")
    graph = graph.compile()
    logger.info("✅ [AGENT] エージェントの初期化が完了しました")
    
except Exception as e:
    logger.error(f"❌ [AGENT] エージェントの初期化中にエラーが発生しました: {e}", exc_info=True)
    raise


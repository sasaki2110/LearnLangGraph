"""
ノード関数の実装（MCPサーバー統合版）
"""
from langchain.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def extract_query_intent(state: State):
    """メッセージからクエリ意図を抽出するノード"""
    logger.info("📝 [EXTRACT] クエリ意図抽出を開始します")
    logger.debug(f"📊 [EXTRACT] 現在の状態: messages数={len(state.get('messages', []))}")
    
    try:
        # メッセージが存在する場合、最後のユーザーメッセージからクエリ意図を抽出
        if state.get("messages") and len(state["messages"]) > 0:
            # 最後のメッセージの内容をクエリ意図として使用
            last_message = state["messages"][-1]
            if hasattr(last_message, "content"):
                query_intent = last_message.content.strip()
            else:
                query_intent = str(last_message).strip()
            logger.info(f"✅ [EXTRACT] メッセージからクエリ意図を抽出しました: {query_intent[:50]}...")
        else:
            # メッセージがない場合は、既存のtopicを使用（後方互換性のため）
            query_intent = state.get("topic", "")
            logger.info(f"📝 [EXTRACT] 既存のクエリ意図を使用します: {query_intent[:50] if query_intent else 'なし'}...")
        
        return {"topic": query_intent}
    except Exception as e:
        logger.error(f"❌ [EXTRACT] クエリ意図抽出中にエラーが発生しました: {e}", exc_info=True)
        raise


def execute_postgres_query(state: State, llm_with_tools):
    """PostgreSQLクエリを実行するノード（MCPツールを使用）"""
    logger.info("🗄️ [POSTGRES] PostgreSQLクエリ実行を開始します")
    
    try:
        topic = state.get("topic", "")
        if not topic:
            logger.error("❌ [POSTGRES] トピックが設定されていません")
            raise ValueError("トピックが設定されていません")
        
        logger.info(f"📝 [POSTGRES] クエリ意図: {topic[:50]}...")
        
        # LLMにPostgreSQLクエリの生成と実行を依頼
        prompt = f"""以下のユーザーのリクエストに基づいて、適切なPostgreSQLクエリを実行してください。

ユーザーのリクエスト: {topic}

利用可能なMCPツールを使用して、データベースから情報を取得してください。
必要に応じて、テーブル一覧の取得、スキーマの確認、データの検索などを行ってください。"""
        
        messages = [
            SystemMessage(content="あなたはPostgreSQLデータベースの専門家です。ユーザーのリクエストに基づいて、適切なMCPツールを使用してデータベースから情報を取得してください。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [POSTGRES] LLM（MCPツール付き）を呼び出しています...")
        response = llm_with_tools.invoke(messages)
        
        # ツール呼び出しがある場合は、結果を取得
        query_result = ""
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.info(f"🔧 [POSTGRES] {len(response.tool_calls)}個のツール呼び出しを検出しました")
            # ツール呼び出しの結果は後続のノードで処理される
            query_result = f"ツール呼び出しを実行しました: {len(response.tool_calls)}個"
        else:
            # ツール呼び出しがない場合は、LLMの応答を使用
            query_result = response.content.strip() if hasattr(response, "content") else str(response)
            logger.info(f"✅ [POSTGRES] LLM応答を取得しました (長さ: {len(query_result)}文字)")
        
        logger.debug(f"📊 [POSTGRES] クエリ結果: {query_result[:100]}...")
        
        return {
            "query_result": query_result,
            "messages": [response]  # LLMの応答をmessagesに追加
        }
    except Exception as e:
        logger.error(f"❌ [POSTGRES] PostgreSQLクエリ実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def format_response(state: State, llm):
    """クエリ結果を整形して最終応答を生成するノード"""
    logger.info("📝 [FORMAT] 最終応答の生成を開始します")
    
    try:
        # messagesからToolMessageを探して、実際のクエリ結果を取得
        messages = state.get("messages", [])
        tool_results = []
        
        # ToolMessageを探す
        for msg in messages:
            if hasattr(msg, "type") and msg.type == "tool":
                # ToolMessageの場合
                if hasattr(msg, "content"):
                    tool_results.append(msg.content)
                    logger.debug(f"📊 [FORMAT] ToolMessageの内容を取得: {str(msg.content)[:100]}...")
            elif isinstance(msg, ToolMessage):
                # ToolMessageオブジェクトの場合
                if hasattr(msg, "content"):
                    tool_results.append(msg.content)
                    logger.debug(f"📊 [FORMAT] ToolMessageの内容を取得: {str(msg.content)[:100]}...")
        
        # クエリ結果を決定
        if tool_results:
            # ツール実行結果がある場合はそれを使用
            query_result = "\n\n".join([str(r) for r in tool_results])
            logger.info(f"✅ [FORMAT] ツール実行結果を取得しました (長さ: {len(query_result)}文字)")
        else:
            # ツール実行結果がない場合は、query_resultを使用
            query_result = state.get("query_result", "")
            if not query_result:
                logger.warning("⚠️ [FORMAT] クエリ結果が空です")
                query_result = "クエリ結果が取得できませんでした"
        
        topic = state.get("topic", "")
        if isinstance(topic, dict):
            # topicが辞書の場合は、contentを取得
            topic = topic.get("content", str(topic))
        elif not isinstance(topic, str):
            topic = str(topic)
        
        logger.info(f"📝 [FORMAT] トピック: {topic[:50]}...")
        logger.debug(f"📊 [FORMAT] クエリ結果: {query_result[:200]}...")
        
        prompt = f"""以下のPostgreSQLクエリの結果を、ユーザーにとって分かりやすい形式で説明してください。

ユーザーのリクエスト: {topic}
クエリ結果: {query_result}

結果を自然な日本語で説明してください。"""
        
        messages_for_llm = [
            SystemMessage(content="あなたはデータ分析の専門家です。データベースのクエリ結果を、ユーザーにとって分かりやすい形式で説明してください。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [FORMAT] LLMを呼び出しています...")
        response = llm.invoke(messages_for_llm)
        formatted_response = response.content.strip()
        
        logger.info(f"✅ [FORMAT] 最終応答の生成が完了しました (長さ: {len(formatted_response)}文字)")
        logger.debug(f"📝 [FORMAT] 生成された応答: {formatted_response[:100]}...")
        
        # Vercel AI SDKのチャットが表示できるように、AIMessageとしてmessagesに追加
        return {
            "messages": [AIMessage(content=formatted_response)]  # チャットUIで表示されるメッセージ
        }
    except Exception as e:
        logger.error(f"❌ [FORMAT] 最終応答生成中にエラーが発生しました: {e}", exc_info=True)
        raise


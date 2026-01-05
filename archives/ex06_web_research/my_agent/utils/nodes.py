"""
ノード関数の実装
"""
from langchain.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from my_agent.utils.state import State
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')

# モック検索結果データ（AI動向に関する情報、各企業を含む）
MOCK_SEARCH_RESULTS = [
    "OpenAIが最新のGPT-4モデルをリリースし、マルチモーダル機能を大幅に強化しました。GoogleもGemini Proの性能向上を発表しています。",
    "AnthropicはClaude 3.5 Sonnetを公開し、コード生成能力が向上しました。NVIDIAはAIチップの新製品を発表し、OracleもクラウドAIサービスを拡充しています。",
    "OpenAIとGoogleが生成AIの安全性向上に取り組んでいます。AnthropicはAIアライメント研究を進めており、NVIDIAはAI推論の高速化技術を開発中です。",
    "GoogleのGeminiとOpenAIのGPT-4が競争を激化させています。Anthropicは企業向けAIソリューションを強化し、NVIDIAはAIインフラの拡大を計画しています。OracleもAI統合プラットフォームを提供しています。",
    "OpenAIが新しいAIモデルの訓練方法を公開しました。Googleは検索エンジンにAI機能を統合し、AnthropicはAI安全性の研究を発表しています。NVIDIAとOracleはAIクラウドサービスを拡大しています。",
    "AnthropicのClaudeが企業市場でシェアを拡大しています。OpenAIはAPIの価格を下げ、GoogleはAI開発ツールを無料化しました。NVIDIAはAIチップの需要が高まっており、OracleはAIデータベース機能を強化しています。",
    "NVIDIAがAI推論用の新ハードウェアを発表しました。OpenAIとGoogleは多言語対応を強化し、AnthropicはAI倫理ガイドラインを策定しています。OracleはAI分析ツールをリリースしました。",
    "OpenAI、Google、AnthropicがAI安全性に関する共同声明を発表しました。NVIDIAはAIトレーニングの効率化技術を開発し、OracleはAI統合エンタープライズソリューションを提供しています。",
    "GoogleがAI研究の新成果を発表しました。OpenAIは開発者向けツールを拡充し、AnthropicはAIアシスタントの精度向上を実現しました。NVIDIAとOracleはAIインフラの共同開発を進めています。",
    "OpenAI、Google、Anthropic、NVIDIA、Oracleの5社がAI業界の標準化に向けて協力することを発表しました。各社は独自の強みを活かしながら、AI技術の普及を推進しています。"
]


@tool
def search_web(theme: str, call_count: int) -> str:
    """
    Web検索を実行するツール（モック実装）
    
    Args:
        theme: 検索テーマ
        call_count: 呼び出し回数（何番目の検索結果を返すかを決定）
        
    Returns:
        検索結果の文字列
    """
    logger.info(f"🔍 [TOOL] Web検索を実行します (テーマ: {theme}, 呼び出し回数: {call_count})")
    
    # call_countに基づいて検索結果を返す（配列の範囲内で循環）
    index = call_count % len(MOCK_SEARCH_RESULTS)
    result = MOCK_SEARCH_RESULTS[index]
    
    logger.info(f"✅ [TOOL] 検索結果を返却しました (インデックス: {index}, 長さ: {len(result)}文字)")
    logger.debug(f"📄 [TOOL] 検索結果: {result[:100]}...")
    
    return result


def extract_theme(state: State):
    """ユーザー指定テーマ抽出ノード"""
    logger.info("📝 [EXTRACT] テーマ抽出を開始します")
    logger.debug(f"📊 [EXTRACT] 現在の状態: messages数={len(state.get('messages', []))}")
    
    try:
        # メッセージが存在する場合、最後のユーザーメッセージからテーマを抽出
        if state.get("messages") and len(state["messages"]) > 0:
            # 最後のメッセージの内容をテーマとして使用
            last_message = state["messages"][-1]
            if hasattr(last_message, "content"):
                theme = last_message.content.strip()
            else:
                theme = str(last_message).strip()
            logger.info(f"✅ [EXTRACT] メッセージからテーマを抽出しました: {theme[:50]}...")
        else:
            # メッセージがない場合は、既存のthemeを使用
            theme = state.get("theme", "")
            logger.info(f"📝 [EXTRACT] 既存のテーマを使用します: {theme[:50] if theme else 'なし'}...")
        
        return {"theme": theme}
    except Exception as e:
        logger.error(f"❌ [EXTRACT] テーマ抽出中にエラーが発生しました: {e}", exc_info=True)
        raise


def think_and_action(state: State, llm_with_tools):
    """思考＋Actionノード（LLMを使用）"""
    logger.info("🤔 [THINK] 思考＋Actionを開始します")
    
    try:
        # llm_call_countをカウントアップ（Annotated[int, operator.add]なので増分を返す）
        current_count = state.get("llm_call_count", 0)
        new_count = current_count + 1
        
        logger.info(f"📊 [THINK] LLM呼び出し回数: {new_count} (増分: 1)")
        
        # themeが格納されていれば、WEB検索ツール利用を返却する
        theme = state.get("theme", "")
        if not theme:
            logger.warning("⚠️ [THINK] テーマが設定されていません")
            theme = "最近のAI動向"
        
        # システムメッセージとプロンプトを構築
        system_message = SystemMessage(
            content="あなたはWebリサーチエージェントです。ユーザーの質問に対して、必要に応じてWeb検索ツールを使用して情報を収集してください。\n\n重要な制約: 一度に1つのツール呼び出しのみを行ってください。複数のツールを同時に呼び出すことはできません。"
        )
        
        # メッセージ履歴を取得
        messages = state.get("messages", [])
        
        # 調査結果がある場合は、それも含める
        survey_results = state.get("survey_results", [])
        if survey_results:
            results_text = "\n\n".join([f"調査結果{i+1}: {result}" for i, result in enumerate(survey_results)])
            prompt = f"テーマ: {theme}\n\nこれまでの調査結果:\n{results_text}\n\n追加の情報が必要であれば、search_webツールを**1回だけ**使用してください。十分な情報があれば、回答を準備してください。\n\n注意: 一度に1つのツール呼び出しのみ可能です。"
        else:
            prompt = f"テーマ: {theme}\n\nこのテーマについて調査を開始してください。search_webツールを**1回だけ**使用して情報を収集してください。\n\n注意: 一度に1つのツール呼び出しのみ可能です。"
        
        human_message = HumanMessage(content=prompt)
        
        # LLMを呼び出し
        logger.debug("🤖 [THINK] LLMを呼び出しています...")
        response = llm_with_tools.invoke([system_message] + messages + [human_message])
        
        logger.info(f"✅ [THINK] 思考＋Actionが完了しました")
        logger.debug(f"📄 [THINK] レスポンス: {response.content[:100] if hasattr(response, 'content') else 'N/A'}...")
        
        return {
            "messages": [response],
            "llm_call_count": 1  # Annotated[int, operator.add]なので増分を返す
        }
    except Exception as e:
        logger.error(f"❌ [THINK] 思考＋Action中にエラーが発生しました: {e}", exc_info=True)
        raise


def tool_node(state: State):
    """ツールノード（指定されたツールを起動）"""
    logger.info("🔧 [TOOL_NODE] ツールノードを開始します")
    
    try:
        messages = state.get("messages", [])
        if not messages:
            logger.warning("⚠️ [TOOL_NODE] メッセージがありません")
            return {}
        
        last_message = messages[-1]
        
        # ツール呼び出しを確認
        if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
            logger.warning("⚠️ [TOOL_NODE] ツール呼び出しがありません")
            return {}
        
        tool_results = []
        survey_results = []  # 複数のツール呼び出し結果を累積
        theme = state.get("theme", "最近のAI動向")
        current_tool_count = state.get("tool_count", 0)
        tool_count_increment = 0  # この呼び出しで増加したtool_count
        
        # 一度に1つのツール呼び出しのみを処理（最初の1つだけ）
        tool_calls = last_message.tool_calls
        if len(tool_calls) > 1:
            logger.warning(f"⚠️ [TOOL_NODE] 複数のツール呼び出しが検出されました ({len(tool_calls)}個)。最初の1つだけを処理します。")
        
        # 最初のツール呼び出しのみを処理
        if tool_calls:
            tool_call = tool_calls[0]
            tool_name = tool_call.get("name", "")
            tool_args = tool_call.get("args", {})
            
            logger.info(f"🔧 [TOOL_NODE] ツール呼び出し: {tool_name} (引数: {tool_args})")
            
            if tool_name == "search_web":
                # リサーチツールを実行（現在のtool_countを使用）
                call_count = current_tool_count
                result = search_web.invoke({
                    "theme": theme,
                    "call_count": call_count
                })
                
                # 結果をsurvey_resultsに追加
                survey_results.append(result)
                
                # tool_countをカウントアップ
                tool_count_increment = 1
                new_tool_count = current_tool_count + tool_count_increment
                
                # ToolMessageを作成
                tool_message = ToolMessage(
                    content=result,
                    tool_call_id=tool_call.get("id", "")
                )
                tool_results.append(tool_message)
                
                logger.info(f"✅ [TOOL_NODE] ツール実行完了 (tool_count: {new_tool_count}, 調査結果数: {len(state.get('survey_results', [])) + len(survey_results)})")
        
        return {
            "messages": tool_results,
            "survey_results": survey_results,  # Annotated[list[str], operator.add]なのでリストを返す
            "tool_count": tool_count_increment  # Annotated[int, operator.add]なので増分を返す
        }
    except Exception as e:
        logger.error(f"❌ [TOOL_NODE] ツールノード実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def observe(state: State, llm):
    """観察ノード（調査結果が十分か判定）"""
    logger.info("👀 [OBSERVE] 観察ノードを開始します")
    
    try:
        survey_results = state.get("survey_results", [])
        if not survey_results:
            logger.warning("⚠️ [OBSERVE] 調査結果がありません")
            return {"is_sufficient": False}
        
        # 調査結果を結合
        results_text = "\n\n".join([f"調査結果{i+1}: {result}" for i, result in enumerate(survey_results)])
        
        # 十分の判定: OpenAI、Google、Anthropic、nvidia、oracleが言及されているか
        required_companies = ["OpenAI", "Google", "Anthropic", "nvidia", "oracle"]
        results_lower = results_text.lower()
        
        # 各企業が言及されているかチェック（全ての調査結果を結合した中で）
        mentioned_companies = [company for company in required_companies if company.lower() in results_lower]
        
        logger.info(f"📊 [OBSERVE] 言及されている企業: {mentioned_companies}")
        logger.info(f"📊 [OBSERVE] 必要な企業数: {len(required_companies)}, 言及されている企業数: {len(mentioned_companies)}")
        
        # 企業チェックで十分性を判定（全ての調査結果を結合した中に5社が含まれているか）
        all_companies_mentioned = len(mentioned_companies) >= len(required_companies)
        
        # 企業チェックで十分と判定された場合は、LLMを呼び出さずにTrueを返す
        if all_companies_mentioned:
            logger.info(f"✅ [OBSERVE] 企業チェックで十分と判定されました（全ての調査結果を結合した中に5社が含まれています）")
            return {"is_sufficient": True}
        
        # 企業チェックで不十分と判定された場合は、LLMに確認を依頼（念のため）
        # LLMに判定を依頼
        prompt = f"""以下の調査結果（複数の調査結果を結合した全体）を確認し、以下の5つの企業（OpenAI、Google、Anthropic、NVIDIA、Oracle）が**全ての調査結果を結合した中に**すべて言及されているかどうかを判定してください。

重要な注意点:
- 各調査結果を個別に判定するのではなく、**全ての調査結果を結合した全体**を見て判定してください
- 5つの企業が**全ての調査結果を結合した中に**すべて含まれていれば「十分」です
- 1つでも欠けていれば「不十分」です

調査結果（結合した全体）:
{results_text}

判定基準:
- 5つの企業（OpenAI、Google、Anthropic、NVIDIA、Oracle）が**全ての調査結果を結合した中に**すべて言及されている場合: 十分
- 1つでも欠けている場合: 不十分

「十分」または「不十分」のいずれかで回答してください。"""
        
        messages = [
            SystemMessage(content="あなたは調査結果の十分性を判定する専門家です。全ての調査結果を結合した全体を見て判定してください。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [OBSERVE] LLMを呼び出しています...")
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        # レスポンスから十分性を判定
        # 「不十分」を先にチェック（「不十分」には「十分」が含まれるため）
        response_lower = response_text.lower()
        is_insufficient = "不十分" in response_text or "insufficient" in response_lower
        is_sufficient_llm = "十分" in response_text or "sufficient" in response_lower
        
        if is_insufficient:
            # LLMが「不十分」と判定した場合はFalse
            is_sufficient = False
        elif is_sufficient_llm:
            # LLMが「十分」と判定した場合はTrue
            is_sufficient = True
        else:
            # LLMの判定が不明確な場合は、企業の言及チェックに基づく
            is_sufficient = all_companies_mentioned
        
        logger.info(f"✅ [OBSERVE] 判定完了: is_sufficient={is_sufficient}")
        logger.debug(f"📄 [OBSERVE] LLMレスポンス: {response_text}")
        
        return {"is_sufficient": is_sufficient}
    except Exception as e:
        logger.error(f"❌ [OBSERVE] 観察ノード実行中にエラーが発生しました: {e}", exc_info=True)
        raise


def format_final_answer(state: State, llm):
    """最終回答整形ノード（LLMを使用）"""
    logger.info("📝 [FORMAT] 最終回答整形を開始します")
    
    try:
        survey_results = state.get("survey_results", [])
        theme = state.get("theme", "最近のAI動向")
        llm_call_count = state.get("llm_call_count", 0)
        
        if not survey_results:
            logger.warning("⚠️ [FORMAT] 調査結果がありません")
            return {
                "messages": [AIMessage(content="調査結果がありませんでした。")]
            }
        
        # 調査結果を整形
        results_text = "\n\n".join([f"調査結果{i+1}: {result}" for i, result in enumerate(survey_results)])
        
        prompt = f"""以下の調査結果を基に、テーマ「{theme}」についての包括的なレポートを作成してください。

調査結果:
{results_text}

レポートは以下の形式で作成してください:
- 概要
- 主要な動向
- まとめ

簡潔で読みやすい形式で作成してください。"""
        
        # llm_call_count > 10 の場合は試行回数オーバーの旨も追加
        if llm_call_count > 10:
            prompt += "\n\n注意: 試行回数が上限に達したため、現在の調査結果を基にレポートを作成してください。"
        
        messages = [
            SystemMessage(content="あなたは調査結果を分かりやすくまとめる専門家です。"),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [FORMAT] LLMを呼び出しています...")
        response = llm.invoke(messages)
        final_answer = response.content.strip()
        
        # 試行回数オーバーの場合はメッセージに追加
        if llm_call_count > 10:
            final_answer += "\n\n※ 試行回数が上限に達したため、現在の調査結果を基にレポートを作成しました。"
        
        logger.info(f"✅ [FORMAT] 最終回答整形が完了しました (長さ: {len(final_answer)}文字)")
        logger.debug(f"📄 [FORMAT] 最終回答: {final_answer[:200]}...")
        
        return {
            "messages": [AIMessage(content=final_answer)]
        }
    except Exception as e:
        logger.error(f"❌ [FORMAT] 最終回答整形中にエラーが発生しました: {e}", exc_info=True)
        raise


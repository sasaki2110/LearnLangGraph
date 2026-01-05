"""
ノード関数の実装
"""
import json
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from my_agent.utils.state import SummaryState
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('nodes')


def extractor(state: SummaryState, llm):
    """ノードA (Extractor): 文章から重要な事実・トピックを抽出する"""
    logger.info("📝 [EXTRACTOR] 重要点抽出ノードを開始します")
    
    try:
        # 最初に最終メッセージの内容を、状態のraw_textへ格納
        messages = state.get("messages", [])
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, "content"):
                raw_text = last_message.content
            else:
                raw_text = str(last_message)
            logger.info(f"📄 [EXTRACTOR] 元の文書を取得しました (長さ: {len(raw_text)}文字)")
        else:
            raw_text = state.get("raw_text", "")
            if not raw_text:
                logger.warning("⚠️ [EXTRACTOR] メッセージもraw_textも見つかりませんでした")
                return {
                    "raw_text": "",
                    "extracted_items": []
                }
            logger.info(f"📄 [EXTRACTOR] 既存のraw_textを使用します (長さ: {len(raw_text)}文字)")
        
        # 文章から「重要な事実・トピック」を5〜10個、箇条書きのリストとして抽出
        prompt = f"""以下の文章から、重要な事実・トピックを5〜10個、箇条書きのリストとして抽出してください。
各項目は簡潔に、重要な情報を含むようにしてください。

文章:
{raw_text}

JSON形式で返してください。以下の形式で返してください：
{{
  "items": [
    "項目1",
    "項目2",
    ...
  ]
}}
"""
        
        messages_for_llm = [
            SystemMessage(content="You are a helpful assistant that extracts key facts and topics from text. Always respond in valid JSON format."),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [EXTRACTOR] LLMを呼び出しています...")
        response = llm.invoke(messages_for_llm)
        response_text = response.content.strip()
        
        logger.debug(f"💬 [EXTRACTOR] LLM応答: {response_text[:200]}...")
        
        # JSON形式でパース
        try:
            # JSONコードブロックを除去
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(response_text)
            extracted_items = parsed.get("items", [])
            
            logger.info(f"✅ [EXTRACTOR] {len(extracted_items)}個の重要点を抽出しました")
            logger.debug(f"📋 [EXTRACTOR] 抽出された項目: {extracted_items[:3]}...")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [EXTRACTOR] JSON解析エラー: {e}")
            logger.debug(f"💬 [EXTRACTOR] 解析できなかった応答: {response_text}")
            # フォールバック: 行ごとに分割してリストにする
            extracted_items = [line.strip() for line in response_text.split("\n") if line.strip() and not line.strip().startswith("#")]
            logger.info(f"⚠️ [EXTRACTOR] フォールバック処理: {len(extracted_items)}個の項目を抽出")
        
        return {
            "raw_text": raw_text,
            "extracted_items": extracted_items
        }
        
    except Exception as e:
        logger.error(f"❌ [EXTRACTOR] 重要点抽出中にエラーが発生しました: {e}", exc_info=True)
        raise


def refiner(state: SummaryState, llm):
    """ノードB (Refiner): 抽出されたリストを見て、重複を削り、重要度の高い順に並べ替える"""
    logger.info("✨ [REFINER] リスト精緻化ノードを開始します")
    
    try:
        extracted_items = state.get("extracted_items", [])
        
        if not extracted_items:
            logger.warning("⚠️ [REFINER] 抽出された項目がありません")
            return {
                "refined_items": []
            }
        
        logger.info(f"📋 [REFINER] {len(extracted_items)}個の項目を精緻化します")
        logger.debug(f"📋 [REFINER] 元の項目: {extracted_items[:3]}...")
        
        # 抽出されたリストを見て、重複を削り、重要度の高い順に並べ替える
        items_text = "\n".join([f"- {item}" for item in extracted_items])
        
        prompt = f"""以下の箇条書きリストから、重複を削除し、重要度の高い順に並べ替えてください。
重要な項目を優先し、類似した項目は統合してください。

元のリスト:
{items_text}

JSON形式で返してください。以下の形式で返してください：
{{
  "items": [
    "最重要項目1",
    "重要項目2",
    ...
  ]
}}
"""
        
        messages_for_llm = [
            SystemMessage(content="You are a helpful assistant that refines and prioritizes lists of items. Always respond in valid JSON format."),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [REFINER] LLMを呼び出しています...")
        response = llm.invoke(messages_for_llm)
        response_text = response.content.strip()
        
        logger.debug(f"💬 [REFINER] LLM応答: {response_text[:200]}...")
        
        # JSON形式でパース
        try:
            # JSONコードブロックを除去
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(response_text)
            refined_items = parsed.get("items", [])
            
            logger.info(f"✅ [REFINER] {len(refined_items)}個の項目に精緻化しました")
            logger.debug(f"📋 [REFINER] 精緻化された項目: {refined_items[:3]}...")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [REFINER] JSON解析エラー: {e}")
            logger.debug(f"💬 [REFINER] 解析できなかった応答: {response_text}")
            # フォールバック: 元のリストをそのまま使用
            refined_items = extracted_items
            logger.warning(f"⚠️ [REFINER] フォールバック処理: 元のリストを使用します")
        
        return {
            "refined_items": refined_items
        }
        
    except Exception as e:
        logger.error(f"❌ [REFINER] リスト精緻化中にエラーが発生しました: {e}", exc_info=True)
        raise


def writer(state: SummaryState, llm):
    """ノードC (Writer): 整理されたリストを元に、最終回答を作成する"""
    logger.info("📝 [WRITER] 最終回答作成ノードを開始します")
    
    try:
        refined_items = state.get("refined_items", [])
        
        if not refined_items:
            logger.warning("⚠️ [WRITER] 精緻化された項目がありません")
            return {
                "final_report": "要約する内容がありませんでした。"
            }
        
        logger.info(f"📋 [WRITER] {len(refined_items)}個の項目から最終回答を作成します")
        logger.debug(f"📋 [WRITER] 使用する項目: {refined_items[:3]}...")
        
        # 整理されたリストを元に、「忙しい人のための3行まとめ」と「詳細な箇条書き」の形式で最終回答を作る
        items_text = "\n".join([f"- {item}" for item in refined_items])
        
        prompt = f"""以下の箇条書きリストを元に、「忙しい人のための3行まとめ」と「詳細な箇条書き」の形式で最終回答を作成してください。

箇条書きリスト:
{items_text}

以下の形式で返してください：

【3行まとめ】
1. 最初の重要なポイント
2. 2番目の重要なポイント
3. 3番目の重要なポイント

【詳細な箇条書き】
- 詳細項目1
- 詳細項目2
...
"""
        
        messages_for_llm = [
            SystemMessage(content="You are a helpful assistant that creates clear, concise summaries. Format your response with a 3-line summary and detailed bullet points."),
            HumanMessage(content=prompt)
        ]
        
        logger.debug("🤖 [WRITER] LLMを呼び出しています...")
        response = llm.invoke(messages_for_llm)
        final_report = response.content.strip()
        
        logger.info(f"✅ [WRITER] 最終回答を作成しました (長さ: {len(final_report)}文字)")
        logger.debug(f"📄 [WRITER] 最終回答: {final_report[:200]}...")
        
        # 最終回答をmessagesにも追加（Vercel AI SDKなどで表示するため）
        return {
            "final_report": final_report,
            "messages": [AIMessage(content=final_report)]
        }
        
    except Exception as e:
        logger.error(f"❌ [WRITER] 最終回答作成中にエラーが発生しました: {e}", exc_info=True)
        raise


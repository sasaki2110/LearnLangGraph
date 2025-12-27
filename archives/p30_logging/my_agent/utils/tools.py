"""
ツール定義
"""
from langchain.tools import tool
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('tools')


@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`.
    
    Args:
        a: First int
        b: Second int
    """
    logger.info(f"🔢 [TOOL] multiply を実行します: {a} × {b}")
    try:
        result = a * b
        logger.info(f"✅ [TOOL] multiply の結果: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [TOOL] multiply の実行中にエラーが発生しました: {e}", exc_info=True)
        raise


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`.
    
    Args:
        a: First int
        b: Second int
    """
    logger.info(f"🔢 [TOOL] add を実行します: {a} + {b}")
    try:
        result = a + b
        logger.info(f"✅ [TOOL] add の結果: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [TOOL] add の実行中にエラーが発生しました: {e}", exc_info=True)
        raise


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`.
    
    Args:
        a: First int
        b: Second int
    """
    logger.info(f"🔢 [TOOL] divide を実行します: {a} ÷ {b}")
    try:
        if b == 0:
            logger.error(f"❌ [TOOL] divide: ゼロ除算エラー ({a} ÷ {b})")
            raise ValueError("ゼロで除算することはできません")
        result = a / b
        logger.info(f"✅ [TOOL] divide の結果: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [TOOL] divide の実行中にエラーが発生しました: {e}", exc_info=True)
        raise


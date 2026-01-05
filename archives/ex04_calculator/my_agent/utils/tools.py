"""
ツール定義
"""
from langchain.tools import tool
from my_agent.utils.logging_config import get_logger

# ロガーを取得
logger = get_logger('tools')


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
def mul(a: int, b: int) -> int:
    """Multiply `a` and `b`.
    
    Args:
        a: First int
        b: Second int
    """
    logger.info(f"🔢 [TOOL] mul を実行します: {a} × {b}")
    try:
        result = a * b
        logger.info(f"✅ [TOOL] mul の結果: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [TOOL] mul の実行中にエラーが発生しました: {e}", exc_info=True)
        raise


@tool
def sub(a: int, b: int) -> int:
    """Subtract `b` from `a`.
    
    Args:
        a: First int
        b: Second int
    """
    logger.info(f"🔢 [TOOL] sub を実行します: {a} - {b}")
    try:
        result = a - b
        logger.info(f"✅ [TOOL] sub の結果: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [TOOL] sub の実行中にエラーが発生しました: {e}", exc_info=True)
        raise


@tool
def div(a: int, b: int) -> float:
    """Divide `a` by `b`.
    
    Args:
        a: First int
        b: Second int
    """
    logger.info(f"🔢 [TOOL] div を実行します: {a} ÷ {b}")
    try:
        if b == 0:
            logger.error(f"❌ [TOOL] div: ゼロ除算エラー ({a} ÷ {b})")
            raise ValueError("ゼロで除算することはできません")
        result = a / b
        logger.info(f"✅ [TOOL] div の結果: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ [TOOL] div の実行中にエラーが発生しました: {e}", exc_info=True)
        raise


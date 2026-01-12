"""
ロボットアーム用のツール関数
"""
from typing import Dict, Tuple
from my_agent.utils.logging_config import get_logger

logger = get_logger('tools')

# 仮想的な物体の位置データ（実際の実装では、データベースやセンサーから取得）
OBJECT_POSITIONS: Dict[str, Tuple[float, float, float]] = {
    # 日本語名
    "赤いコップ": (10.0, 20.0, 5.0),
    "青いトレイ": (30.0, 40.0, 5.0),
    "ボール": (15.0, 25.0, 3.0),
    "箱": (25.0, 35.0, 8.0),
    # 英語名（マッピング用）
    "red cup": (10.0, 20.0, 5.0),
    "blue tray": (30.0, 40.0, 5.0),
    "ball": (15.0, 25.0, 3.0),
    "box": (25.0, 35.0, 8.0),
    # その他のバリエーション
    "赤いコップ": (10.0, 20.0, 5.0),
    "赤コップ": (10.0, 20.0, 5.0),
    "青いトレイ": (30.0, 40.0, 5.0),
    "青トレイ": (30.0, 40.0, 5.0),
}

# 物体名のマッピング（英語→日本語、その他のバリエーション）
ITEM_NAME_MAPPING: Dict[str, str] = {
    "red cup": "赤いコップ",
    "blue tray": "青いトレイ",
    "ball": "ボール",
    "box": "箱",
}


def get_object_position(item_name: str) -> Tuple[float, float, float]:
    """
    指定した物体の3次元座標を返す
    
    Args:
        item_name: 物体の名前（日本語または英語）
        
    Returns:
        物体の位置 (x, y, z)
    """
    logger.info(f"🔍 [TOOL] 物体の位置を取得: {item_name}")
    
    # まず直接検索
    if item_name in OBJECT_POSITIONS:
        position = OBJECT_POSITIONS[item_name]
        logger.info(f"✅ [TOOL] 物体 '{item_name}' の位置: ({position[0]}, {position[1]}, {position[2]})")
        return position
    
    # マッピングを試す（英語名→日本語名）
    if item_name in ITEM_NAME_MAPPING:
        mapped_name = ITEM_NAME_MAPPING[item_name]
        logger.info(f"🔄 [TOOL] 物体名をマッピング: '{item_name}' -> '{mapped_name}'")
        if mapped_name in OBJECT_POSITIONS:
            position = OBJECT_POSITIONS[mapped_name]
            logger.info(f"✅ [TOOL] 物体 '{mapped_name}' の位置: ({position[0]}, {position[1]}, {position[2]})")
            return position
    
    # 部分一致で検索（大文字小文字を無視）
    item_name_lower = item_name.lower()
    for key, position in OBJECT_POSITIONS.items():
        if item_name_lower in key.lower() or key.lower() in item_name_lower:
            logger.info(f"🔄 [TOOL] 部分一致で物体を発見: '{item_name}' -> '{key}'")
            logger.info(f"✅ [TOOL] 物体 '{key}' の位置: ({position[0]}, {position[1]}, {position[2]})")
            return position
    
    # デフォルト位置を返す（物体が見つからない場合）
    default_position = (0.0, 0.0, 0.0)
    logger.warning(f"⚠️ [TOOL] 物体 '{item_name}' が見つかりません。デフォルト位置を返します: {default_position}")
    logger.warning(f"⚠️ [TOOL] 利用可能な物体: {list(OBJECT_POSITIONS.keys())}")
    return default_position


def move_arm_to(x: float, y: float, z: float) -> bool:
    """
    アームの先端（グリッパー）を指定座標へ移動させる
    
    Args:
        x: X座標
        y: Y座標
        z: Z座標
        
    Returns:
        移動が成功したかどうか
    """
    logger.info(f"🤖 [TOOL] アームを移動: ({x}, {y}, {z})")
    
    # 実際の実装では、ロボットアームのAPIを呼び出す
    # ここではシミュレーションとして、常に成功を返す
    logger.info(f"✅ [TOOL] アームの移動が完了しました")
    return True


def control_gripper(action: str) -> bool:
    """
    グリッパーの開閉を行う
    
    Args:
        action: "open" または "close"
        
    Returns:
        操作が成功したかどうか
    """
    logger.info(f"🤖 [TOOL] グリッパーを操作: {action}")
    
    if action not in ["open", "close"]:
        logger.error(f"❌ [TOOL] 無効なアクション: {action} (open または close である必要があります)")
        return False
    
    # 実際の実装では、グリッパーのAPIを呼び出す
    # ここではシミュレーションとして、常に成功を返す
    logger.info(f"✅ [TOOL] グリッパーの操作が完了しました: {action}")
    return True

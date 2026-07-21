"""读取已验证的道具瞄点组，并按检索到的战术进行匹配。"""

from functools import lru_cache
import json
from pathlib import Path

from .config import UTILITY_LINEUPS_DIR


MANIFEST_PATH = UTILITY_LINEUPS_DIR / "manifest.json"


@lru_cache
def load_lineups() -> tuple[dict, ...]:
    """加载素材清单；网页服务重启后会读取最新的 manifest。"""
    with MANIFEST_PATH.open(encoding="utf-8") as file:
        lineups = json.load(file)

    if not isinstance(lineups, list):
        raise ValueError("utility_lineups/manifest.json 的根节点必须是数组")

    return tuple(lineups)


def find_verified_lineups(evidence: list[dict]) -> list[dict]:
    """只返回与当前检索证据对应、且已验证的道具图组。"""
    strategy_ids = {
        item.get("metadata", {}).get("strategy_id")
        for item in evidence
        if item.get("metadata", {}).get("strategy_id")
    }

    return [
        lineup
        for lineup in load_lineups()
        if lineup.get("verification_status") == "verified"
        and lineup.get("strategy_id") in strategy_ids
    ]


def image_path(image: dict) -> Path:
    """将 manifest 中的相对图片路径解析为本地绝对路径。"""
    return UTILITY_LINEUPS_DIR / image["path"]

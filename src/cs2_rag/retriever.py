import chromadb

from .config import CHROMA_DIR, COLLECTION_NAME
from .models import get_embedding_model, get_reranker


# 每项依次为：Chroma 元数据值、显示名称、可识别的中英文别名。
ACTIVE_DUTY_MAPS = (
    ("ancient", "Ancient（远古遗迹）", ("ancient", "远古遗迹", "荒古遗尘")),
    ("anubis", "Anubis（阿努比斯）", ("anubis", "阿努比斯")),
    ("cache", "Cache（死城之谜）", ("cache", "死城之谜")),
    ("dust2", "Dust II（炙热沙城 II）", ("dust2", "dust 2", "dust ii", "炙热沙城", "沙二", "沙2", "d2")),
    ("inferno", "Inferno（炼狱小镇）", ("inferno", "炼狱小镇")),
    ("mirage", "Mirage（荒漠迷城）", ("mirage", "荒漠迷城", "米垃圾")),
    ("nuke", "Nuke（核子危机）", ("nuke", "核子危机", "核子")),
)

MAP_ALIASES = {
    alias.casefold(): map_name
    for map_name, _, aliases in ACTIVE_DUTY_MAPS
    for alias in aliases
}
MAP_LABELS = {
    map_name: label
    for map_name, label, _ in ACTIVE_DUTY_MAPS
}


def normalize_map(value: str) -> str | None:
    """将编号以外的地图名称或别名转为文档 metadata 中使用的标准值。"""
    return MAP_ALIASES.get(value.strip().casefold())


def detect_map(query: str) -> str | None:
    """从自然语言问题中识别地图；长别名优先，避免短词抢先匹配。"""
    normalized_query = query.casefold()
    for alias in sorted(MAP_ALIASES, key=len, reverse=True):
        if alias in normalized_query:
            return MAP_ALIASES[alias]
    return None


def get_map_label(map_name: str) -> str:
    return MAP_LABELS[map_name]


def resolve_map(query: str, map_filter: str | None = None) -> str | None:
    """显式选择优先；未选择时才从问题中自动识别。"""
    if map_filter is not None:
        normalized = normalize_map(map_filter)
        if normalized is None:
            raise ValueError("不是有效的当前服役地图")
        return normalized
    return detect_map(query)


def retrieve(
    query: str,
    top_k: int = 4,
    candidates: int = 12,
    map_filter: str | None = None,
) -> list[dict]:
    """按地图过滤后召回候选片段，再以交叉编码器重排。"""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    embedding_model = get_embedding_model()
    query_embedding = embedding_model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    map_name = resolve_map(query, map_filter)
    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": candidates,
        "include": ["documents", "metadatas", "distances"],
    }
    if map_name:
        # 在向量召回前过滤，其他地图的资料不会进入重排或大模型上下文。
        query_args["where"] = {"map": map_name}

    result = collection.query(**query_args)
    items = [
        {
            "text": text,
            "metadata": metadata,
            "distance": distance,
        }
        for text, metadata, distance in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        )
    ]

    # 地图暂无资料时，不再调用空列表的重排模型。
    if not items:
        return []

    reranker = get_reranker()
    scores = reranker.predict([(query, item["text"]) for item in items])

    for item, score in zip(items, scores):
        item["rerank_score"] = float(score)

    return sorted(items, key=lambda item: item["rerank_score"], reverse=True)[:top_k]

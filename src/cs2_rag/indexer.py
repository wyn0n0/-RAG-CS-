import argparse
import chromadb

from .config import CHROMA_DIR, COLLECTION_NAME, TACTICS_DIR
from .documents import split_markdown
from .models import get_embedding_model


def get_collection(rebuild: bool):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def is_changed(chunk, stored_metadata: dict | None) -> bool:
    """判断正文或当前记录的元数据是否需要写回向量库。"""
    if not stored_metadata:
        return True

    return any(
        stored_metadata.get(key) != value
        for key, value in chunk.metadata.items()
    )


def sync_file(collection, path, model) -> tuple[int, int]:
    """仅写入新增/修改的片段，并删除该文件中已不存在的旧片段。"""
    source_id = path.relative_to(TACTICS_DIR).as_posix()
    chunks = split_markdown(path, source_id=source_id)

    existing = collection.get(
        where={"source": source_id},
        include=["metadatas"],
    )
    existing_metadata_by_id = {
        chunk_id: metadata
        for chunk_id, metadata in zip(existing["ids"], existing["metadatas"])
    }

    # 空文件也应清理它在库中遗留的所有片段。
    if not chunks:
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
        return 0, len(existing["ids"])

    changed_chunks = [
        chunk
        for chunk in chunks
        if is_changed(chunk, existing_metadata_by_id.get(chunk.id))
    ]

    if changed_chunks:
        texts = [chunk.text for chunk in changed_chunks]
        embeddings = model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        collection.upsert(
            ids=[chunk.id for chunk in changed_chunks],
            documents=texts,
            metadatas=[chunk.metadata for chunk in changed_chunks],
            embeddings=embeddings,
        )

    current_ids = {chunk.id for chunk in chunks}
    stale_ids = list(set(existing["ids"]) - current_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)

    return len(changed_chunks), len(stale_ids)


def build_index(rebuild: bool = False) -> None:
    collection = get_collection(rebuild)
    model = get_embedding_model()

    paths = list(TACTICS_DIR.rglob("*.md"))
    if not paths:
        raise ValueError(f"未找到战术文件：{TACTICS_DIR}")

    current_sources = set()

    for path in paths:
        source_id = path.relative_to(TACTICS_DIR).as_posix()
        current_sources.add(source_id)

        changed, deleted = sync_file(collection, path, model)
        print(f"已同步：{source_id}（新增/更新 {changed} 个，删除过期 {deleted} 个）")

    # 删除磁盘上已不存在的文档残留
    existing = collection.get(include=["metadatas"])
    old_sources = {
        metadata.get("source_id", metadata.get("source"))
        for metadata in existing["metadatas"]
        if metadata and ("source_id" in metadata or "source" in metadata)
    }

    for source_id in old_sources - current_sources:
        # 兼容旧版仅保存 source 的片段与新版保存 source_id 的片段。
        collection.delete(where={"source": source_id})
        print(f"已删除失效资料：{source_id}")

    print(f"知识库同步完成，共 {collection.count()} 个片段。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="删除整个向量库后重新构建",
    )
    args = parser.parse_args()
    build_index(rebuild=args.rebuild)

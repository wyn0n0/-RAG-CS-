from dataclasses import dataclass
from pathlib import Path
import hashlib
import re


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict


def make_hash(text: str) -> str:
    """返回文本的 SHA-256 哈希，用于判断片段内容是否变化。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_chunk_id(source_id: str, section_index: int, chunk_index: int) -> str:
    """生成稳定 ID：只依赖文档位置，不依赖正文内容。"""
    return make_hash(f"{source_id}:{section_index}:{chunk_index}")


def parse_markdown(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    metadata = {"source": path.name}

    if text.startswith("---\n"):
        _, header, text = text.split("---", maxsplit=2)
        for line in header.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", maxsplit=1)
                metadata[key.strip()] = value.strip()

    return metadata, text.strip()


def split_markdown(
    path: Path,
    source_id: str,
    max_chars: int = 700,
) -> list[Chunk]:
    base_metadata, content = parse_markdown(path)
    base_metadata["source"] = source_id
    base_metadata["source_id"] = source_id

    sections = re.split(r"(?=^#{1,3}\s)", content, flags=re.MULTILINE)
    chunks = []

    for section_index, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        for chunk_index, char_offset in enumerate(range(0, len(section), max_chars)):
            part = section[char_offset: char_offset + max_chars]

            chunk_id = make_chunk_id(source_id, section_index, chunk_index)

            metadata = {
                **base_metadata,
                "section": str(section_index),
                "chunk_index": chunk_index,
                "content_hash": make_hash(part),
            }
            chunks.append(Chunk(
                id=chunk_id,
                text=part,
                metadata=metadata,
            ))

    return chunks

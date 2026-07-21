from functools import lru_cache
from sentence_transformers import SentenceTransformer, CrossEncoder
from .config import EMBEDDING_MODEL, RERANK_MODEL


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache
def get_reranker() -> CrossEncoder:
    return CrossEncoder(RERANK_MODEL)
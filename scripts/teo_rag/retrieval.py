"""Chroma vector retrieval with hierarchical tier search."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    DETAIL_TOP_K,
    EMBEDDING_MODEL,
    SUMMARY_TOP_K,
)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source: str
    tier: str
    block: str
    section: str
    score: float
    metadata: dict


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_query(query: str) -> list[float]:
    vec = _model().encode([f"query: {query}"], normalize_embeddings=True)
    return vec[0].tolist()


def embed_passages(texts: list[str]) -> list[list[float]]:
    prefixed = [f"passage: {t}" for t in texts]
    vecs = _model().encode(prefixed, normalize_embeddings=True, show_progress_bar=len(texts) > 50)
    return [v.tolist() for v in vecs]


def get_collection(recreate: bool = False):
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )
    if recreate:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _hits_from_result(result: dict[str, Any]) -> list[RetrievedChunk]:
    chunks: list[RetrievedChunk] = []
    if not result or not result.get("ids"):
        return chunks
    for i, chunk_id in enumerate(result["ids"][0]):
        meta = result["metadatas"][0][i] or {}
        dist = result["distances"][0][i] if result.get("distances") else 0.0
        score = 1.0 - float(dist)
        chunks.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                text=result["documents"][0][i],
                source=meta.get("source", ""),
                tier=meta.get("tier", ""),
                block=meta.get("block", ""),
                section=meta.get("section", ""),
                score=score,
                metadata=meta,
            )
        )
    return chunks


def search_tier(query: str, tier: str, top_k: int) -> list[RetrievedChunk]:
    collection = get_collection()
    if collection.count() == 0:
        return []
    qvec = embed_query(query)
    result = collection.query(
        query_embeddings=[qvec],
        n_results=top_k,
        where={"tier": tier},
        include=["documents", "metadatas", "distances"],
    )
    return _hits_from_result(result)


def hierarchical_search(
    query: str,
    mode: str = "vector",
    summary_k: int = SUMMARY_TOP_K,
    detail_k: int = DETAIL_TOP_K,
) -> list[RetrievedChunk]:
    if mode == "summary":
        return search_tier(query, "summary", summary_k + detail_k)

    summary_hits = search_tier(query, "summary", summary_k) if mode in ("vector", "hybrid") else []
    detail_hits = search_tier(query, "detail", detail_k)

    seen: set[str] = set()
    merged: list[RetrievedChunk] = []
    for hit in sorted(summary_hits + detail_hits, key=lambda h: h.score, reverse=True):
        key = f"{hit.source}::{hit.section}"
        if key in seen:
            continue
        seen.add(key)
        merged.append(hit)
    return merged

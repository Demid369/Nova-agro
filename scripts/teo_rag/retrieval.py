"""Chroma + BM25 hybrid retrieval with optional cross-encoder rerank."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import CrossEncoder, SentenceTransformer

from .bm25_index import bm25_search
from .config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    DETAIL_TOP_K,
    EMBEDDING_MODEL,
    HYBRID_BM25_WEIGHT,
    HYBRID_VECTOR_WEIGHT,
    RERANK_CANDIDATES,
    RERANK_TOP_K,
    RERANKER_MODEL,
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
    vector_score: float = 0.0
    bm25_score: float = 0.0


@lru_cache(maxsize=1)
def _embed_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _reranker() -> CrossEncoder:
    return CrossEncoder(RERANKER_MODEL)


def embed_query(query: str) -> list[float]:
    vec = _embed_model().encode([f"query: {query}"], normalize_embeddings=True)
    return vec[0].tolist()


def embed_passages(texts: list[str]) -> list[list[float]]:
    prefixed = [f"passage: {t}" for t in texts]
    vecs = _embed_model().encode(prefixed, normalize_embeddings=True, show_progress_bar=len(texts) > 50)
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
                vector_score=score,
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


def _chunk_from_meta(chunk_id: str, meta: dict, text: str, score: float, **scores) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=text,
        source=meta.get("source", ""),
        tier=meta.get("tier", ""),
        block=meta.get("block", ""),
        section=meta.get("section", ""),
        score=score,
        vector_score=scores.get("vector_score", 0.0),
        bm25_score=scores.get("bm25_score", 0.0),
        metadata=meta,
    )


def hybrid_merge(query: str, vector_hits: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
    bm25_hits = bm25_search(query, top_k=RERANK_CANDIDATES)
    by_id: dict[str, RetrievedChunk] = {}

    for h in vector_hits:
        by_id[h.chunk_id] = RetrievedChunk(
            chunk_id=h.chunk_id,
            text=h.text,
            source=h.source,
            tier=h.tier,
            block=h.block,
            section=h.section,
            score=HYBRID_VECTOR_WEIGHT * h.vector_score,
            vector_score=h.vector_score,
            bm25_score=0.0,
            metadata=h.metadata,
        )

    for cid, bm_sc, meta in bm25_hits:
        text = meta.get("text", "")
        if cid in by_id:
            hit = by_id[cid]
            hit.bm25_score = bm_sc
            hit.score = HYBRID_VECTOR_WEIGHT * hit.vector_score + HYBRID_BM25_WEIGHT * bm_sc
        else:
            by_id[cid] = _chunk_from_meta(
                cid, meta, text,
                HYBRID_BM25_WEIGHT * bm_sc,
                bm25_score=bm_sc,
            )

    merged = sorted(by_id.values(), key=lambda h: h.score, reverse=True)
    return merged[: max(top_k, RERANK_CANDIDATES)]


def rerank(query: str, hits: list[RetrievedChunk], top_k: int = RERANK_TOP_K) -> list[RetrievedChunk]:
    if not hits:
        return []
    if len(hits) <= top_k:
        return hits
    pairs = [(query, h.text[:2000]) for h in hits]
    scores = _reranker().predict(pairs)
    ranked = sorted(zip(hits, scores), key=lambda x: float(x[1]), reverse=True)
    out: list[RetrievedChunk] = []
    for hit, sc in ranked[:top_k]:
        hit.score = float(sc)
        out.append(hit)
    return out


def hierarchical_search(
    query: str,
    mode: str = "vector",
    summary_k: int = SUMMARY_TOP_K,
    detail_k: int = DETAIL_TOP_K,
    *,
    use_hybrid: bool = True,
    use_rerank: bool = True,
) -> list[RetrievedChunk]:
    if mode == "summary":
        hits = search_tier(query, "summary", summary_k + detail_k)
    else:
        summary_hits = search_tier(query, "summary", summary_k) if mode in ("vector", "hybrid") else []
        detail_hits = search_tier(query, "detail", detail_k)
        hits = summary_hits + detail_hits

    seen: set[str] = set()
    deduped: list[RetrievedChunk] = []
    for hit in sorted(hits, key=lambda h: h.score, reverse=True):
        key = f"{hit.source}::{hit.section}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)

    if use_hybrid and deduped:
        deduped = hybrid_merge(query, deduped, summary_k + detail_k)

    if use_rerank and deduped:
        deduped = rerank(query, deduped, top_k=detail_k if mode != "summary" else summary_k + detail_k)

    return deduped[: summary_k + detail_k]

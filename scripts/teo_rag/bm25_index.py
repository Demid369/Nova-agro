"""BM25 lexical index over TEO chunks."""

from __future__ import annotations

import json
import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from .chunks import collect_chunks
from .config import BM25_INDEX_PATH, CHUNK_INDEX_PATH, ROOT


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zа-яё0-9]+", text.lower())


@lru_cache(maxsize=1)
def _bm25_bundle() -> tuple[BM25Okapi, list[str], list[dict]]:
    if BM25_INDEX_PATH.exists() and CHUNK_INDEX_PATH.exists():
        meta = json.loads(BM25_INDEX_PATH.read_text(encoding="utf-8"))
        idx_mtime = CHUNK_INDEX_PATH.stat().st_mtime
        if meta.get("chunk_index_mtime") == idx_mtime:
            ids = meta["ids"]
            corpus = meta["tokenized_corpus"]
            metas = meta["metadatas"]
            return BM25Okapi(corpus), ids, metas

    chunks = collect_chunks()
    ids = [c.chunk_id for c in chunks]
    tokenized = [_tokenize(c.text) for c in chunks]
    metas = [c.to_metadata() | {"text": c.text} for c in chunks]

    BM25_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "chunk_index_mtime": CHUNK_INDEX_PATH.stat().st_mtime if CHUNK_INDEX_PATH.exists() else 0,
        "ids": ids,
        "tokenized_corpus": tokenized,
        "metadatas": metas,
    }
    BM25_INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return BM25Okapi(tokenized), ids, metas


def bm25_search(query: str, top_k: int = 24) -> list[tuple[str, float, dict]]:
    bm25, ids, metas = _bm25_bundle()
    scores = bm25.get_scores(_tokenize(query))
    if not len(scores):
        return []
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    max_s = ranked[0][1] if ranked and ranked[0][1] > 0 else 1.0
    out: list[tuple[str, float, dict]] = []
    for i, sc in ranked:
        if sc <= 0:
            continue
        out.append((ids[i], sc / max_s, metas[i]))
    return out


def invalidate_bm25_cache() -> None:
    _bm25_bundle.cache_clear()
    if BM25_INDEX_PATH.exists():
        BM25_INDEX_PATH.unlink()

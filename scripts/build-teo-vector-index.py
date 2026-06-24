#!/usr/bin/env python3
"""Build Chroma vector index from TEO markdown corpus."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from teo_rag.chunks import collect_chunks  # noqa: E402
from teo_rag.config import (  # noqa: E402
    CHROMA_DIR,
    CHUNK_INDEX_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    MANIFEST_PATH,
    OUT_DIR,
)
from teo_rag.retrieval import embed_passages, get_collection  # noqa: E402

BATCH_SIZE = 32


def main() -> int:
    chunks = collect_chunks()
    if not chunks:
        print("No chunks collected.", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    collection = get_collection(recreate=True)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for chunk in chunks:
        ids.append(chunk.chunk_id)
        documents.append(chunk.text)
        metadatas.append(chunk.to_metadata())

    print(f"Embedding {len(chunks)} chunks with {EMBEDDING_MODEL}...")
    for start in range(0, len(documents), BATCH_SIZE):
        end = start + BATCH_SIZE
        batch_ids = ids[start:end]
        batch_docs = documents[start:end]
        batch_meta = metadatas[start:end]
        embeddings = embed_passages(batch_docs)
        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_meta,
            embeddings=embeddings,
        )
        print(f"  indexed {min(end, len(documents))}/{len(documents)}")

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "collection": COLLECTION_NAME,
        "embedding_model": EMBEDDING_MODEL,
        "chunk_count": len(chunks),
        "summary_count": sum(1 for c in chunks if c.tier == "summary"),
        "detail_count": sum(1 for c in chunks if c.tier == "detail"),
        "excluded_trade_stat": "files matching *-табл-*, в-*-гг-* skipped at chunk stage",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    index = [
        {
            "chunk_id": c.chunk_id,
            "source": c.source,
            "tier": c.tier,
            "block": c.block,
            "section": c.section,
            "word_count": c.word_count,
        }
        for c in chunks
    ]
    CHUNK_INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Done: {len(chunks)} chunks → {CHROMA_DIR}")
    print(f"Manifest: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

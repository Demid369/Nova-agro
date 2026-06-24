"""Paths and constants for TEO hybrid RAG."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS_SUMMARY = ROOT / "docs" / "graphify-corpus"
CORPUS_DETAIL = ROOT / "docs" / "teo"
OUT_DIR = ROOT / "teo-rag-out"
CHROMA_DIR = OUT_DIR / "chroma"
MANIFEST_PATH = OUT_DIR / "manifest.json"
CHUNK_INDEX_PATH = OUT_DIR / "chunk-index.json"
MEMORY_PATH = OUT_DIR / "memory.jsonl"
GRAPH_PATH = ROOT / "graphify-out" / "graph.json"

COLLECTION_NAME = "teo_moya_mechta"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# Chunking
MAX_CHUNK_CHARS = 4000
CHUNK_OVERLAP = 300
MARKET_FILE_HINT = "04-rynok"

# Retrieval defaults
SUMMARY_TOP_K = 3
DETAIL_TOP_K = 8
HYBRID_TOP_K = 6

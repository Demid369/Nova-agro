"""Paths and constants for TEO hybrid RAG."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS_SUMMARY = ROOT / "docs" / "graphify-corpus"
CORPUS_DETAIL = ROOT / "docs" / "teo"
SCENARIOS_DIR = ROOT / "docs" / "scenarios"
OUT_DIR = ROOT / "teo-rag-out"
CHROMA_DIR = OUT_DIR / "chroma"
MANIFEST_PATH = OUT_DIR / "manifest.json"
CHUNK_INDEX_PATH = OUT_DIR / "chunk-index.json"
KPI_PATH = OUT_DIR / "kpi.json"
BM25_INDEX_PATH = OUT_DIR / "bm25-index.json"
MEMORY_PATH = OUT_DIR / "memory.jsonl"
GRAPH_PATH = ROOT / "graphify-out" / "graph.json"

COLLECTION_NAME = "teo_moya_mechta"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"

# Chunking
MAX_CHUNK_CHARS = 4000
CHUNK_OVERLAP = 300
MARKET_FILE_HINT = "04-rynok"

# Retrieval defaults
SUMMARY_TOP_K = 3
DETAIL_TOP_K = 8
HYBRID_TOP_K = 6
RERANK_CANDIDATES = 24
RERANK_TOP_K = 8
HYBRID_VECTOR_WEIGHT = 0.55
HYBRID_BM25_WEIGHT = 0.45

"""Paths and constants for TEO hybrid RAG."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS_SUMMARY = ROOT / "docs" / "graphify-corpus"
CORPUS_DETAIL = ROOT / "docs" / "teo"
TEO_TABLES = ROOT / "docs" / "teo-tables"
TEO_TABLES_CRITICAL = TEO_TABLES / "critical"
TEO_TABLES_MANIFEST = TEO_TABLES / "manifest.json"
TEO_LAND_BUDGET = TEO_TABLES / "land-budget.yaml"
SCENARIOS_DIR = ROOT / "docs" / "scenarios"
OUT_DIR = ROOT / "teo-rag-out"
CHROMA_DIR = OUT_DIR / "chroma"
MANIFEST_PATH = OUT_DIR / "manifest.json"
CHUNK_INDEX_PATH = OUT_DIR / "chunk-index.json"
KPI_PATH = OUT_DIR / "kpi.json"
KPI_BASELINE_PATH = OUT_DIR / "kpi-baseline.json"
BM25_INDEX_PATH = OUT_DIR / "bm25-index.json"
MEMORY_PATH = OUT_DIR / "memory.jsonl"
ACTIVE_SCENARIO_PATH = OUT_DIR / "active-scenario.json"
GRAPH_PATH = ROOT / "graphify-out" / "graph.json"
GRAPH_BASELINE_PATH = ROOT / "graphify-out" / "graph.baseline.json"
SCENARIO_GRAPH_DIR = ROOT / "graphify-out" / "scenarios"
MODEL_CACHE_DIR = OUT_DIR / "model-cache"

COLLECTION_NAME = "teo_moya_mechta"
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANKER_CACHE_DIR = MODEL_CACHE_DIR / "reranker"

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


def resolve_graph_path() -> Path:
    """Return scenario-specific graph when an active what-if scenario is set."""
    if ACTIVE_SCENARIO_PATH.exists():
        try:
            import json

            active = json.loads(ACTIVE_SCENARIO_PATH.read_text(encoding="utf-8"))
            sid = active.get("scenario_id", "baseline")
            if sid and sid != "baseline":
                candidate = SCENARIO_GRAPH_DIR / f"{sid}.json"
                if candidate.exists():
                    return candidate
        except Exception:
            pass
    return GRAPH_PATH

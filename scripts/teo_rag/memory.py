"""Validated Q&A memory (JSONL)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import MEMORY_PATH


@dataclass
class MemoryHit:
    query: str
    answer: str
    mode: str
    citations: list[dict]
    score: float


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def load_entries(path: Path = MEMORY_PATH) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def find_memory_hit(query: str, threshold: float = 0.92) -> MemoryHit | None:
    qn = _normalize(query)
    best: MemoryHit | None = None
    best_score = 0.0
    for entry in load_entries():
        eq = _normalize(entry.get("query", ""))
        if not eq:
            continue
        if eq == qn:
            return MemoryHit(
                query=entry["query"],
                answer=entry.get("answer", ""),
                mode=entry.get("mode", "memory"),
                citations=entry.get("citations", []),
                score=1.0,
            )
        # simple token overlap
        q_tokens = set(qn.split())
        e_tokens = set(eq.split())
        if not q_tokens:
            continue
        overlap = len(q_tokens & e_tokens) / len(q_tokens)
        if overlap > best_score:
            best_score = overlap
            best = MemoryHit(
                query=entry["query"],
                answer=entry.get("answer", ""),
                mode=entry.get("mode", "memory"),
                citations=entry.get("citations", []),
                score=overlap,
            )
    if best and best_score >= threshold:
        return best
    return None


def save_memory(
    query: str,
    answer: str,
    mode: str,
    citations: list[dict],
    path: Path = MEMORY_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "answer": answer,
        "mode": mode,
        "citations": citations,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

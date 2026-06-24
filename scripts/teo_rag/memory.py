"""Validated Q&A memory (JSONL) + graphify save-result."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import MEMORY_PATH, ROOT


@dataclass
class MemoryHit:
    query: str
    answer: str
    mode: str
    citations: list[dict]
    score: float
    validated: bool = True


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
        if entry.get("validated") is False:
            continue
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
                validated=entry.get("validated", True),
            )
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
                validated=entry.get("validated", True),
            )
    if best and best_score >= threshold:
        return best
    return None


def save_memory(
    query: str,
    answer: str,
    mode: str,
    citations: list[dict],
    *,
    validated: bool = True,
    validation: dict | None = None,
    synthesis_method: str | None = None,
    path: Path = MEMORY_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "answer": answer,
        "mode": mode,
        "citations": citations,
        "validated": validated,
        "validation": validation,
        "synthesis_method": synthesis_method,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_graphify_result(
    query: str,
    answer: str,
    query_type: str = "query",
    graph_nodes: list[str] | None = None,
    memory_dir: Path | None = None,
) -> bool:
    """Mirror answer to graphify memory via save-result CLI."""
    graphify = shutil.which("graphify")
    if not graphify:
        return False

    cmd = [
        graphify,
        "save-result",
        "--question",
        query,
        "--answer",
        answer[:8000],
        "--type",
        query_type,
    ]
    nodes = [n for n in (graph_nodes or []) if n][:8]
    if nodes:
        cmd.extend(["--nodes", *nodes])
    if memory_dir:
        cmd.extend(["--memory-dir", str(memory_dir)])

    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    return proc.returncode == 0


def persist_validated(
    query: str,
    answer: str,
    mode: str,
    citations: list[dict],
    validation: dict,
    *,
    synthesis_method: str | None = None,
    graph_nodes: list[str] | None = None,
    to_graphify: bool = True,
    to_teo_memory: bool = True,
) -> dict:
    """Save to teo memory + optionally graphify when validation passed."""
    saved = {"teo_memory": False, "graphify": False}
    if not validation.get("valid", False):
        return saved

    if to_teo_memory:
        save_memory(
            query=query,
            answer=answer,
            mode=mode,
            citations=citations,
            validated=True,
            validation=validation,
            synthesis_method=synthesis_method,
        )
        saved["teo_memory"] = True

    if to_graphify:
        saved["graphify"] = save_graphify_result(
            query=query,
            answer=answer,
            query_type=mode if mode in ("query", "path_query", "explain") else "query",
            graph_nodes=graph_nodes,
        )
    return saved

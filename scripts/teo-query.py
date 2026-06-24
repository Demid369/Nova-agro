#!/usr/bin/env python3
"""Unified TEO query CLI: graph + vector + memory hybrid."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from teo_rag.graph_client import run_graph_query  # noqa: E402
from teo_rag.memory import find_memory_hit, save_memory  # noqa: E402
from teo_rag.retrieval import hierarchical_search  # noqa: E402
from teo_rag.router import classify_query  # noqa: E402


def chunk_citation(hit) -> dict:
    return {
        "type": "chunk",
        "source": hit.source,
        "section": hit.section,
        "block": hit.block,
        "tier": hit.tier,
        "chunk_id": hit.chunk_id,
        "score": round(hit.score, 4),
        "excerpt": hit.text[:400].replace("\n", " "),
    }


def graph_citations(result) -> list[dict]:
    cites = []
    for node in result.nodes[:12]:
        cites.append(
            {
                "type": "graph_node",
                "label": node.label,
                "source": node.source,
                "community": node.community,
            }
        )
    for edge in result.edges[:8]:
        cites.append(
            {
                "type": "graph_edge",
                "source_node": edge.source,
                "relation": edge.relation,
                "target_node": edge.target,
            }
        )
    return cites


def format_vector_answer(query: str, hits) -> str:
    if not hits:
        return "Релевантные фрагменты не найдены. Запустите: python scripts/build-teo-vector-index.py"
    lines = [f"Запрос: {query}", "", "Релевантные фрагменты (иерархия summary → detail):", ""]
    for i, hit in enumerate(hits, 1):
        lines.append(f"{i}. [{hit.tier}] {hit.section} — {hit.source} (score {hit.score:.3f})")
        excerpt = hit.text[:600].strip()
        if len(hit.text) > 600:
            excerpt += "…"
        lines.append(excerpt)
        lines.append("")
    lines.append("Используйте citations для точных ссылок на источник.")
    return "\n".join(lines)


def format_graph_answer(query: str, result) -> str:
    lines = [f"Запрос (graph): {query}"]
    if result.traversal:
        lines.append(f"Traversal: {result.traversal}")
    lines.append("")
    if result.nodes:
        lines.append("Узлы:")
        for node in result.nodes[:15]:
            comm = f" [{node.community}]" if node.community else ""
            lines.append(f"  • {node.label} ← {node.source}{comm}")
    if result.edges:
        lines.append("")
        lines.append("Связи:")
        for edge in result.edges[:12]:
            lines.append(f"  • {edge.source} --{edge.relation}--> {edge.target}")
    if not result.nodes and result.raw:
        lines.append(result.raw)
    return "\n".join(lines)


def format_hybrid_answer(query: str, graph_result, vector_hits) -> str:
    parts = [format_graph_answer(query, graph_result), "", "---", "", format_vector_answer(query, vector_hits)]
    return "\n".join(parts)


def run_query(query: str, mode: str = "auto", budget: int = 2500, json_out: bool = False) -> dict:
    memory = find_memory_hit(query)
    if memory and mode in ("auto", "memory"):
        payload = {
            "query": query,
            "mode": "memory",
            "reason": f"memory hit (score {memory.score:.2f})",
            "answer": memory.answer,
            "citations": memory.citations,
        }
        if json_out:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(memory.answer)
        return payload

    decision = classify_query(query, force_mode=None if mode == "auto" else mode)
    route_mode = decision.mode

    citations: list[dict] = []
    answer = ""

    if route_mode == "graph":
        graph = run_graph_query(query, budget=budget)
        citations = graph_citations(graph)
        answer = format_graph_answer(query, graph)
    elif route_mode == "vector":
        hits = hierarchical_search(query, mode="vector")
        citations = [chunk_citation(h) for h in hits]
        answer = format_vector_answer(query, hits)
    elif route_mode == "summary":
        hits = hierarchical_search(query, mode="summary")
        citations = [chunk_citation(h) for h in hits]
        answer = format_vector_answer(query, hits)
    else:  # hybrid
        graph = run_graph_query(query, budget=budget)
        hits = hierarchical_search(query, mode="hybrid")
        citations = graph_citations(graph) + [chunk_citation(h) for h in hits]
        answer = format_hybrid_answer(query, graph, hits)

    payload = {
        "query": query,
        "mode": route_mode,
        "reason": decision.reason,
        "scores": decision.scores,
        "answer": answer,
        "citations": citations,
    }
    if json_out:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(answer)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="TEO hybrid query (graph + vector + memory)")
    parser.add_argument("query", help="Вопрос по ТЭО")
    parser.add_argument(
        "--mode",
        choices=["auto", "graph", "vector", "hybrid", "summary", "memory"],
        default="auto",
        help="Маршрут запроса",
    )
    parser.add_argument("--budget", type=int, default=2500, help="Budget для graphify query")
    parser.add_argument("--json", action="store_true", help="JSON-вывод")
    parser.add_argument("--save-memory", action="store_true", help="Сохранить ответ в memory.jsonl")
    args = parser.parse_args()

    payload = run_query(args.query, mode=args.mode, budget=args.budget, json_out=args.json)

    if args.save_memory:
        save_memory(
            query=args.query,
            answer=payload.get("answer", ""),
            mode=payload.get("mode", "auto"),
            citations=payload.get("citations", []),
        )
        if not args.json:
            print("\n[memory] сохранено в teo-rag-out/memory.jsonl")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

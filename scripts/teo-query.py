#!/usr/bin/env python3
"""Unified TEO query CLI: graph + vector + memory hybrid."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from teo_rag.context import EvidenceBundle  # noqa: E402
from teo_rag.graph_client import GraphResult, run_graph_query  # noqa: E402
from teo_rag.kpi import format_kpi_answer, match_block  # noqa: E402
from teo_rag.memory import find_memory_hit, persist_validated  # noqa: E402
from teo_rag.retrieval import RetrievedChunk, hierarchical_search  # noqa: E402
from teo_rag.router import classify_query  # noqa: E402
from teo_rag.scenarios import compare_scenarios, resolve_scenario_compare  # noqa: E402
from teo_rag.synthesis import synthesize as run_synthesis  # noqa: E402
from teo_rag.validator import validate_answer  # noqa: E402


def chunk_citation(hit: RetrievedChunk) -> dict:
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


def graph_citations(result: GraphResult) -> list[dict]:
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


def format_vector_answer(query: str, hits: list[RetrievedChunk]) -> str:
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


def format_graph_answer(query: str, result: GraphResult) -> str:
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


def format_hybrid_answer(query: str, graph_result: GraphResult, vector_hits: list[RetrievedChunk]) -> str:
    parts = [format_graph_answer(query, graph_result), "", "---", "", format_vector_answer(query, vector_hits)]
    return "\n".join(parts)


def retrieve(
    query: str,
    route_mode: str,
    budget: int,
) -> tuple[str, list[dict], EvidenceBundle, GraphResult | None, list[RetrievedChunk]]:
    graph: GraphResult | None = None
    hits: list[RetrievedChunk] = []
    citations: list[dict] = []
    raw_answer = ""

    if route_mode == "graph":
        graph = run_graph_query(query, budget=budget)
        citations = graph_citations(graph)
        raw_answer = format_graph_answer(query, graph)
    elif route_mode == "scenario":
        pair = resolve_scenario_compare(query) or ("baseline", "poultry-variant")
        raw_answer = compare_scenarios(pair[0], pair[1])
        citations = [{"type": "scenario", "baseline": pair[0], "variant": pair[1]}]
    elif route_mode == "vector":
        hits = hierarchical_search(query, mode="vector")
        citations = [chunk_citation(h) for h in hits]
        raw_answer = format_vector_answer(query, hits)
    elif route_mode == "summary":
        hits = hierarchical_search(query, mode="summary")
        citations = [chunk_citation(h) for h in hits]
        raw_answer = format_vector_answer(query, hits)
    else:
        graph = run_graph_query(query, budget=budget)
        hits = hierarchical_search(query, mode="hybrid")
        citations = graph_citations(graph) + [chunk_citation(h) for h in hits]
        raw_answer = format_hybrid_answer(query, graph, hits)

    bundle = EvidenceBundle(query=query, chunks=hits, graph=graph)
    return raw_answer, citations, bundle, graph, hits


def run_query(
    query: str,
    mode: str = "auto",
    budget: int = 2500,
    json_out: bool = False,
    *,
    synthesize: str | None = None,
    validate: bool = False,
) -> dict:
    memory = find_memory_hit(query)
    if memory and mode in ("auto", "memory"):
        payload = {
            "query": query,
            "mode": "memory",
            "reason": f"memory hit (score {memory.score:.2f})",
            "answer": memory.answer,
            "citations": memory.citations,
            "validation": {"valid": True, "from_memory": True},
        }
        if json_out:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(memory.answer)
        return payload

    decision = classify_query(query, force_mode=None if mode == "auto" else mode)
    route_mode = decision.mode

    if not synthesize and route_mode in ("auto", "vector", "hybrid"):
        q_lower = query.lower()
        block_hit = match_block(query)
        kpi_on_hybrid = route_mode == "hybrid" and block_hit and any(
            w in q_lower for w in ("сколько", "тонн", "npv", "irr", "capex", "окупаем")
        )
        if route_mode != "hybrid" or kpi_on_hybrid:
            kpi_hit = format_kpi_answer(query)
            if kpi_hit:
                kpi_answer, kpi_citations = kpi_hit
                payload = {
                    "query": query,
                    "mode": "kpi",
                    "reason": "structured KPI layer (fast path)",
                    "scores": decision.scores,
                    "answer": kpi_answer,
                    "raw_answer": None,
                    "citations": kpi_citations,
                    "synthesis": None,
                    "validation": {"valid": True, "from_kpi": True},
                }
                if json_out:
                    print(json.dumps(payload, ensure_ascii=False, indent=2))
                else:
                    print(kpi_answer)
                return payload

    raw_answer, citations, bundle, graph, _hits = retrieve(query, route_mode, budget)

    answer = raw_answer
    synthesis_meta: dict | None = None
    if synthesize:
        syn = run_synthesis(bundle, method=synthesize)
        answer = syn.answer
        synthesis_meta = {"method": syn.method, "model": syn.model}

    validation_result = None
    if validate or synthesize:
        validation_result = validate_answer(answer, bundle.corpus_text(), check_claims=True)
        if not validation_result.valid and synthesis_meta:
            synthesis_meta["rejected"] = True
            synthesis_meta["unsupported_numbers"] = validation_result.unsupported

    payload = {
        "query": query,
        "mode": route_mode,
        "reason": decision.reason,
        "scores": decision.scores,
        "answer": answer,
        "raw_answer": raw_answer if synthesize else None,
        "citations": citations,
        "synthesis": synthesis_meta,
        "validation": validation_result.to_dict() if validation_result else None,
    }

    if json_out:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(answer)
        if validation_result and not validation_result.valid:
            parts = []
            if validation_result.unsupported:
                parts.append(f"числа: {', '.join(validation_result.unsupported)}")
            if validation_result.unsupported_claims:
                parts.append(f"claims: {len(validation_result.unsupported_claims)}")
            print(f"\n[validation FAILED] {'; '.join(parts)}", file=sys.stderr)
        elif validation_result and validation_result.valid and validate:
            print("\n[validation OK]", file=sys.stderr)

    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="TEO hybrid query (graph + vector + memory)")
    parser.add_argument("query", help="Вопрос по ТЭО")
    parser.add_argument(
        "--mode",
        choices=["auto", "graph", "vector", "hybrid", "summary", "memory", "scenario"],
        default="auto",
        help="Маршрут запроса",
    )
    parser.add_argument("--budget", type=int, default=2500, help="Budget для graphify query")
    parser.add_argument("--json", action="store_true", help="JSON-вывод")
    parser.add_argument(
        "--synthesize",
        nargs="?",
        const="extractive",
        choices=["extractive", "llm"],
        help="Синтез ответа только из retrieved (extractive по умолчанию, llm — Gemini)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Проверить числа в ответе против evidence corpus",
    )
    parser.add_argument(
        "--save-memory",
        action="store_true",
        help="Сохранить в teo-rag-out/memory.jsonl + graphify save-result (только если validation OK)",
    )
    parser.add_argument(
        "--force-save",
        action="store_true",
        help="Сохранить в memory даже при failed validation",
    )
    args = parser.parse_args()

    validate = args.validate or bool(args.synthesize) or args.save_memory

    payload = run_query(
        args.query,
        mode=args.mode,
        budget=args.budget,
        json_out=args.json,
        synthesize=args.synthesize,
        validate=validate,
    )

    if args.save_memory:
        validation = payload.get("validation") or {}
        can_save = validation.get("valid", False) or args.force_save
        if can_save:
            graph_nodes = [
                c["label"]
                for c in payload.get("citations", [])
                if c.get("type") == "graph_node"
            ]
            syn = payload.get("synthesis") or {}
            saved = persist_validated(
                query=args.query,
                answer=payload.get("answer", ""),
                mode=payload.get("mode", "auto"),
                citations=payload.get("citations", []),
                validation=validation if validation else {"valid": args.force_save},
                synthesis_method=syn.get("method"),
                graph_nodes=graph_nodes,
                to_graphify=validation.get("valid", False) or args.force_save,
                to_teo_memory=True,
            )
            if not args.json:
                flags = [k for k, v in saved.items() if v]
                print(f"\n[memory] сохранено: {', '.join(flags) or 'none'}")
        elif not args.json:
            print(
                "\n[memory] НЕ сохранено: validation failed. Используйте --force-save для принудительного.",
                file=sys.stderr,
            )
            return 2

    if payload.get("validation") and not payload["validation"].get("valid") and validate:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

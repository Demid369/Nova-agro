#!/usr/bin/env python3
"""Собрать стартовый knowledge graph Graphify для ТЭО «МОЯ МЕЧТА».

Запуск:
  uv tool run --from graphifyy==0.8.49 python scripts/build-teo-graph.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"
CORPUS = ROOT / "docs" / "graphify-corpus"


def node(nid: str, label: str, source: str, ftype: str = "concept") -> dict:
    return {
        "id": nid,
        "label": label,
        "file_type": ftype,
        "source_file": str(source),
        "source_location": None,
    }


def edge(src: str, tgt: str, relation: str, source: str, conf: str = "EXTRACTED", score: float = 1.0) -> dict:
    return {
        "source": src,
        "target": tgt,
        "relation": relation,
        "confidence": conf,
        "confidence_score": score,
        "source_file": str(source),
        "source_location": None,
        "weight": 1.0,
    }


def build_extraction() -> dict:
    s = str(CORPUS / "00-summary.md")
    p = str(CORPUS / "03-proizvodstvo-i-tehnologii.md")
    f = str(CORPUS / "05-finansy-i-byudzhet.md")

    nodes = [
        node("summary_moya_mechta", "ООО «МОЯ МЕЧТА»", s, "concept"),
        node("summary_kherson", "Херсонская область", s, "concept"),
        node("summary_invest_100b", "Инвестиции 100 млрд руб.", s, "concept"),
        node("summary_revenue_71b", "Выручка 71,4 млрд руб./год", s, "concept"),
        node("summary_jobs_5000", "5000 рабочих мест", s, "concept"),
        node("summary_land_135k", "Земельный фонд 135 000 га", s, "concept"),
        node("summary_zero_meat_cost", "Нулевая себестоимость мяса", s, "rationale"),
        node("prod_rabbit", "Кролиководство 7 000 т/год", p, "concept"),
        node("prod_greenhouse", "Тепличный комплекс 100 га", p, "concept"),
        node("prod_livestock", "Животноводство КРС/МРС", p, "concept"),
        node("prod_fish", "Рыбоводство белуга", p, "concept"),
        node("prod_oil", "Масложировой комбинат", p, "concept"),
        node("prod_biogas", "Биогазовая установка 20 МВт·ч", p, "concept"),
        node("prod_solar", "Солнечные панели 50 МВт·ч", p, "concept"),
        node("prod_leather", "Переработка кожи 600 000 м²", p, "concept"),
        node("prod_gelatin", "Халяльный желатин 6 000 т", p, "concept"),
        node("prod_caviar", "Чёрная икра 20 т/год", p, "concept"),
        node("prod_feed", "Комбикормовый завод", p, "concept"),
        node("tech_meneghin", "Meneghin Srl", p, "concept"),
        node("tech_sint", "SINT Technologies", p, "concept"),
        node("tech_hocevar", "HOCEVAR", p, "concept"),
        node("tech_aia", "AIA Associazione Italiana Allevatori", p, "concept"),
        node("fin_npv_rabbit", "NPV кролиководство 2,78 млрд", f, "concept"),
        node("fin_npv_greenhouse", "NPV теплицы 33,86 млрд", f, "concept"),
        node("fin_npv_livestock", "NPV животноводство 28,92 млрд", f, "concept"),
        node("fin_npv_fish", "NPV рыбоводство 3,86 млрд", f, "concept"),
        node("fin_npv_oil", "NPV масложировой 26,83 млрд", f, "concept"),
        node("market_export", "Экспорт 10,2 млрд руб.", s, "concept"),
        node("market_halal", "Сертификат Халяль", p, "concept"),
    ]

    edges = [
        edge("summary_moya_mechta", "summary_kherson", "conceptually_related_to", s),
        edge("summary_moya_mechta", "summary_invest_100b", "conceptually_related_to", s),
        edge("summary_moya_mechta", "summary_revenue_71b", "conceptually_related_to", s),
        edge("summary_moya_mechta", "summary_jobs_5000", "conceptually_related_to", s),
        edge("summary_moya_mechta", "summary_land_135k", "conceptually_related_to", s),
        edge("summary_zero_meat_cost", "prod_leather", "rationale_for", s, "INFERRED", 0.85),
        edge("summary_zero_meat_cost", "prod_gelatin", "rationale_for", s, "INFERRED", 0.85),
        edge("summary_moya_mechta", "prod_rabbit", "conceptually_related_to", s),
        edge("summary_moya_mechta", "prod_greenhouse", "conceptually_related_to", s),
        edge("summary_moya_mechta", "prod_livestock", "conceptually_related_to", s),
        edge("summary_moya_mechta", "prod_fish", "conceptually_related_to", s),
        edge("summary_moya_mechta", "prod_oil", "conceptually_related_to", s),
        edge("prod_rabbit", "tech_meneghin", "references", p),
        edge("prod_livestock", "tech_sint", "references", p),
        edge("prod_gelatin", "tech_hocevar", "references", p),
        edge("prod_livestock", "tech_aia", "references", p),
        edge("prod_livestock", "prod_biogas", "shares_data_with", p, "INFERRED", 0.75),
        edge("prod_livestock", "prod_leather", "shares_data_with", p, "EXTRACTED", 1.0),
        edge("prod_livestock", "prod_gelatin", "shares_data_with", p, "EXTRACTED", 1.0),
        edge("prod_livestock", "prod_feed", "conceptually_related_to", p),
        edge("prod_fish", "prod_caviar", "conceptually_related_to", p),
        edge("prod_oil", "prod_feed", "conceptually_related_to", p, "INFERRED", 0.75),
        edge("prod_biogas", "prod_solar", "semantically_similar_to", p, "INFERRED", 0.7),
        edge("summary_invest_100b", "fin_npv_rabbit", "conceptually_related_to", f),
        edge("summary_invest_100b", "fin_npv_greenhouse", "conceptually_related_to", f),
        edge("summary_invest_100b", "fin_npv_livestock", "conceptually_related_to", f),
        edge("summary_invest_100b", "fin_npv_fish", "conceptually_related_to", f),
        edge("summary_invest_100b", "fin_npv_oil", "conceptually_related_to", f),
        edge("summary_revenue_71b", "market_export", "conceptually_related_to", s),
        edge("prod_gelatin", "market_halal", "conceptually_related_to", p),
        edge("prod_caviar", "market_export", "conceptually_related_to", p, "INFERRED", 0.85),
        edge("prod_leather", "market_export", "conceptually_related_to", p, "INFERRED", 0.85),
    ]

    return {"nodes": nodes, "edges": edges, "hyperedges": [], "input_tokens": 0, "output_tokens": 0}


def main() -> int:
    sys.path.insert(0, str(Path.home() / ".local/share/uv/tools/graphifyy"))
    try:
        from graphify.build import build
        from graphify.cluster import cluster, score_all
        from graphify.analyze import god_nodes, surprising_connections, suggest_questions
        from graphify.report import generate
        from graphify.export import to_json, to_html
    except ImportError:
        import graphify  # noqa: F401
        from graphify.build import build
        from graphify.cluster import cluster, score_all
        from graphify.analyze import god_nodes, surprising_connections, suggest_questions
        from graphify.report import generate
        from graphify.export import to_json, to_html

    extraction = build_extraction()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "extraction-seed.json").write_text(
        json.dumps(extraction, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    G = build([extraction], root=ROOT)
    communities = cluster(G)
    labels = {cid: f"Community {cid}" for cid in communities}
    gods = god_nodes(G)
    surprises = surprising_connections(G, communities)
    cohesion = score_all(G, communities)
    questions = suggest_questions(G, communities, labels)

    report = generate(
        G,
        communities,
        cohesion,
        labels,
        gods,
        surprises,
        {"warning": "Стартовый граф из сводки ТЭО. Для полного графа: /graphify docs/graphify-corpus"},
        {"input": 0, "output": 0},
        str(ROOT),
        suggested_questions=questions,
    )
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    to_json(G, communities, str(OUT / "graph.json"), community_labels=labels)
    to_html(G, communities, str(OUT / "graph.html"), community_labels=labels)

    manifest = {
        "version": 1,
        "root": str(ROOT),
        "files": {str(p): {"md5": "seed"} for p in CORPUS.glob("*.md")},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / ".graphify_python").write_text(sys.executable, encoding="utf-8")

    print(f"graphify-out: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Report: {OUT / 'GRAPH_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

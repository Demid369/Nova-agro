#!/usr/bin/env python3
"""Семантическая экстракция ТЭО: доменная онтология + слияние со структурным графом."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"
STRUCTURAL = OUT / "extraction-full.json"
SEMANTIC = OUT / "extraction-semantic.json"
MERGED = OUT / "extraction-merged.json"

SRC_SUMMARY = "docs/graphify-corpus/00-summary.md"
SRC_INTRO = "docs/graphify-corpus/01-vvedenie-i-resume.md"
SRC_PROD = "docs/graphify-corpus/03-proizvodstvo-i-tehnologii.md"
SRC_MARKET = "docs/graphify-corpus/04-rynok-i-analitika.md"
SRC_FIN = "docs/graphify-corpus/05-finansy-i-byudzhet.md"
SRC_RISK = "docs/graphify-corpus/06-vyvody-i-riski.md"


def norm_id(stem: str, label: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", stem.lower())[:40].strip("_")
    ent = re.sub(r"[^a-z0-9]+", "_", label.lower())[:80].strip("_")
    return f"{base}_{ent}" if ent else base


def node(nid: str, label: str, source: str, ftype: str = "concept") -> dict:
    return {
        "id": nid,
        "label": label,
        "file_type": ftype,
        "source_file": source,
        "source_location": None,
    }


def edge(
    src: str,
    tgt: str,
    relation: str,
    source: str,
    conf: str = "INFERRED",
    score: float = 0.85,
) -> dict | None:
    if src == tgt:
        return None
    return {
        "source": src,
        "target": tgt,
        "relation": relation,
        "confidence": conf,
        "confidence_score": score,
        "source_file": source,
        "source_location": None,
        "weight": 1.0,
    }


def build_semantic_ontology() -> tuple[list[dict], list[dict], list[dict]]:
    """Курированные семантические связи из бизнес-логики ТЭО."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    hyperedges: list[dict] = []

    def add(label: str, source: str, ftype: str = "concept") -> str:
        stem = Path(source).stem
        nid = norm_id(stem, label)
        if nid not in nodes:
            nodes[nid] = node(nid, label, source, ftype)
        return nid

    def link(a: str, b: str, rel: str, source: str, conf: str = "INFERRED", score: float = 0.85):
        ea, eb = add(a, source), add(b, source)
        e = edge(ea, eb, rel, source, conf, score)
        if e:
            edges.append(e)

    # --- Ядро проекта ---
    hub = add("ООО «МОЯ МЕЧТА»", SRC_SUMMARY)
    region = add("Херсонская область", SRC_SUMMARY)
    link("ООО «МОЯ МЕЧТА»", "Херсонская область", "conceptually_related_to", SRC_SUMMARY, "EXTRACTED", 1.0)

    blocks = [
        ("Кролиководство", SRC_SUMMARY, 12.0, "7 000 т мяса/год"),
        ("Тепличный комплекс 100 га", SRC_SUMMARY, 34.5, "18 400 т овощей"),
        ("Животноводство КРС/МРС", SRC_SUMMARY, 40.0, "20 000 т мяса"),
        ("Рыбоводство белуга", SRC_SUMMARY, 8.0, "20 т икры"),
        ("Масложировой комбинат", SRC_SUMMARY, 5.5, "50 000 т масла"),
        ("Комбикормовый завод", SRC_INTRO, None, "262 800 т/год"),
        ("Биогазовая установка 20 МВт·ч", SRC_SUMMARY, None, None),
        ("Солнечные панели 50 МВт·ч", SRC_SUMMARY, None, None),
        ("Убойный цех", SRC_INTRO, None, "525,6 тыс. КРС + 4,38 млн МРС"),
        ("Завод халяльного желатина", SRC_INTRO, None, "6 000 т/год"),
        ("Кожевенный завод", SRC_INTRO, None, "600 тыс. м² кожи"),
        ("Завод кровяной муки", SRC_INTRO, None, "3 000 т/год"),
        ("Завод переработки молока", SRC_INTRO, None, "50 000 т молока"),
        ("Генетический центр КРС", SRC_INTRO, None, "4 000 голов"),
        ("Генетический центр Фризон", SRC_INTRO, None, "6 000 голов"),
    ]
    block_ids = []
    for name, src, *_ in blocks:
        bid = add(name, src)
        block_ids.append(bid)
        e = edge(hub, bid, "conceptually_related_to", src, "EXTRACTED", 1.0)
        if e:
            edges.append(e)

    # --- Ключевая бизнес-модель (rationale_for) ---
    free_slaughter = add("Бесплатный убой для производителей", SRC_INTRO, "rationale")
    zero_cost = add("Нулевая себестоимость мяса", SRC_INTRO, "rationale")
    byproducts = add("Побочные продукты убоя (шкуры, кровь, головы, лапы)", SRC_INTRO, "concept")
    profit_56 = add("Прибыль переработки 5,6 млрд руб.", SRC_SUMMARY, "concept")
    cost_58 = add("Затраты на мясо 5,8 млрд руб.", SRC_SUMMARY, "concept")
    closed_loop = add("Замкнутый безотходный цикл", SRC_INTRO, "rationale")

    link("Бесплатный убой для производителей", "Побочные продукты убоя (шкуры, кровь, головы, лапы)", "rationale_for", SRC_INTRO, "EXTRACTED", 1.0)
    link("Побочные продукты убоя (шкуры, кровь, головы, лапы)", "Прибыль переработки 5,6 млрд руб.", "shares_data_with", SRC_INTRO, "INFERRED", 0.95)
    link("Прибыль переработки 5,6 млрд руб.", "Затраты на мясо 5,8 млрд руб.", "semantically_similar_to", SRC_SUMMARY, "INFERRED", 0.85)
    link("Прибыль переработки 5,6 млрд руб.", "Нулевая себестоимость мяса", "rationale_for", SRC_INTRO, "INFERRED", 0.95)
    link("Замкнутый безотходный цикл", "Нулевая себестоимость мяса", "rationale_for", SRC_INTRO, "INFERRED", 0.9)

    # --- Цепочки переработки ---
    link("Убойный цех", "Завод халяльного желатина", "shares_data_with", SRC_INTRO, "EXTRACTED", 1.0)
    link("Убойный цех", "Кожевенный завод", "shares_data_with", SRC_INTRO, "EXTRACTED", 1.0)
    link("Убойный цех", "Завод кровяной муки", "shares_data_with", SRC_INTRO, "EXTRACTED", 1.0)
    link("Животноводство КРС/МРС", "Убойный цех", "conceptually_related_to", SRC_INTRO, "INFERRED", 0.9)
    link("Завод халяльного желатин", "сертификат Халяль", "references", SRC_INTRO, "INFERRED", 0.85) if False else None
    halal = add("Сертификат Халяль", SRC_INTRO)
    link("Завод халяльного желатина", "Сертификат Халяль", "references", SRC_INTRO, "INFERRED", 0.85)

    # --- Кормовой цикл ---
    sunflower = add("Посев подсолнечника 34 000 га", SRC_INTRO)
    soy = add("Посев сои 34 000 га", SRC_INTRO)
    link("Посев подсолнечника 34 000 га", "Масложировой комбинат", "shares_data_with", SRC_INTRO, "INFERRED", 0.9)
    link("Масложировой комбинат", "Комбикормовый завод", "shares_data_with", SRC_INTRO, "INFERRED", 0.9)
    link("Комбикормовый завод", "Животноводство КРС/МРС", "shares_data_with", SRC_INTRO, "INFERRED", 0.9)
    link("Комбикормовый завод", "Кролиководство", "shares_data_with", SRC_INTRO, "INFERRED", 0.85)
    link("Посев сои 34 000 га", "Комбикормовый завод", "shares_data_with", SRC_INTRO, "INFERRED", 0.85)

    # --- Энергетический цикл ---
    manure = add("Навоз и органические отходы", SRC_INTRO)
    link("Животноводство КРС/МРС", "Навоз и органические отходы", "shares_data_with", SRC_INTRO, "INFERRED", 0.95)
    link("Навоз и органические отходы", "Биогазовая установка 20 МВт·ч", "shares_data_with", SRC_INTRO, "EXTRACTED", 1.0)
    link("Биогазовая установка 20 МВт·ч", "Солнечные панели 50 МВт·ч", "semantically_similar_to", SRC_SUMMARY, "INFERRED", 0.75)
    compost = add("Компост и органические удобрения 600 000 т", SRC_INTRO)
    link("Биогазовая установка 20 МВт·ч", "Компост и органические удобрения 600 000 т", "shares_data_with", SRC_INTRO, "EXTRACTED", 1.0)
    link("Компост и органические удобрения 600 000 т", "Посев подсолнечника 34 000 га", "rationale_for", SRC_INTRO, "INFERRED", 0.85)

    # --- Технологические поставщики ---
    suppliers = [
        ("Meneghin Srl", "Кролиководство"),
        ("AIA Associazione Italiana Allevatori", "Генетический центр КРС"),
        ("SINT Technologies", "Тепличный комплекс 100 га"),
        ("HOCEVAR", "Тепличный комплекс 100 га"),
        ("Gozzini", "Комбикормовый завод"),
    ]
    for sup, target in suppliers:
        sid = add(sup, SRC_SUMMARY)
        tid = add(target, SRC_SUMMARY)
        e = edge(sid, tid, "references", SRC_SUMMARY, "EXTRACTED", 1.0)
        if e:
            edges.append(e)

    # --- Породы ---
    breeds = [
        ("Кьянина", "Генетический центр КРС"),
        ("Маркиджиана", "Генетический центр КРС"),
        ("Лимузин", "Генетический центр КРС"),
        ("Фризон", "Генетический центр Фризон"),
        ("Меринос", "Животноводство КРС/МРС"),
        ("Суффолк", "Животноводство КРС/МРС"),
        ("Дорпер", "Животноводство КРС/МРС"),
    ]
    for breed, target in breeds:
        link(breed, target, "conceptually_related_to", SRC_INTRO, "EXTRACTED", 1.0)

    # --- Рыбоводство ---
    link("Рыбоводство белуга", "Чёрная икра", "shares_data_with", SRC_SUMMARY, "EXTRACTED", 1.0)
    caviar = add("Чёрная икра 20 т/год", SRC_SUMMARY)
    link("Рыбоводство белуга", "Чёрная икра 20 т/год", "shares_data_with", SRC_SUMMARY, "EXTRACTED", 1.0)

    # --- Экспорт ---
    export = add("Экспорт 10,2 млрд руб.", SRC_SUMMARY)
    markets = ["СНГ", "Азия", "Арабские страны", "Ближний Восток"]
    export_products = ["Натуральная кожа", "Халяльный желатин", "Чёрная икра", "Шерсть мериноса"]
    for m in markets:
        mid = add(m, SRC_SUMMARY)
        e = edge(export, mid, "references", SRC_SUMMARY, "EXTRACTED", 1.0)
        if e:
            edges.append(e)
    for p in export_products:
        pid = add(p, SRC_SUMMARY)
        e = edge(pid, export, "conceptually_related_to", SRC_SUMMARY, "INFERRED", 0.9)
        if e:
            edges.append(e)

    # --- Финансы ---
    inv = add("Инвестиции 100 млрд руб.", SRC_SUMMARY)
    rev = add("Выручка 71,4 млрд руб./год", SRC_SUMMARY)
    npv_blocks = [
        ("NPV кролиководство 2,78 млрд", "Кролиководство", 15.19),
        ("NPV теплицы 33,86 млрд", "Тепличный комплекс 100 га", 28.99),
        ("NPV животноводство 28,92 млрд", "Животноводство КРС/МРС", 23.25),
        ("NPV рыбоводство 3,86 млрд", "Рыбоводство белуга", 17.19),
        ("NPV масложировой 26,83 млрд", "Масложировой комбинат", 90.24),
    ]
    link("ООО «МОЯ МЕЧТА»", "Инвестиции 100 млрд руб.", "shares_data_with", SRC_SUMMARY, "EXTRACTED", 1.0)
    link("ООО «МОЯ МЕЧТА»", "Выручка 71,4 млрд руб./год", "shares_data_with", SRC_SUMMARY, "EXTRACTED", 1.0)
    for npv_label, block, irr in npv_blocks:
        nid = add(npv_label, SRC_SUMMARY)
        bid = add(block, SRC_SUMMARY)
        e1 = edge(nid, bid, "rationale_for", SRC_SUMMARY, "EXTRACTED", 1.0)
        irr_node = add(f"IRR {irr}%", SRC_SUMMARY)
        e2 = edge(nid, irr_node, "shares_data_with", SRC_SUMMARY, "EXTRACTED", 1.0)
        if e1:
            edges.append(e1)
        if e2:
            edges.append(e2)

    payback = add("Окупаемость 8 лет", SRC_SUMMARY)
    link("Выручка 71,4 млрд руб./год", "Окупаемость 8 лет", "rationale_for", SRC_SUMMARY, "INFERRED", 0.85)

    # --- Риски и меры (из 06-vyvody) ---
    risks = [
        ("Технологические риски", "IoT-мониторинг и обучение персонала"),
        ("Биологические и ветеринарные риски", "Ветеринарный контроль и страхование поголовья"),
        ("Климатические и природные риски", "Автономная энергетика и капельное орошение"),
        ("Экономические и рыночные риски", "Долгосрочные контракты и валютная диверсификация"),
        ("Юридические и регуляторные риски", "Юридический мониторинг и лицензирование"),
        ("Финансовые риски", "Поэтапное финансирование и резервный фонд"),
        ("Логистические риски", "Собственная логистика и запасы материалов"),
        ("Социальные и кадровые риски", "Социальные проекты и программы обучения"),
        ("Экологические риски", "Биогаз и зелёные сертификаты"),
    ]
    for risk, mitigation in risks:
        rid = add(risk, SRC_RISK, "rationale")
        mid = add(mitigation, SRC_RISK, "concept")
        e1 = edge(rid, mid, "rationale_for", SRC_RISK, "EXTRACTED", 1.0)
        e2 = edge(hub, rid, "conceptually_related_to", SRC_RISK, "INFERRED", 0.75)
        if e1:
            edges.append(e1)
        if e2:
            edges.append(e2)

    # --- Рыночные драйверы (из 04 и 01) ---
    drivers = [
        ("Дефицит мяса в РФ 12,1 млн т", "Животноводство КРС/МРС"),
        ("Импортозамещение продовольствия", "ООО «МОЯ МЕЧТА»"),
        ("Госпрограмма восстановления Херсонской области", "Херсонская область"),
        ("Спрос на халяльную продукцию", "Сертификат Халяль"),
        ("Рост экспорта маргарина РФ +80%", "Масложировой комбинат"),
        ("Дефицит переработки шкур до 80% потерь", "Кожевенный завод"),
        ("Спрос на телятину и ягнятину Ближний Восток", "Экспорт 10,2 млрд руб."),
        ("Круглогодичное тепличное производство", "Тепличный комплекс 100 га"),
    ]
    for driver, target in drivers:
        link(driver, target, "rationale_for", SRC_MARKET, "INFERRED", 0.85)

    # --- Молочная цепочка (из 03) ---
    dairy_products = ["Кефир", "Творог", "Сыр твёрдый", "Сливочное масло", "Сметана"]
    milk_plant = add("Завод переработки молока", SRC_PROD)
    for dp in dairy_products:
        link("Завод переработки молока", dp, "conceptually_related_to", SRC_PROD, "INFERRED", 0.85)
    whey = add("Сыворотка — корм и пищевые добавки", SRC_PROD)
    link("Творог", "Сыворотка — корм и пищевые добавки", "shares_data_with", SRC_PROD, "EXTRACTED", 1.0)
    link("Сыворотка — корм и пищевые добавки", "Комбикормовый завод", "shares_data_with", SRC_PROD, "INFERRED", 0.85)

    # --- Гиперрёбра ---
    hyperedges.append({
        "id": "closed_cycle_apk",
        "label": "Замкнутый агропромышленный цикл",
        "nodes": [
            add("Посев подсолнечника 34 000 га", SRC_INTRO),
            add("Комбикормовый завод", SRC_INTRO),
            add("Животноводство КРС/МРС", SRC_SUMMARY),
            add("Убойный цех", SRC_INTRO),
            add("Биогазовая установка 20 МВт·ч", SRC_SUMMARY),
        ],
        "relation": "participate_in",
        "confidence": "INFERRED",
        "confidence_score": 0.9,
        "source_file": SRC_INTRO,
    })
    hyperedges.append({
        "id": "byproduct_value_chain",
        "label": "Цепочка монетизации побочных продуктов",
        "nodes": [
            add("Убойный цех", SRC_INTRO),
            add("Кожевенный завод", SRC_INTRO),
            add("Завод халяльного желатина", SRC_INTRO),
            add("Завод кровяной муки", SRC_INTRO),
            add("Нулевая себестоимость мяса", SRC_INTRO),
        ],
        "relation": "form",
        "confidence": "EXTRACTED",
        "confidence_score": 1.0,
        "source_file": SRC_INTRO,
    })
    hyperedges.append({
        "id": "green_energy_cluster",
        "label": "Кластер зелёной энергии",
        "nodes": [
            add("Биогазовая установка 20 МВт·ч", SRC_SUMMARY),
            add("Солнечные панели 50 МВт·ч", SRC_SUMMARY),
            add("Навоз и органические отходы", SRC_INTRO),
            add("Замкнутый безотходный цикл", SRC_INTRO),
        ],
        "relation": "participate_in",
        "confidence": "INFERRED",
        "confidence_score": 0.85,
        "source_file": SRC_SUMMARY,
    })

    return list(nodes.values()), edges, hyperedges


STANDARD_RELATIONS = {
    "calls", "implements", "references", "cites", "conceptually_related_to",
    "shares_data_with", "semantically_similar_to", "rationale_for",
}

RELATION_MAP = {
    "PRODUCES": "shares_data_with",
    "YIELDS": "shares_data_with",
    "RAW_MATERIAL_FOR": "shares_data_with",
    "INGREDIENT_OF": "shares_data_with",
    "FEEDSTOCK_FOR": "shares_data_with",
    "FEEDS": "shares_data_with",
    "FERTILIZES": "rationale_for",
    "POWERS": "shares_data_with",
    "ENABLES": "rationale_for",
    "EXPORTED_TO": "references",
    "SOLD_IN": "references",
    "SUPPLIES": "references",
    "PROCESSES_VIA": "conceptually_related_to",
    "EQUIPMENT_FOR": "conceptually_related_to",
    "BYPRODUCT_FROM": "shares_data_with",
    "FLOWS_INTO": "shares_data_with",
    "ADDRESSES": "rationale_for",
    "ADDRESSES_GAP_IN": "rationale_for",
    "CREATES_OPPORTUNITY_FOR": "rationale_for",
    "STRENGTHENS": "rationale_for",
    "BELONGS_TO": "conceptually_related_to",
    "CHARACTERIZES": "conceptually_related_to",
}


def normalize_chunk_item(item: dict, default_source: str) -> dict:
    item = dict(item)
    if not item.get("source_file"):
        item["source_file"] = default_source
    return item


def normalize_chunk_edges(edges: list[dict], default_source: str) -> list[dict]:
    out = []
    for e in edges:
        if e is None:
            continue
        e = dict(e)
        if not e.get("source_file"):
            e["source_file"] = default_source
        rel = e.get("relation", "")
        if rel not in STANDARD_RELATIONS:
            e["relation"] = RELATION_MAP.get(rel, "conceptually_related_to")
        if "confidence" not in e:
            e["confidence"] = "INFERRED"
        if "confidence_score" not in e:
            e["confidence_score"] = 0.75
        if "weight" not in e:
            e["weight"] = 1.0
        out.append(e)
    return out


def load_chunk_files() -> tuple[list[dict], list[dict], list[dict]]:
    """Подхватить chunk-файлы от LLM-субагентов, если есть."""
    nodes, edges, hyper = [], [], []
    for p in sorted(OUT.glob(".graphify_chunk_*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            default_src = "docs/graphify-corpus/00-summary.md"
            for n in d.get("nodes", []):
                nodes.append(normalize_chunk_item(n, n.get("source_file") or default_src))
            edges.extend(normalize_chunk_edges(d.get("edges", []), default_src))
            for h in d.get("hyperedges", []):
                hyper.append(normalize_chunk_item(h, h.get("source_file") or default_src))
        except Exception as exc:
            print(f"  skip chunk {p.name}: {exc}", file=sys.stderr)
    return nodes, edges, hyper


def merge_extractions(*extractions: dict) -> dict:
    nodes_map: dict[str, dict] = {}
    all_edges: list[dict] = []
    all_hyper: list[dict] = []
    tokens_in = tokens_out = 0

    for ext in extractions:
        for n in ext.get("nodes", []):
            nid = n["id"]
            if nid not in nodes_map:
                nodes_map[nid] = n
            elif len(n.get("label", "")) > len(nodes_map[nid].get("label", "")):
                nodes_map[nid] = n
        all_edges.extend(ext.get("edges", []))
        all_hyper.extend(ext.get("hyperedges", []))
        tokens_in += ext.get("input_tokens", 0)
        tokens_out += ext.get("output_tokens", 0)

    seen_e = set()
    deduped_edges = []
    for e in all_edges:
        if e is None:
            continue
        key = (e["source"], e["target"], e["relation"])
        if key not in seen_e:
            seen_e.add(key)
            deduped_edges.append(e)

    return {
        "nodes": list(nodes_map.values()),
        "edges": deduped_edges,
        "hyperedges": all_hyper,
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    sem_nodes, sem_edges, sem_hyper = build_semantic_ontology()
    chunk_nodes, chunk_edges, chunk_hyper = load_chunk_files()
    semantic = {
        "nodes": sem_nodes + chunk_nodes,
        "edges": sem_edges + chunk_edges,
        "hyperedges": sem_hyper + chunk_hyper,
        "input_tokens": 0,
        "output_tokens": 0,
    }
    (OUT / "extraction-semantic.json").write_text(
        json.dumps(semantic, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Semantic: {len(semantic['nodes'])} nodes, {len(semantic['edges'])} edges, {len(semantic['hyperedges'])} hyperedges")

    structural = json.loads(STRUCTURAL.read_text(encoding="utf-8")) if STRUCTURAL.exists() else {
        "nodes": [], "edges": [], "hyperedges": []
    }
    merged = merge_extractions(structural, semantic)
    (OUT / "extraction-merged.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Merged: {len(merged['nodes'])} nodes, {len(merged['edges'])} edges")

    from graphify.build import build
    from graphify.cluster import cluster, score_all
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
    from graphify.report import generate
    from graphify.export import to_json, to_html

    G = build([merged], root=ROOT)
    communities = cluster(G, resolution=1.0)
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
        {
            "total_files": 146,
            "total_words": 166762,
            "warning": "Структурный + семантический граф ТЭО (deep mode, доменная онтология)",
        },
        {"input": merged.get("input_tokens", 0), "output": merged.get("output_tokens", 0)},
        str(ROOT),
        suggested_questions=questions,
        min_community_size=3,
    )
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    to_json(G, communities, str(OUT / "graph.json"), community_labels=labels, force=True)
    to_html(G, communities, str(OUT / "graph.html"), community_labels=labels)
    (OUT / ".graphify_python").write_text(sys.executable, encoding="utf-8")

    # stats
    rel_counts: dict[str, int] = {}
    conf_counts: dict[str, int] = {}
    for e in merged["edges"]:
        rel_counts[e.get("relation", "?")] = rel_counts.get(e.get("relation", "?"), 0) + 1
        conf = e.get("confidence", "UNKNOWN")
        conf_counts[conf] = conf_counts.get(conf, 0) + 1

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities")
    print(f"Relations: {dict(sorted(rel_counts.items(), key=lambda x: -x[1])[:8])}")
    print(f"Confidence: {conf_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

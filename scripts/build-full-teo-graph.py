#!/usr/bin/env python3
"""Полная структурно-семантическая экстракция ТЭО для Graphify."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"
CORPUS_DIRS = [ROOT / "docs" / "graphify-corpus", ROOT / "docs" / "teo"]

REL_DOC = "references"
REL_HIER = "conceptually_related_to"
REL_CO = "shares_data_with"
REL_WIKI = "references"
REL_RISK = "rationale_for"

STOP = {
    "это", "как", "для", "при", "или", "также", "более", "менее", "может", "будет",
    "года", "году", "год", "тыс", "руб", "рублей", "млн", "млрд", "весь", "мире",
    "все", "всех", "если", "что", "они", "она", "его", "ее", "них", "том", "так",
    "из", "на", "по", "от", "до", "не", "но", "а", "и", "в", "с", "у", "о", "об",
    "the", "and", "for", "with", "from", "that", "are", "was", "were", "has", "have",
}

PROJECT_ENTITIES = [
    "ООО «МОЯ МЕЧТА»", "Херсонская область", "SAM-NEGIN",
    "Кролиководство", "Тепличный комплекс", "Животноводство", "Рыбоводство",
    "Масложировой комбинат", "Биогазовая установка", "Солнечные панели",
    "Комбикормовый завод", "Халяльный желатин", "Натуральная кожа",
    "Кровяная мука", "Чёрная икра", "Белуга", "Meneghin Srl", "SINT Technologies",
    "HOCEVAR", "AIA", "Кьянина", "Маркиджиана", "Лимузин", "Фризон",
    "Меринос", "Суффолк", "Дорпер", "NPV", "IRR", "инвестиции 100 млрд",
    "выручка 71,4 млрд", "нулевая себестоимость мяса", "экспорт 10,2 млрд",
    "UNIDO", "Госпрограмма восстановления", "сертификат Халяль",
]

RISK_TYPES = [
    "Технологические риски", "Биологические и ветеринарные риски",
    "Климатические и природные риски", "Экономические и рыночные риски",
    "Юридические и регуляторные риски", "Финансовые риски",
    "Логистические риски", "Социальные и кадровые риски", "Экологические риски",
]


def norm_id(stem: str, label: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", stem.lower())[:40].strip("_")
    ent = re.sub(r"[^a-z0-9]+", "_", label.lower())[:60].strip("_")
    return f"{base}_{ent}" if ent else base


def node(nid: str, label: str, source: str, ftype: str = "concept") -> dict:
    return {
        "id": nid,
        "label": label[:200],
        "file_type": ftype,
        "source_file": source,
        "source_location": None,
    }


def edge(src: str, tgt: str, relation: str, source: str, conf: str = "EXTRACTED", score: float = 1.0) -> dict:
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


def extract_heading_level(line: str) -> tuple[int, str] | None:
    m = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
    if m:
        return len(m.group(1)), m.group(2).strip()
    return None


def extract_bullet(line: str) -> str | None:
    line = line.strip()
    for p in (r"^[-*✓]\s+(.+)$", r"^\d+\.\s+(.+)$", r"^Риски:\s*$", r"^Меры снижения:\s*$"):
        m = re.match(p, line)
        if m:
            return m.group(1).strip() if m.lastindex else line
    if line.startswith("Риски:") or line.startswith("Меры"):
        return line
    return None


def extract_wikilinks(text: str) -> list[str]:
    return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", text)


def extract_caps_phrases(text: str) -> list[str]:
    found = []
    for m in re.finditer(r"[«\"]([^»\"]{3,80})[»\"]", text):
        found.append(m.group(1).strip())
    for m in re.finditer(r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z][A-Za-z0-9]+){0,3})\b", text):
        found.append(m.group(1).strip())
    return found


def extract_table_rows(text: str) -> list[list[str]]:
    rows = []
    for line in text.splitlines():
        if "||" in line or "|" in line:
            parts = [p.strip() for p in re.split(r"\|\|?|\t", line) if p.strip()]
            if len(parts) >= 2:
                rows.append(parts)
    return rows


def is_noise_label(label: str) -> bool:
    s = label.strip()
    if len(s) < 3:
        return True
    if re.fullmatch(r"[\d\s,.:;%\-–—/]+", s):
        return True
    return False


def add_project_backbone(nodes: dict[str, dict], edges: list[dict], source: str) -> None:
    core = [
        "ООО «МОЯ МЕЧТА»", "Херсонская область", "Кролиководство", "Тепличный комплекс",
        "Животноводство", "Рыбоводство", "Масложировой комбинат", "Биогазовая установка",
        "Халяльный желатин", "Натуральная кожа", "Чёрная икра", "нулевая себестоимость мяса",
        "инвестиции 100 млрд", "выручка 71,4 млрд", "экспорт 10,2 млрд",
    ]
    ids = []
    for c in core:
        nid = norm_id("project_core", c)
        if nid not in nodes:
            nodes[nid] = node(nid, c, source, "concept")
        ids.append(nid)
    hub = ids[0]
    for other in ids[1:]:
        e = edge(hub, other, REL_HIER, source, "EXTRACTED", 1.0)
        if e:
            edges.append(e)
    pairs = [
        ("Животноводство", "Халяльный желатин"),
        ("Животноводство", "Натуральная кожа"),
        ("Животноводство", "Биогазовая установка"),
        ("Рыбоводство", "Чёрная икра"),
        ("нулевая себестоимость мяса", "Халяльный желатин"),
        ("нулевая себестоимость мяса", "Натуральная кожа"),
    ]
    for a, b in pairs:
        ea = norm_id("project_core", a)
        eb = norm_id("project_core", b)
        if ea in nodes and eb in nodes:
            e = edge(ea, eb, REL_RISK, source, "INFERRED", 0.9)
            if e:
                edges.append(e)


def tokenize_entities(text: str) -> list[str]:
    ents = []
    ents.extend(extract_caps_phrases(text))
    for pe in PROJECT_ENTITIES:
        if pe.lower() in text.lower():
            ents.append(pe)
    for rt in RISK_TYPES:
        if rt.lower() in text.lower():
            ents.append(rt)
    # Capitalized Russian multi-word (2-5 words)
    for m in re.finditer(r"\b([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁа-яё][а-яё]+){0,4})\b", text):
        phrase = m.group(1).strip()
        words = phrase.lower().split()
        if len(words) >= 2 and not any(w in STOP for w in words[:1]):
            if len(phrase) >= 6:
                ents.append(phrase)
    # metrics
    for m in re.finditer(
        r"((?:NPV|IRR|PB|рентабельность|окупаемость|инвестиц|выручк)[^\n.,;]{0,60})",
        text,
        re.I,
    ):
        ents.append(m.group(1).strip()[:80])
    for m in re.finditer(r"(\d[\d\s,.]*\s*(?:млрд|млн|тыс\.?|тн|га|МВт|кг|руб)[^\n.,;]{0,30})", text, re.I):
        ents.append(m.group(1).strip()[:80])
    # dedupe preserve order
    seen = set()
    out = []
    for e in ents:
        k = e.lower()
        if k not in seen and len(k) > 2:
            seen.add(k)
            out.append(e)
    return out[:25]


def process_file(path: Path) -> tuple[list[dict], list[dict]]:
    rel = str(path.relative_to(ROOT))
    stem = path.stem
    text = path.read_text(encoding="utf-8", errors="replace")
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(label: str, ftype: str = "concept") -> str:
        label = label.strip()
        if not label or is_noise_label(label):
            return ""
        nid = norm_id(stem, label)
        if nid not in nodes:
            nodes[nid] = node(nid, label, rel, ftype)
        return nid

    doc_nid = add_node(path.stem.replace("-", " "), "document")
    heading_stack: list[tuple[int, str]] = []
    prev_nid = doc_nid

    paragraphs: list[str] = []
    current_para: list[str] = []

    def flush_para():
        nonlocal current_para
        if current_para:
            paragraphs.append("\n".join(current_para))
            current_para = []

    for line in text.splitlines():
        h = extract_heading_level(line)
        if h:
            flush_para()
            level, title = h
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            nid = add_node(title, "concept")
            if heading_stack:
                e = edge(heading_stack[-1][1], nid, REL_HIER, rel)
                if e:
                    edges.append(e)
            heading_stack.append((level, nid))
            prev_nid = nid
            continue
        bullet = extract_bullet(line)
        if bullet:
            flush_para()
            bnid = add_node(bullet[:120], "concept")
            e = edge(prev_nid, bnid, REL_HIER, rel)
            if e:
                edges.append(e)
            continue
        if line.strip():
            current_para.append(line)
        else:
            flush_para()
    flush_para()

    for para in paragraphs:
        ents = tokenize_entities(para)
        nids = [add_node(e) for e in ents]
        nids = [n for n in nids if n]
        if not nids:
            continue
        anchor = heading_stack[-1][1] if heading_stack else doc_nid
        for n in nids[:12]:
            e = edge(anchor, n, REL_CO, rel, "INFERRED", 0.75)
            if e:
                edges.append(e)
        for i in range(len(nids)):
            for j in range(i + 1, min(i + 4, len(nids))):
                e = edge(nids[i], nids[j], REL_CO, rel, "INFERRED", 0.65)
                if e:
                    edges.append(e)

    for wl in extract_wikilinks(text):
        src = add_node(wl, "document")
        e = edge(doc_nid, src, REL_WIKI, rel)
        if e:
            edges.append(e)

    for row in extract_table_rows(text):
        if len(row) >= 2:
            a, b = add_node(row[0]), add_node(row[1])
            if a and b:
                e = edge(a, b, REL_DOC, rel, "EXTRACTED", 0.95)
                if e:
                    edges.append(e)

    return list(nodes.values()), edges


def cross_link_by_label(all_nodes: list[dict]) -> list[dict]:
    label_map: dict[str, list[str]] = defaultdict(list)
    for n in all_nodes:
        key = re.sub(r"\s+", " ", n["label"].lower().strip())
        if len(key) > 3:
            label_map[key].append(n["id"])
    extra = []
    for key, ids in label_map.items():
        if len(ids) < 2:
            continue
        base = ids[0]
        for other in ids[1:6]:
            e = edge(base, other, "semantically_similar_to", all_nodes[0]["source_file"], "INFERRED", 0.85)
            if e:
                extra.append(e)
    return extra


def main() -> int:
    all_nodes: dict[str, dict] = {}
    all_edges: list[dict] = []

    files = []
    for d in CORPUS_DIRS:
        if d.exists():
            files.extend(sorted(d.glob("*.md")))
    files = [f for f in files if f.name != "README.md"]

    print(f"Processing {len(files)} markdown files...")
    for i, f in enumerate(files, 1):
        try:
            ns, es = process_file(f)
            for n in ns:
                if n["id"] not in all_nodes:
                    all_nodes[n["id"]] = n
            all_edges.extend(es)
        except Exception as exc:
            print(f"  skip {f.name}: {exc}", file=sys.stderr)
        if i % 20 == 0:
            print(f"  {i}/{len(files)} files...")

    cross = cross_link_by_label(list(all_nodes.values()))
    all_edges.extend(cross)
    add_project_backbone(all_nodes, all_edges, str(CORPUS_DIRS[0] / "00-summary.md"))

    # dedupe edges
    seen_e = set()
    deduped_edges = []
    for e in all_edges:
        if e is None:
            continue
        key = (e["source"], e["target"], e["relation"])
        if key not in seen_e:
            seen_e.add(key)
            deduped_edges.append(e)

    extraction = {
        "nodes": list(all_nodes.values()),
        "edges": deduped_edges,
        "hyperedges": [],
        "input_tokens": 0,
        "output_tokens": 0,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "extraction-full.json").write_text(
        json.dumps(extraction, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Extracted: {len(extraction['nodes'])} nodes, {len(extraction['edges'])} edges")

    from graphify.build import build
    from graphify.cluster import cluster, score_all
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
    from graphify.report import generate
    from graphify.export import to_json, to_html

    G = build([extraction], root=ROOT)
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
            "total_files": len(files),
            "total_words": sum(len(f.read_text(encoding="utf-8").split()) for f in files),
            "warning": "Полная структурно-семантическая экстракция ТЭО (markdown корпус)",
        },
        {"input": 0, "output": 0},
        str(ROOT),
        suggested_questions=questions,
        min_community_size=3,
    )
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    to_json(G, communities, str(OUT / "graph.json"), community_labels=labels, force=True)
    to_html(G, communities, str(OUT / "graph.html"), community_labels=labels)
    (OUT / ".graphify_python").write_text(sys.executable, encoding="utf-8")

    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

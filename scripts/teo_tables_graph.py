"""Graphify nodes/edges from recovered docx tables (land budget + critical tables)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LAND_BUDGET = ROOT / "docs" / "teo-tables" / "land-budget.yaml"
MANIFEST_PATH = ROOT / "docs" / "teo-tables" / "manifest.json"
CORPUS_TABLES = ROOT / "docs" / "graphify-corpus" / "07-docx-tables-critical.md"

REL_HIER = "conceptually_related_to"
REL_REF = "references"

_SLUG_RE = re.compile(r"[^a-z0-9а-яё]+", re.I)

BLOCK_LABELS: dict[str, str] = {
    "кролиководство": "Кролиководство",
    "тепличный_комплекс": "Тепличный комплекс",
    "животноводство": "Животноводство",
    "рыбоводство": "Рыбоводство",
    "масложировой_комбинат": "Масложировой комбинат",
    "прочие_строительство": "Прочие земли строительства",
    "подсолнечник": "Подсолнечник",
    "соя": "Соя",
    "прочие": "Прочие культуры",
}

PROD_NODE_IDS: dict[str, str] = {
    "кролиководство": "project_core_кролиководство",
    "тепличный_комплекс": "project_core_тепличный_комплекс",
    "животноводство": "project_core_животноводство",
    "рыбоводство": "project_core_рыбоводство",
    "масложировой_комбинат": "project_core_масложировой_комбинат",
}

NPV_TABLE_PROD: dict[int, str] = {
    7: "project_core_кролиководство",
    8: "project_core_тепличный_комплекс",
    9: "project_core_животноводство",
    10: "project_core_рыбоводство",
    11: "project_core_масложировой_комбинат",
}


def slugify(text: str, max_len: int = 60) -> str:
    s = _SLUG_RE.sub("_", text.lower())[:max_len].strip("_")
    return s or "x"


def _node(nid: str, label: str, source: str, ftype: str = "concept") -> dict:
    return {
        "id": nid,
        "label": label[:200],
        "file_type": ftype,
        "source_file": source,
        "source_location": None,
    }


def _edge(src: str, tgt: str, relation: str, source: str, conf: str = "EXTRACTED", score: float = 1.0) -> dict | None:
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


def _load_land_budget() -> dict:
    if not LAND_BUDGET.exists():
        return {}
    raw = LAND_BUDGET.read_text(encoding="utf-8")
    body = raw.split("\n", 1)[-1] if raw.startswith("#") else raw
    return yaml.safe_load(body) or {}


def add_land_budget_nodes(nodes: dict[str, dict], edges: list[dict]) -> None:
    data = _load_land_budget()
    if not data:
        return
    source = str(LAND_BUDGET.relative_to(ROOT))
    hub = "project_core_ооо_моя_мечта"

    def ensure(nid: str, label: str) -> str:
        if nid not in nodes:
            nodes[nid] = _node(nid, label, source, "metric")
        return nid

    apk = ensure("land_apk_100000", f"APK {data.get('total_apk_ha', 100_000):,} га".replace(",", " "))
    construction = ensure(
        "land_construction_20000",
        f"Строительство {data.get('construction_ha', 20_000):,} га".replace(",", " "),
    )
    arable = ensure(
        "land_arable_80000",
        f"Посевная {data.get('arable_ha', 80_000):,} га".replace(",", " "),
    )
    other = ensure(
        "land_other_19490",
        f"Прочие земли строительства {data.get('other_ha', 19_490):,} га".replace(",", " "),
    )

    for e in (
        _edge(hub, apk, REL_HIER, source),
        _edge(apk, construction, REL_HIER, source),
        _edge(apk, arable, REL_HIER, source),
        _edge(construction, other, REL_HIER, source, "EXTRACTED", 1.0),
    ):
        if e:
            edges.append(e)

    block_ids: dict[str, str] = {}
    for slug, ha in (data.get("blocks_ha") or {}).items():
        if slug == "прочие_строительство":
            continue
        label = BLOCK_LABELS.get(slug, slug.replace("_", " ").title())
        nid = ensure(f"land_block_{slugify(slug)}", f"{label} {ha:,} га".replace(",", " "))
        block_ids[slug] = nid
        e = _edge(construction, nid, REL_HIER, source)
        if e:
            edges.append(e)

    for slug, ha in (data.get("crops_ha") or {}).items():
        label = BLOCK_LABELS.get(slug, slug.replace("_", " ").title())
        nid = ensure(f"land_crop_{slugify(slug)}", f"{label} {ha:,} га".replace(",", " "))
        e = _edge(arable, nid, REL_HIER, source)
        if e:
            edges.append(e)

    for slug, prod_id in PROD_NODE_IDS.items():
        land_id = block_ids.get(slug)
        if land_id and prod_id in nodes:
            e = _edge(land_id, prod_id, REL_REF, source, "EXTRACTED", 0.95)
            if e:
                edges.append(e)


def add_critical_table_nodes(nodes: dict[str, dict], edges: list[dict]) -> None:
    if not MANIFEST_PATH.exists():
        return
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    hub = "project_core_ооо_моя_мечта"
    land_hub = "land_apk_100000"

    for entry in manifest.get("tables", []):
        if not entry.get("critical"):
            continue
        rel_path = entry.get("path_critical") or entry.get("path_all")
        if not rel_path:
            continue
        source = rel_path
        nid = f"docx_table_{slugify(entry['id'])}"
        label = f"Табл. #{entry['index']}: {entry['title']}"
        if nid not in nodes:
            nodes[nid] = _node(nid, label, source, "table")

        e = _edge(hub, nid, REL_REF, source)
        if e:
            edges.append(e)

        idx = entry["index"]
        if idx == 3:
            e2 = _edge(nid, land_hub, REL_HIER, source, "EXTRACTED", 1.0)
            if e2 and land_hub in nodes:
                edges.append(e2)
        elif idx in NPV_TABLE_PROD:
            prod = NPV_TABLE_PROD[idx]
            if prod in nodes:
                e3 = _edge(nid, prod, REL_HIER, source)
                if e3:
                    edges.append(e3)


def add_docx_tables_to_graph(nodes: dict[str, dict], edges: list[dict]) -> None:
    """Inject land budget + critical docx table nodes into Graphify extraction."""
    add_land_budget_nodes(nodes, edges)
    add_critical_table_nodes(nodes, edges)

    if CORPUS_TABLES.exists():
        nid = "corpus_07_docx_tables_critical"
        source = str(CORPUS_TABLES.relative_to(ROOT))
        if nid not in nodes:
            nodes[nid] = _node(nid, "Критичные таблицы ТЭО (docx)", source, "concept")
        hub = "project_core_ооо_моя_мечта"
        e = _edge(hub, nid, REL_REF, source)
        if e:
            edges.append(e)
        if "land_apk_100000" in nodes:
            e2 = _edge(nid, "land_apk_100000", REL_HIER, source)
            if e2:
                edges.append(e2)

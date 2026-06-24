"""Apply what-if scenario to KPI store and graph.json derivative."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    ACTIVE_SCENARIO_PATH,
    GRAPH_BASELINE_PATH,
    GRAPH_PATH,
    KPI_BASELINE_PATH,
    KPI_PATH,
    OUT_DIR,
    SCENARIO_GRAPH_DIR,
)
from dataclasses import replace

from .kpi import BlockKPI, KPIStore, load_kpi, save_kpi
from .scenarios import Scenario, load_scenario


_SLUG_RE = re.compile(r"[^a-z0-9а-яё]+", re.I)


def _slug(text: str, max_len: int = 80) -> str:
    s = _SLUG_RE.sub("_", text.lower())[:max_len].strip("_")
    return s or "node"


def _backup_baseline() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not KPI_BASELINE_PATH.exists() and KPI_PATH.exists():
        shutil.copy2(KPI_PATH, KPI_BASELINE_PATH)
    if not GRAPH_BASELINE_PATH.exists() and GRAPH_PATH.exists():
        shutil.copy2(GRAPH_PATH, GRAPH_BASELINE_PATH)


def build_kpi_for_scenario(scenario: Scenario, baseline: KPIStore | None = None) -> KPIStore:
    baseline = baseline or load_kpi()
    if KPI_BASELINE_PATH.exists():
        baseline = KPIStore.from_dict(json.loads(KPI_BASELINE_PATH.read_text(encoding="utf-8")))

    store = KPIStore(
        project=dict(baseline.project),
        blocks={k: replace(v) for k, v in baseline.blocks.items()},
        built_from=list(baseline.built_from) + [f"scenario:{scenario.id}"],
    )
    store.project.update(scenario.project)

    for bid, raw in scenario.blocks.items():
        if not raw.get("active", True) and bid in store.blocks:
            store.blocks.pop(bid, None)
            continue
        if not raw.get("active", True):
            continue
        prev = store.blocks.get(bid)
        label = raw.get("label") or (prev.label if prev else bid)
        blk = BlockKPI(
            block_id=bid,
            label=label,
            npv_thousand_rub=raw.get("npv_thousand_rub", prev.npv_thousand_rub if prev else None),
            irr_pct=raw.get("irr_pct", prev.irr_pct if prev else None),
            payback_months=raw.get("payback_months", prev.payback_months if prev else None),
            capex_bln_rub=raw.get("capex_bln_rub", prev.capex_bln_rub if prev else None),
            output=raw.get("output", prev.output if prev else None),
            notes=raw.get("note") or raw.get("notes"),
            source=f"docs/scenarios/{scenario.id}.yaml",
            section="what-if scenario",
        )
        store.blocks[bid] = blk

    replaces = scenario.raw.get("replaces")
    if replaces and replaces in store.blocks:
        store.blocks.pop(replaces, None)

    return store


def _label_matches(label: str, needle: str) -> bool:
    return needle.lower() in label.lower()


def _find_node_ids_by_labels(nodes: list[dict], labels: list[str]) -> set[str]:
    found: set[str] = set()
    for node in nodes:
        lbl = node.get("label", "")
        norm = node.get("norm_label", lbl)
        for needle in labels:
            if _label_matches(lbl, needle) or _label_matches(norm, needle):
                found.add(node["id"])
    return found


def _make_node(label: str, scenario_id: str) -> dict:
    nid = f"scenario_{scenario_id}_{_slug(label)}"
    return {
        "id": nid,
        "label": label,
        "file_type": "concept",
        "source_file": f"docs/scenarios/{scenario_id}.yaml",
        "source_location": None,
        "community": None,
        "community_name": None,
        "norm_label": label.lower(),
    }


def patch_graph_for_scenario(scenario: Scenario, src_graph: Path | None = None) -> Path:
    src_graph = src_graph or (GRAPH_BASELINE_PATH if GRAPH_BASELINE_PATH.exists() else GRAPH_PATH)
    data = json.loads(src_graph.read_text(encoding="utf-8"))
    nodes: list[dict] = data.get("nodes", [])
    links: list[dict] = data.get("links", [])

    impact = scenario.raw.get("graph_impact", {})
    remove_labels = impact.get("remove_nodes", [])
    add_labels = impact.get("add_nodes", [])
    paths = impact.get("paths_to_rebuild", [])

    remove_ids = _find_node_ids_by_labels(nodes, remove_labels)
    if remove_ids:
        nodes = [n for n in nodes if n["id"] not in remove_ids]
        links = [
            lnk
            for lnk in links
            if lnk.get("source") not in remove_ids and lnk.get("target") not in remove_ids
        ]

    label_to_id: dict[str, str] = {n["label"]: n["id"] for n in nodes}
    for label in add_labels:
        if not any(_label_matches(n["label"], label) for n in nodes):
            node = _make_node(label, scenario.id)
            nodes.append(node)
            label_to_id[label] = node["id"]

    def resolve_id(name: str) -> str | None:
        for lbl, nid in label_to_id.items():
            if _label_matches(lbl, name) or _label_matches(name, lbl):
                return nid
        for n in nodes:
            if _label_matches(n["label"], name):
                return n["id"]
        return None

    for path_str in paths:
        parts = re.split(r"\s*(?:→|->|--)\s*", path_str)
        if len(parts) < 2:
            continue
        src_id = resolve_id(parts[0].strip())
        tgt_id = resolve_id(parts[-1].strip())
        if src_id and tgt_id and src_id != tgt_id:
            links.append(
                {
                    "source": src_id,
                    "target": tgt_id,
                    "relation": "scenario_path",
                    "confidence": "INFERRED",
                    "source_file": f"docs/scenarios/{scenario.id}.yaml",
                }
            )

    data["nodes"] = nodes
    data["links"] = links
    if "graph" in data and isinstance(data["graph"], dict):
        data["graph"]["scenario_id"] = scenario.id
        data["graph"]["scenario_applied_at"] = datetime.now(timezone.utc).isoformat()

    SCENARIO_GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    out_path = SCENARIO_GRAPH_DIR / f"{scenario.id}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return out_path


def apply_scenario(scenario_id: str, *, rebuild_kpi: bool = True, patch_graph: bool = True) -> dict:
    if scenario_id == "baseline":
        return restore_baseline()

    _backup_baseline()
    scenario = load_scenario(scenario_id)
    result: dict = {"scenario_id": scenario_id, "status": scenario.status}

    if rebuild_kpi:
        store = build_kpi_for_scenario(scenario)
        save_kpi(store, KPI_PATH)
        result["kpi_blocks"] = len(store.blocks)
        result["kpi_path"] = str(KPI_PATH)

    if patch_graph:
        graph_out = patch_graph_for_scenario(scenario)
        result["graph_path"] = str(graph_out)
        result["graph_nodes"] = len(json.loads(graph_out.read_text(encoding="utf-8")).get("nodes", []))

    ACTIVE_SCENARIO_PATH.write_text(
        json.dumps(
            {
                "scenario_id": scenario_id,
                "name": scenario.name,
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "replaces": scenario.raw.get("replaces"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    result["active_scenario"] = str(ACTIVE_SCENARIO_PATH)
    return result


def restore_baseline() -> dict:
    if KPI_BASELINE_PATH.exists():
        shutil.copy2(KPI_BASELINE_PATH, KPI_PATH)
    if ACTIVE_SCENARIO_PATH.exists():
        ACTIVE_SCENARIO_PATH.unlink()
    return {
        "scenario_id": "baseline",
        "kpi_path": str(KPI_PATH),
        "graph_path": str(GRAPH_PATH),
        "restored": True,
    }


def active_scenario_id() -> str | None:
    if not ACTIVE_SCENARIO_PATH.exists():
        return None
    try:
        return json.loads(ACTIVE_SCENARIO_PATH.read_text(encoding="utf-8")).get("scenario_id")
    except Exception:
        return None

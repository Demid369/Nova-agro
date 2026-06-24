"""Load and compare TEO what-if scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import SCENARIOS_DIR


@dataclass
class Scenario:
    id: str
    name: str
    status: str
    raw: dict = field(default_factory=dict)

    @property
    def blocks(self) -> dict:
        return self.raw.get("blocks", {})

    @property
    def project(self) -> dict:
        return self.raw.get("project", {})

    @property
    def shared(self) -> dict | list:
        return self.raw.get("shared_infrastructure", self.raw.get("shared", {}))


def load_scenario(scenario_id: str) -> Scenario:
    path = SCENARIOS_DIR / f"{scenario_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Scenario(
        id=data.get("id", scenario_id),
        name=data.get("name", scenario_id),
        status=data.get("status", "draft"),
        raw=data,
    )


def list_scenarios() -> list[str]:
    return sorted(p.stem for p in SCENARIOS_DIR.glob("*.yaml"))


def resolve_scenario_compare(query: str) -> tuple[str, str] | None:
    """Map natural-language what-if query to (baseline_id, variant_id)."""
    q = query.lower()
    if not any(
        w in q
        for w in (
            "сценари",
            "what-if",
            "what if",
            "замен",
            "вариант",
            "сравни",
            "вместо",
            "baseline",
        )
    ):
        return None

    ids = list_scenarios()
    mentioned = [sid for sid in ids if sid.replace("-", " ") in q or sid in q]
    if len(mentioned) >= 2:
        return mentioned[0], mentioned[1]
    if len(mentioned) == 1:
        other = "baseline" if mentioned[0] != "baseline" else "poultry-variant"
        return "baseline", mentioned[0] if mentioned[0] != "baseline" else other

    if any(w in q for w in ("птиц", "бройлер", "утк", "перепел", "индейк", "куриц")):
        return "baseline", "poultry-variant"
    if "кролик" in q and any(w in q for w in ("замен", "вместо", "сценари")):
        return "baseline", "poultry-variant"
    return "baseline", "poultry-variant"


def _fmt_val(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:,.2f}".replace(",", " ")
    return str(v)


def compare_scenarios(base_id: str, variant_id: str) -> str:
    base = load_scenario(base_id)
    var = load_scenario(variant_id)
    lines = [
        f"Сравнение сценариев: {base.name} → {var.name}",
        f"Статус варианта: {var.status}",
        "",
        "## Проект",
    ]

    all_proj_keys = set(base.project) | set(var.project)
    for k in sorted(all_proj_keys):
        bv, vv = base.project.get(k), var.project.get(k)
        if bv != vv:
            lines.append(f"  {k}: {_fmt_val(bv)} → {_fmt_val(vv)}")

    lines.append("")
    lines.append("## Блоки")
    all_blocks = set(base.blocks) | set(var.blocks)
    for bid in sorted(all_blocks):
        b = base.blocks.get(bid, {})
        v = var.blocks.get(bid, {})
        b_active = b.get("active", True)
        v_active = v.get("active", True)
        if b_active == v_active and b.get("npv_thousand_rub") == v.get("npv_thousand_rub"):
            if b_active:
                continue
        label = v.get("label") or b.get("label") or bid
        lines.append(f"### {label} ({bid})")
        lines.append(f"  active: {b_active} → {v_active}")
        for field in ("output", "capex_bln_rub", "npv_thousand_rub", "irr_pct", "payback_months", "equipment"):
            bv, vv = b.get(field), v.get(field)
            if bv != vv:
                lines.append(f"  {field}: {_fmt_val(bv)} → {_fmt_val(vv)}")

    replaces = var.raw.get("replaces")
    if replaces:
        lines.extend(["", f"Заменяет блок: {replaces}"])

    impact = var.raw.get("graph_impact", {})
    if impact:
        lines.extend(["", "## Влияние на граф"])
        for node in impact.get("remove_nodes", []):
            lines.append(f"  − узел: {node}")
        for node in impact.get("add_nodes", []):
            lines.append(f"  + узел: {node}")
        for p in impact.get("paths_to_rebuild", []):
            lines.append(f"  ↻ path: {p}")

    kept = var.raw.get("shared_infrastructure", {})
    if isinstance(kept, dict):
        if kept.get("kept"):
            lines.extend(["", "## Сохраняется", *[f"  • {x}" for x in kept["kept"]]])
        if kept.get("weakened"):
            lines.extend(["", "## Ослабевает", *[f"  • {x}" for x in kept["weakened"]]])

    lines.extend([
        "",
        "## Действия для включения в RAG",
        "1. Обновить docs/graphify-corpus/00-summary.md",
        "2. python scripts/build-teo-kpi-index.py",
        "3. python scripts/build-teo-vector-index.py",
        "4. Пересборка графа (build-full + smart-semantic)",
    ])
    return "\n".join(lines)

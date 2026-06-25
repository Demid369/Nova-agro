"""Structured KPI extraction from TEO corpus tables."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import CORPUS_SUMMARY, KPI_PATH, ROOT, TEO_LAND_BUDGET, TEO_TABLES_CRITICAL

BLOCK_ALIASES: dict[str, list[str]] = {
    "кролиководство": ["кролик", "крольчат", "кроликовод"],
    "теплицы": ["теплиц", "овощ", "цветов"],
    "животноводство": ["животновод", "крс", "мрс", "говядин"],
    "рыбоводство": ["рыбовод", "икр", "белуг", "осетр"],
    "масложировой": ["масложиров", "масл", "маргарин", "шрот"],
    "птицеводство": ["птицевод", "птиц", "бройлер", "утк", "перепел", "индейк", "куриц"],
    "энергия": ["биогаз", "солнечн", "энерг"],
    "финансы": ["npv", "irr", "capex", "инвестиц", "выручк", "окупаем"],
    "ядро": ["моя мечта", "проект", "херсон"],
}


@dataclass
class BlockKPI:
    block_id: str
    label: str
    npv_thousand_rub: float | None = None
    irr_pct: float | None = None
    payback_months: int | None = None
    capex_bln_rub: float | None = None
    output: str | None = None
    notes: str | None = None
    source: str = ""
    section: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class KPIStore:
    project: dict = field(default_factory=dict)
    blocks: dict[str, BlockKPI] = field(default_factory=dict)
    built_from: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "blocks": {k: v.to_dict() for k, v in self.blocks.items()},
            "built_from": self.built_from,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KPIStore:
        store = cls(project=data.get("project", {}), built_from=data.get("built_from", []))
        for bid, raw in data.get("blocks", {}).items():
            store.blocks[bid] = BlockKPI(block_id=bid, label=raw.get("label", bid), **{
                k: raw[k]
                for k in (
                    "npv_thousand_rub", "irr_pct", "payback_months",
                    "capex_bln_rub", "output", "notes", "source", "section",
                )
                if k in raw
            })
        return store


def _slug_block(label: str) -> str:
    low = label.lower().strip()
    for bid, aliases in BLOCK_ALIASES.items():
        if bid in low or any(a in low for a in aliases):
            return bid
    return re.sub(r"[^a-z0-9а-яё]+", "_", low).strip("_")[:40] or "прочее"


def _parse_num(s: str) -> float | None:
    s = s.strip().replace("\u00a0", " ").replace(" ", "").replace(",", ".")
    s = re.sub(r"[^\d.]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_pct(s: str) -> float | None:
    m = re.search(r"([\d,.]+)\s*%", s)
    if not m:
        return _parse_num(s)
    return _parse_num(m.group(1))


def parse_markdown_table(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        if all(re.match(r"^[-:]+$", p) for p in parts):
            continue
        rows.append(parts)
    return rows


def extract_from_summary(path: Path) -> KPIStore:
    rel = str(path.relative_to(ROOT))
    text = path.read_text(encoding="utf-8")
    store = KPIStore(built_from=[rel])

    for line in text.splitlines():
        low = line.lower()
        if "инвестиц" in low and "млрд" in low:
            m = re.search(r"([\d,.]+)\s*млрд", line)
            if m:
                store.project["investment_bln_rub"] = _parse_num(m.group(1))
        if "выручка" in low and "млрд" in low:
            m = re.search(r"([\d,.]+)\s*млрд", line)
            if m:
                store.project["revenue_bln_rub_year"] = _parse_num(m.group(1))
        if "окупаемость" in low:
            m = re.search(r"(\d+)\s*лет", line)
            if m:
                store.project["payback_years"] = int(m.group(1))
        if "экспорт" in low and "млрд" in low:
            m = re.search(r"([\d,.]+)\s*млрд", line)
            if m:
                store.project["export_bln_rub"] = _parse_num(m.group(1))
        if line.strip().startswith("-") and ":" in line:
            body = line.strip().lstrip("- ").strip()
            name, _, rest = body.partition(":")
            bid = _slug_block(name)
            store.blocks.setdefault(
                bid,
                BlockKPI(block_id=bid, label=name.strip(), source=rel, section="Производственные блоки"),
            )
            store.blocks[bid].output = rest.strip()

    in_kpi = False
    in_capex = False
    for line in text.splitlines():
        if "Финансовые KPI" in line:
            in_kpi = True
            in_capex = False
            continue
        if "Фазы и CAPEX" in line or "CAPEX" in line:
            in_capex = True
            in_kpi = False
            continue
        if line.startswith("##") and in_kpi:
            in_kpi = False
        if line.startswith("##") and in_capex:
            in_capex = False
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 2 or parts[0].lower() in ("блок", "---", ""):
            continue
        bid = _slug_block(parts[0])
        blk = store.blocks.get(bid) or BlockKPI(
            block_id=bid, label=parts[0], source=rel,
            section="Финансовые KPI" if in_kpi else "CAPEX",
        )
        if in_kpi and len(parts) >= 4:
            blk.npv_thousand_rub = _parse_num(parts[1])
            blk.irr_pct = _parse_pct(parts[2])
            pm = _parse_num(parts[3])
            blk.payback_months = int(pm) if pm is not None else None
            blk.section = "Финансовые KPI"
        elif in_capex and len(parts) >= 2:
            blk.capex_bln_rub = _parse_num(parts[1])
            blk.section = "CAPEX"
        store.blocks[bid] = blk

    return store


NPV_TABLE_MAP: dict[str, tuple[str, str]] = {
    "T007-npv-krolikovodstvo.md": ("кролиководство", "Кролиководство"),
    "T008-npv-teplitsy.md": ("теплицы", "Теплицы"),
    "T009-npv-zhivotnovodstvo.md": ("животноводство", "Животноводство"),
    "T010-npv-rybovodstvo.md": ("рыбоводство", "Рыбоводство"),
    "T011-npv-maslozhir.md": ("масложировой", "Масложировой"),
}


def extract_from_npv_table(path: Path, block_id: str, label: str) -> BlockKPI | None:
    rows = parse_markdown_table(path.read_text(encoding="utf-8"))
    rel = str(path.relative_to(ROOT))
    blk = BlockKPI(block_id=block_id, label=label, source=rel, section="NPV из docx")
    for row in rows:
        if len(row) < 2:
            continue
        key = row[0].lower()
        val = row[1]
        if "npv" in key or "чистая привед" in key:
            blk.npv_thousand_rub = _parse_num(val)
        elif "irr" in key or "внутренн" in key:
            blk.irr_pct = _parse_pct(val)
        elif "окупа" in key or "pb" in key:
            pm = _parse_num(val)
            blk.payback_months = int(pm) if pm is not None else None
    if blk.npv_thousand_rub is None and blk.irr_pct is None:
        return None
    return blk


def extract_from_land_budget_yaml(path: Path, store: KPIStore) -> None:
    if not path.exists():
        return
    import yaml

    rel = str(path.relative_to(ROOT))
    data = yaml.safe_load(path.read_text(encoding="utf-8").split("\n", 1)[-1])
    store.built_from.append(rel)
    store.project["land_total_apk_ha"] = data.get("total_apk_ha")
    store.project["land_construction_ha"] = data.get("construction_ha")
    store.project["land_other_ha"] = data.get("other_ha")
    store.project["land_arable_ha"] = data.get("arable_ha")
    for slug, ha in (data.get("blocks_ha") or {}).items():
        bid = _slug_block(slug)
        store.blocks.setdefault(
            bid,
            BlockKPI(block_id=bid, label=slug.replace("_", " ").title(), source=rel, section="Земельный баланс"),
        )
        store.blocks[bid].notes = f"Земля: {ha} га"


def build_kpi_store() -> KPIStore:
    store = KPIStore()
    for path in sorted(CORPUS_SUMMARY.glob("*.md")):
        if path.name == "00-summary.md":
            part = extract_from_summary(path)
            store.project.update(part.project)
            store.blocks.update(part.blocks)
            store.built_from.extend(part.built_from)

    for fname, (bid, label) in NPV_TABLE_MAP.items():
        path = TEO_TABLES_CRITICAL / fname
        if path.exists():
            blk = extract_from_npv_table(path, bid, label)
            if blk:
                store.blocks[bid] = blk
                store.built_from.append(str(path.relative_to(ROOT)))

    extract_from_land_budget_yaml(TEO_LAND_BUDGET, store)
    return store


def save_kpi(store: KPIStore, path: Path = KPI_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_kpi(path: Path = KPI_PATH) -> KPIStore:
    if not path.exists():
        return build_kpi_store()
    return KPIStore.from_dict(json.loads(path.read_text(encoding="utf-8")))


def match_block(query: str) -> str | None:
    q = query.lower()
    best: tuple[int, str] | None = None
    for bid, aliases in BLOCK_ALIASES.items():
        score = sum(1 for a in [bid, *aliases] if a in q)
        if score and (best is None or score > best[0]):
            best = (score, bid)
    return best[1] if best else None


def format_kpi_answer(query: str, store: KPIStore | None = None) -> tuple[str, list[dict]] | None:
    store = store or load_kpi()
    citations: list[dict] = []
    q = query.lower()

    if any(w in q for w in ("npv", "irr", "payback", "окупаем", "capex", "сколько", "тонн")) or match_block(
        query
    ):
        bid = match_block(query)
        lines = ["KPI (структурированный слой, не LLM):", ""]
        if bid and bid in store.blocks:
            b = store.blocks[bid]
            lines.append(f"Блок: {b.label}")
            tonnage_q = any(w in q for w in ("сколько", "тонн", "мощност", "объем", "объём"))
            finance_q = any(w in q for w in ("npv", "irr", "payback", "окупаем", "capex"))
            if b.output and (tonnage_q or not finance_q):
                lines.append(f"  Продукт: {b.output}")
            if b.npv_thousand_rub is not None and finance_q:
                npv_fmt = f"{b.npv_thousand_rub:,.0f}".replace(",", " ")
                lines.append(f"  NPV: {npv_fmt} тыс. руб.")
            if b.irr_pct is not None and finance_q:
                lines.append(f"  IRR: {b.irr_pct}%")
            if b.payback_months is not None and finance_q:
                lines.append(f"  Payback: {b.payback_months} мес.")
            if b.capex_bln_rub is not None and finance_q:
                lines.append(f"  CAPEX: {b.capex_bln_rub} млрд руб.")
            citations.append({"type": "kpi", "block": bid, "source": b.source, "section": b.section})
            return "\n".join(lines), citations

        if any(w in q for w in ("инвестиц", "выручк", "экспорт", "окупаем")) and store.project:
            lines.append("Проект (сводка):")
            for k, v in store.project.items():
                lines.append(f"  {k}: {v}")
            citations.append({"type": "kpi", "block": "project", "source": "00-summary.md"})
            return "\n".join(lines), citations

        if "npv" in q or "irr" in q or "блок" in q:
            lines.append("| Блок | NPV тыс. | IRR | Payback | CAPEX млрд |")
            lines.append("|------|----------|-----|---------|------------|")
            for b in store.blocks.values():
                if b.npv_thousand_rub is None and b.capex_bln_rub is None:
                    continue
                lines.append(
                    f"| {b.label} | {b.npv_thousand_rub or '—'} | {b.irr_pct or '—'}% | "
                    f"{b.payback_months or '—'} | {b.capex_bln_rub or '—'} |"
                )
            citations.append({"type": "kpi_table", "source": "docs/graphify-corpus/00-summary.md"})
            return "\n".join(lines), citations
    return None

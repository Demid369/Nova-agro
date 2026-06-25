#!/usr/bin/env python3
"""Extract all Word tables from canonical TEO docx into docs/teo-tables/."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCX = ROOT / "docs" / "1.ТЭО_МОЯ МЕЧТА.docx"
OUT_DIR = ROOT / "docs" / "teo-tables"
ALL_DIR = OUT_DIR / "all"
CRITICAL_DIR = OUT_DIR / "critical"

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

# Curated project tables (not Comtrade reference stats)
CRITICAL_TABLES: dict[int, dict[str, str]] = {
    1: {"id": "T001-master-summary-phases", "title": "Сводка проекта: фазы, CAPEX, мощности"},
    3: {"id": "T003-land-budget", "title": "Земельный баланс 100 000 га"},
    4: {"id": "T004-revenue-matrix", "title": "Выручка по комплексам (местный рынок)"},
    5: {"id": "T005-export-revenue-matrix", "title": "Выручка: экспорт и местный рынок"},
    7: {"id": "T007-npv-krolikovodstvo", "title": "NPV/IRR кролиководство"},
    8: {"id": "T008-npv-teplitsy", "title": "NPV/IRR теплицы"},
    9: {"id": "T009-npv-zhivotnovodstvo", "title": "NPV/IRR животноводство"},
    10: {"id": "T010-npv-rybovodstvo", "title": "NPV/IRR рыбоводство"},
    11: {"id": "T011-npv-maslozhir", "title": "NPV/IRR масложировой"},
    14: {"id": "T014-capex-by-phase", "title": "CAPEX по фазам"},
    21: {"id": "T021-krolik-farm-capex", "title": "Кролиководческая ферма: структура затрат"},
    22: {"id": "T022-investment-schedule", "title": "График внесения инвестиций"},
    236: {"id": "T236-staff-krolik", "title": "Штатное расписание: кролиководство"},
    237: {"id": "T237-staff-teplitsy", "title": "Штатное расписание: теплицы"},
    238: {"id": "T238-staff-zhivotnovodstvo", "title": "Штатное расписание: животноводство"},
    239: {"id": "T239-staff-rybovodstvo", "title": "Штатное расписание: рыбоводство"},
    240: {"id": "T240-staff-maslozhir", "title": "Штатное расписание: масложировой"},
    241: {"id": "T241-taxes-payroll", "title": "Налоги и страховые взносы по блокам"},
}


def para_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", NS))


def table_rows(tbl: ET.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in tbl.findall("w:tr", NS):
        cells: list[str] = []
        for tc in tr.findall("w:tc", NS):
            parts = [para_text(p).strip() for p in tc.findall(".//w:p", NS)]
            parts = [x for x in parts if x]
            cells.append("\n".join(parts))
        if any(c.strip() for c in cells):
            rows.append(cells)
    return rows


def classify_table(rows: list[list[str]], index: int) -> str:
    flat = " ".join(" ".join(r) for r in rows).lower()
    if index in CRITICAL_TABLES:
        return "project_critical"
    if "земельная площадь" in flat or "посевная площадь" in flat:
        return "project_land"
    if re.search(r"i-фаза|ii-фаза|iii-фаза", flat):
        return "project_phase"
    if "npv" in flat or "irr" in flat or "чистая привед" in flat:
        return "project_finance"
    if "налог" in flat and ("ставк" in flat or "ндс" in flat):
        return "project_tax"
    if "оклад" in flat and "фонд зарплат" in flat:
        return "project_staff"
    if "комплекс" in flat and "тыс.руб" in flat:
        return "project_revenue"
    if re.search(r"табл\.?\s*\d+|весь мир|импорт|экспорт", flat):
        return "reference_trade"
    return "other"


def rows_to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    norm = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(c.replace("|", "\\|").replace("\n", " ") for c in row) + " |" for row in norm]
    sep = "| " + " | ".join("---" for _ in range(width)) + " |"
    if len(norm) > 1:
        return lines[0] + "\n" + sep + "\n" + "\n".join(lines[1:])
    return lines[0]


def content_hash(rows: list[list[str]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def first_cell_preview(rows: list[list[str]], max_len: int = 80) -> str:
    for row in rows:
        for cell in row:
            if cell.strip():
                return cell.strip()[:max_len]
    return ""


def write_table_md(
    path: Path,
    *,
    table_index: int,
    title: str,
    category: str,
    rows: list[list[str]],
    source_docx: str,
    critical: bool,
) -> None:
    md = rows_to_markdown(rows)
    header = f"""# {title}

> **Источник:** `{source_docx}` — Word-таблица **#{table_index}**  
> **Категория:** `{category}`  
> **Критичная для проекта:** {'да' if critical else 'нет'}  
> **Извлечено:** автоматически (`scripts/extract-teo-docx-tables.py`)

"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + md + "\n", encoding="utf-8")


def parse_ha_value(val_raw: str) -> int | None:
    """Parse hectare values like '19 490,0 га' or '80\u00a0000,00 га'."""
    if "га" not in val_raw.lower():
        return None
    m = re.search(r"([\d\s,\.]+)\s*га", val_raw.replace("\u00a0", " "), re.I)
    if not m:
        return None
    num = m.group(1).replace(" ", "").replace(",", ".")
    try:
        return int(round(float(num)))
    except ValueError:
        return None


def extract_land_budget_yaml(rows: list[list[str]], out_path: Path) -> None:
    """Parse T003 land table (hectare section only) into structured YAML."""
    data: dict = {
        "source": "docs/1.ТЭО_МОЯ МЕЧТА.docx",
        "source_table": 3,
        "total_apk_ha": 100_000,
        "construction_ha": None,
        "blocks_ha": {},
        "other_ha": None,
        "arable_ha": None,
        "crops_ha": {},
    }
    current_section = None
    for row in rows:
        if len(row) < 2:
            continue
        key = row[0].strip().lower()
        val_raw = row[1].strip()
        if "тыс.руб" in val_raw.lower() or "единиц" in val_raw.lower():
            break
        val = parse_ha_value(val_raw)
        if val is None:
            continue
        if "земельная площадь" in key and "из них" in key:
            data["total_apk_ha"] = val
        elif "строительства объектов" in key:
            data["construction_ha"] = val
            current_section = "construction"
        elif "посевная" in key:
            data["arable_ha"] = val
            current_section = "arable"
        elif key == "другие" and current_section == "construction":
            data["other_ha"] = val
            data["blocks_ha"]["прочие_строительство"] = val
        elif key == "другие" and current_section == "arable":
            data["crops_ha"]["прочие"] = val
        elif current_section == "construction":
            slug = re.sub(r"[^a-z0-9а-яё]+", "_", row[0].strip().lower()).strip("_")
            data["blocks_ha"][slug] = val
        elif current_section == "arable":
            slug = re.sub(r"[^a-z0-9а-яё]+", "_", row[0].strip().lower()).strip("_")
            data["crops_ha"][slug] = val

    import yaml

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        "# Canonical land budget from TEO docx table #3\n"
        + yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


def build_corpus_critical_summary(critical_entries: list[dict]) -> None:
    """Generate RAG-friendly index in graphify-corpus."""
    corpus_path = ROOT / "docs" / "graphify-corpus" / "07-docx-tables-critical.md"
    lines = [
        "# Критичные таблицы ТЭО (восстановлены из docx)",
        "",
        "Канон: [`docs/1.ТЭО_МОЯ МЕЧТА.docx`](../1.ТЭО_МОЯ%20МЕЧТА.docx). "
        "Полный экспорт: [`docs/teo-tables/`](../teo-tables/) — **241** Word-таблица.",
        "",
        "Graphify при конвертации docx→md терял таблицы (остались заглушки «Табл. N»). "
        "Этот слой восстанавливает **проектные** таблицы для RAG и KPI.",
        "",
        "## Земельный баланс (таблица #3)",
        "",
        "См. [`docs/teo-tables/land-budget.yaml`](../teo-tables/land-budget.yaml) и "
        "[`T003-land-budget.md`](../teo-tables/critical/T003-land-budget.md).",
        "",
        "| Назначение | га |",
        "|------------|-----|",
        "| APK всего | 100 000 |",
        "| Строительство объектов | 20 000 |",
        "| — Кролиководство | 50 |",
        "| — Тепличный комплекс | 100 |",
        "| — Животноводство | 300 |",
        "| — Рыбоводство | 30 |",
        "| — Масложировой комбинат | 30 |",
        "| — **Другие** | **19 490** |",
        "| Посевная площадь | 80 000 |",
        "| — Подсолнечник | 34 000 |",
        "| — Соя | 34 000 |",
        "| — Другие | 12 000 |",
        "",
        "## Индекс критичных таблиц",
        "",
        "| # | ID | Назначение |",
        "|---|-----|------------|",
    ]
    for e in sorted(critical_entries, key=lambda x: x["index"]):
        lines.append(
            f"| {e['index']} | {e['id']} | {e['title']} → "
            f"[`{e['id']}.md`](../teo-tables/critical/{e['id']}.md) |"
        )
    lines.extend(
        [
            "",
            "## Связи",
            "- [[00-summary]] — сводка проекта с земельным балансом",
            "- [[05-finansy-i-byudzhet]] — финансы (текст без таблиц)",
            "",
        ]
    )
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text("\n".join(lines), encoding="utf-8")


def build_critical_index(critical_entries: list[dict]) -> None:
    lines = [
        "# Критичные таблицы ТЭО (из docx)",
        "",
        "Автоматически извлечённые **проектные** таблицы. Полный каталог: `manifest.json`.",
        "",
        "| # | ID | Файл | Строк |",
        "|---|-----|------|-------|",
    ]
    for e in sorted(critical_entries, key=lambda x: x["index"]):
        lines.append(
            f"| {e['index']} | {e['id']} | [{e['id']}.md](critical/{e['id']}.md) | {e['row_count']} |"
        )
    lines.append("")
    (CRITICAL_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")


def run(docx_path: Path, check_only: bool = False) -> int:
    if not docx_path.exists():
        print(f"Missing docx: {docx_path}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(docx_path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        body = root.find("w:body", NS)
        if body is None:
            print("Invalid docx: no body", file=sys.stderr)
            return 1

        tables: list[list[list[str]]] = []
        for child in body:
            if child.tag.split("}")[-1] == "tbl":
                rows = table_rows(child)
                if rows:
                    tables.append(rows)

    manifest_path = OUT_DIR / "manifest.json"
    existing_hashes: dict[str, str] = {}
    if check_only and manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in old.get("tables", []):
            existing_hashes[str(entry["index"])] = entry["content_hash"]

    manifest_tables: list[dict] = []
    critical_entries: list[dict] = []
    source_rel = str(docx_path.relative_to(ROOT)).replace("\\", "/")

    for idx, rows in enumerate(tables, start=1):
        cat = classify_table(rows, idx)
        crit_meta = CRITICAL_TABLES.get(idx)
        is_critical = crit_meta is not None
        file_id = crit_meta["id"] if crit_meta else f"T{idx:03d}"
        title = crit_meta["title"] if crit_meta else first_cell_preview(rows) or f"Таблица {idx}"
        h = content_hash(rows)

        entry = {
            "index": idx,
            "id": file_id,
            "title": title,
            "category": cat,
            "critical": is_critical,
            "row_count": len(rows),
            "col_count_max": max(len(r) for r in rows),
            "content_hash": h,
            "preview": first_cell_preview(rows, 120),
            "path_all": f"docs/teo-tables/all/{file_id}.md",
            "path_critical": f"docs/teo-tables/critical/{file_id}.md" if is_critical else None,
        }
        manifest_tables.append(entry)

        if check_only:
            old_h = existing_hashes.get(str(idx))
            if old_h != h:
                print(f"DRIFT table #{idx} {file_id}: hash {old_h} -> {h}", file=sys.stderr)
                return 1
            continue

        write_table_md(
            ALL_DIR / f"{file_id}.md",
            table_index=idx,
            title=title,
            category=cat,
            rows=rows,
            source_docx=source_rel,
            critical=is_critical,
        )
        if is_critical:
            write_table_md(
                CRITICAL_DIR / f"{file_id}.md",
                table_index=idx,
                title=title,
                category=cat,
                rows=rows,
                source_docx=source_rel,
                critical=True,
            )
            critical_entries.append(entry)
            if idx == 3:
                extract_land_budget_yaml(rows, OUT_DIR / "land-budget.yaml")

    if check_only:
        if len(existing_hashes) != len(manifest_tables):
            print(
                f"Table count mismatch: manifest {len(existing_hashes)} vs docx {len(manifest_tables)}",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {len(manifest_tables)} tables match manifest hashes")
        return 0

    # Remove stale exports from interrupted runs
    expected_all = {f"{t['id']}.md" for t in manifest_tables}
    expected_critical = {f"{t['id']}.md" for t in manifest_tables if t["critical"]}
    for stale in ALL_DIR.glob("*.md"):
        if stale.name not in expected_all:
            stale.unlink()
    for stale in CRITICAL_DIR.glob("*.md"):
        if stale.name not in expected_critical and stale.name.lower() != "readme.md":
            stale.unlink()

    manifest = {
        "source_docx": source_rel,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "table_count": len(manifest_tables),
        "critical_count": sum(1 for t in manifest_tables if t["critical"]),
        "categories": {
            cat: sum(1 for t in manifest_tables if t["category"] == cat)
            for cat in sorted({t["category"] for t in manifest_tables})
        },
        "tables": manifest_tables,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    build_critical_index(critical_entries)
    build_corpus_critical_summary(critical_entries)

    readme = f"""# Таблицы ТЭО «МОЯ МЕЧТА» (из docx)

Канон: [`docs/1.ТЭО_МОЯ МЕЧТА.docx`](../1.ТЭО_МОЯ%20МЕЧТА.docx)

| Каталог | Содержание |
|---------|------------|
| [`manifest.json`](manifest.json) | {manifest['table_count']} таблиц, SHA256-хеши |
| [`all/`](all/) | все таблицы `T001`…`T{manifest['table_count']:03d}` |
| [`critical/`](critical/) | {manifest['critical_count']} проектных таблиц |
| [`land-budget.yaml`](land-budget.yaml) | структурированный земельный баланс (#3) |

Обновление:

```bash
python3 scripts/extract-teo-docx-tables.py
python3 scripts/validate-teo-docx-tables.py
```
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")

    print(f"Extracted {len(manifest_tables)} tables -> {OUT_DIR}")
    print(f"  critical: {manifest['critical_count']}")
    print(f"  categories: {manifest['categories']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract TEO docx tables to markdown")
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--check", action="store_true", help="Verify manifest hashes vs docx")
    args = parser.parse_args()
    return run(args.docx.resolve(), check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())

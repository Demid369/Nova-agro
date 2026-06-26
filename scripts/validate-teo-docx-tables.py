#!/usr/bin/env python3
"""Validate extracted TEO docx tables against manifest and critical expectations."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "teo-tables"
MANIFEST_PATH = OUT_DIR / "manifest.json"
LAND_BUDGET_PATH = OUT_DIR / "land-budget.yaml"
CRITICAL_DIR = OUT_DIR / "critical"
ALL_DIR = OUT_DIR / "all"

EXPECTED_TABLE_COUNT = 241
EXPECTED_CRITICAL = {
    1, 3, 4, 5, 7, 8, 9, 10, 11, 14, 21, 22,
    236, 237, 238, 239, 240, 241,
}
LAND_MARKERS = ("19 490", "19\u00a0490", "50,0", "50.0", "100 000")
CRITICAL_LAND_MARKERS = ("19 490", "19\u00a0490", "Кролиководство", "50,0")


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing manifest: {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_manifest_structure(manifest: dict) -> list[str]:
    errors: list[str] = []
    tables = manifest.get("tables", [])
    if len(tables) != EXPECTED_TABLE_COUNT:
        errors.append(f"Expected {EXPECTED_TABLE_COUNT} tables, got {len(tables)}")
    indices = {t["index"] for t in tables}
    if indices != set(range(1, EXPECTED_TABLE_COUNT + 1)):
        missing = set(range(1, EXPECTED_TABLE_COUNT + 1)) - indices
        extra = indices - set(range(1, EXPECTED_TABLE_COUNT + 1))
        if missing:
            errors.append(f"Missing table indices: {sorted(missing)[:10]}...")
        if extra:
            errors.append(f"Unexpected table indices: {sorted(extra)[:10]}...")
    critical_indices = {t["index"] for t in tables if t.get("critical")}
    if critical_indices != EXPECTED_CRITICAL:
        errors.append(
            f"Critical set mismatch: expected {sorted(EXPECTED_CRITICAL)}, "
            f"got {sorted(critical_indices)}"
        )
    return errors


def check_files_on_disk(manifest: dict) -> list[str]:
    errors: list[str] = []
    all_files = list(ALL_DIR.glob("*.md"))
    if len(all_files) != EXPECTED_TABLE_COUNT:
        errors.append(f"all/ file count {len(all_files)} != {EXPECTED_TABLE_COUNT}")
    crit_files = [p for p in CRITICAL_DIR.glob("*.md") if p.name.lower() != "readme.md"]
    expected_crit = sum(1 for t in manifest["tables"] if t.get("critical"))
    if len(crit_files) != expected_crit:
        errors.append(f"critical/ file count {len(crit_files)} != {expected_crit}")
    for entry in manifest["tables"]:
        path_all = ROOT / entry["path_all"]
        if not path_all.exists():
            errors.append(f"Missing all/: {entry['path_all']}")
            continue
        text = path_all.read_text(encoding="utf-8")
        if "| ---" not in text and "| --- |" not in text:
            if entry["row_count"] > 1:
                errors.append(f"No markdown table in {entry['path_all']}")
        if entry.get("critical"):
            path_crit = ROOT / entry["path_critical"]
            if not path_crit.exists():
                errors.append(f"Missing critical/: {entry['path_critical']}")
    return errors


def check_land_budget() -> list[str]:
    errors: list[str] = []
    if not LAND_BUDGET_PATH.exists():
        return ["Missing land-budget.yaml"]
    text = LAND_BUDGET_PATH.read_text(encoding="utf-8")
    if "other_ha: 19490" not in text.replace(" ", "") and "other_ha: 19_490" not in text:
        if not re.search(r"other_ha:\s*19490", text):
            errors.append("land-budget.yaml: other_ha != 19490")
    if "construction_ha: 20000" not in text.replace(" ", ""):
        if not re.search(r"construction_ha:\s*20000", text):
            errors.append("land-budget.yaml: construction_ha != 20000")
    t003 = CRITICAL_DIR / "T003-land-budget.md"
    if t003.exists():
        body = t003.read_text(encoding="utf-8")
        if not any(m in body for m in CRITICAL_LAND_MARKERS):
            errors.append("T003-land-budget.md missing expected land markers")
    return errors


def check_docx_hash_sync() -> list[str]:
    """Re-run extract --check (hash drift vs docx)."""
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "extract-teo-docx-tables.py"), "--check"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return [proc.stderr.strip() or proc.stdout.strip() or "extract --check failed"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TEO docx table exports")
    parser.add_argument("--skip-hash", action="store_true", help="Skip docx hash drift check")
    args = parser.parse_args()

    all_errors: list[str] = []
    try:
        manifest = load_manifest()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1

    all_errors.extend(check_manifest_structure(manifest))
    all_errors.extend(check_files_on_disk(manifest))
    all_errors.extend(check_land_budget())

    if not args.skip_hash:
        all_errors.extend(check_docx_hash_sync())

    graph_path = ROOT / "graphify-out" / "graph.json"
    if graph_path.exists():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        node_ids = {n["id"] for n in graph.get("nodes", [])}
        for required in ("land_other_19490", "land_apk_100000", "docx_table_t003_land_budget"):
            if required not in node_ids:
                all_errors.append(f"graph.json missing node: {required}")
    else:
        all_errors.append("graphify-out/graph.json missing (run build-full-teo-graph.py)")

    if all_errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(
        f"OK: {manifest['table_count']} tables, "
        f"{manifest['critical_count']} critical, land-budget.yaml present"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

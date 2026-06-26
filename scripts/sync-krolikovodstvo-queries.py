#!/usr/bin/env python3
"""Sync registry.rag_validation_queries → tests/teo-queries.yaml (single source of truth)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from krolikovodstvo_inventory import load_registry  # noqa: E402

TEO_QUERIES_PATH = ROOT / "tests" / "teo-queries.yaml"
INV_PREFIX = "inv_q"
HEADER = "# TEO RAG — тестовый набор (router + e2e expectations)\n\n"


def inventory_query_entries(registry: dict) -> list[dict]:
    rows: list[dict] = []
    for item in registry.get("rag_validation_queries", []):
        if not item.get("sync_teo_queries", True):
            continue
        qid = item.get("id")
        if not qid:
            continue
        entry: dict = {
            "id": qid,
            "query": item["query"],
            "expected_mode": item.get("expected_mode", "hybrid"),
            "tags": item.get("tags", ["rabbit", "inventory"]),
        }
        if item.get("expect"):
            entry["expect_contains"] = item["expect"]
        rows.append(entry)
    return rows


def merged_queries(registry: dict) -> list[dict]:
    data = yaml.safe_load(TEO_QUERIES_PATH.read_text(encoding="utf-8"))
    base = [q for q in data.get("queries", []) if not str(q.get("id", "")).startswith(INV_PREFIX)]
    return base + inventory_query_entries(registry)


def check_sync(registry: dict) -> list[str]:
    data = yaml.safe_load(TEO_QUERIES_PATH.read_text(encoding="utf-8"))
    current_inv = [q for q in data.get("queries", []) if str(q.get("id", "")).startswith(INV_PREFIX)]
    expected_inv = inventory_query_entries(registry)
    if current_inv == expected_inv:
        return []
    return [
        "tests/teo-queries.yaml inventory section out of sync — "
        "run: python3 scripts/sync-krolikovodstvo-queries.py --write"
    ]


def write_sync(registry: dict) -> None:
    queries = merged_queries(registry)
    body = yaml.dump({"queries": queries}, allow_unicode=True, sort_keys=False, width=120)
    TEO_QUERIES_PATH.write_text(HEADER + body, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Exit 1 if teo-queries.yaml is out of sync")
    parser.add_argument("--write", action="store_true", help="Merge inventory queries into teo-queries.yaml")
    args = parser.parse_args()

    registry = load_registry()

    if args.check:
        errors = check_sync(registry)
        if errors:
            for e in errors:
                print(e, file=sys.stderr)
            return 1
        print("teo-queries.yaml in sync with registry")
        return 0

    write_sync(registry)
    print(f"Updated {TEO_QUERIES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Extract structured KPI tables from TEO corpus."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from teo_rag.kpi import build_kpi_store, save_kpi  # noqa: E402
from teo_rag.config import KPI_PATH  # noqa: E402


def main() -> int:
    store = build_kpi_store()
    path = save_kpi(store)
    print(f"KPI blocks: {len(store.blocks)}")
    print(f"Project keys: {list(store.project.keys())}")
    print(f"Saved: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

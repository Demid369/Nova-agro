#!/usr/bin/env python3
"""Seed teo-rag-out/memory.jsonl with validated baseline facts (no LLM)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    raise SystemExit(1)

from teo_rag.memory import find_memory_hit, load_entries, save_memory  # noqa: E402


def main() -> int:
    seed_path = ROOT / "tests" / "teo-memory-seed.yaml"
    data = yaml.safe_load(seed_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    added = 0
    skipped = 0

    for item in entries:
        q = item["query"].strip()
        if find_memory_hit(q, threshold=0.95):
            skipped += 1
            continue
        save_memory(
            query=q,
            answer=item["answer"].strip(),
            mode=item.get("mode", "kpi"),
            citations=item.get("citations", []),
            validated=True,
            validation={"valid": True, "seed": True},
        )
        added += 1

    total = len(load_entries())
    print(f"Seed: +{added} new, {skipped} skipped (already in memory)")
    print(f"Memory entries total: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

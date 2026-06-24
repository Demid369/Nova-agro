#!/usr/bin/env python3
"""Quick benchmark: router + retrieval latency on test queries."""

from __future__ import annotations

import sys
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from teo_rag.retrieval import hierarchical_search  # noqa: E402
from teo_rag.router import classify_query  # noqa: E402


def main() -> int:
    data = yaml.safe_load((ROOT / "tests" / "teo-queries.yaml").read_text(encoding="utf-8"))
    queries = data["queries"]
    router_ok = 0
    print(f"{'id':<6} {'expected':<8} {'routed':<8} {'ms':>6}  query")
    print("-" * 72)
    for q in queries:
        t0 = time.perf_counter()
        decision = classify_query(q["query"])
        routed = decision.mode
        if routed == q["expected_mode"]:
            router_ok += 1
        # warm retrieval once
        hierarchical_search(q["query"], mode=routed if routed != "graph" else "vector")
        ms = (time.perf_counter() - t0) * 1000
        mark = "✓" if routed == q["expected_mode"] else "✗"
        print(f"{q['id']:<6} {q['expected_mode']:<8} {routed:<8} {ms:6.0f}  {mark} {q['query'][:40]}")
    print("-" * 72)
    print(f"Router accuracy: {router_ok}/{len(queries)}")
    return 0 if router_ok == len(queries) else 1


if __name__ == "__main__":
    raise SystemExit(main())

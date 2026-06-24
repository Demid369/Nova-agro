#!/usr/bin/env python3
"""Quick benchmark: router + retrieval latency on test queries."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from teo_rag.config import OUT_DIR  # noqa: E402
from teo_rag.retrieval import hierarchical_search  # noqa: E402
from teo_rag.router import classify_query  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="TEO RAG benchmark")
    parser.add_argument("--json", action="store_true", help="Write teo-rag-out/benchmark-latest.json")
    args = parser.parse_args()

    data = yaml.safe_load((ROOT / "tests" / "teo-queries.yaml").read_text(encoding="utf-8"))
    queries = data["queries"]
    router_ok = 0
    rows: list[dict] = []
    print(f"{'id':<6} {'expected':<8} {'routed':<8} {'ms':>6}  query")
    print("-" * 72)
    for q in queries:
        t0 = time.perf_counter()
        decision = classify_query(q["query"])
        routed = decision.mode
        match = routed == q["expected_mode"]
        if match:
            router_ok += 1
        retrieval_mode = routed if routed not in ("graph", "scenario") else "vector"
        hits = hierarchical_search(q["query"], mode=retrieval_mode)
        ms = (time.perf_counter() - t0) * 1000
        mark = "✓" if match else "✗"
        print(f"{q['id']:<6} {q['expected_mode']:<8} {routed:<8} {ms:6.0f}  {mark} {q['query'][:40]}")
        rows.append(
            {
                "id": q["id"],
                "query": q["query"],
                "expected_mode": q["expected_mode"],
                "routed_mode": routed,
                "router_match": match,
                "latency_ms": round(ms, 1),
                "retrieval_hits": len(hits),
            }
        )
    print("-" * 72)
    print(f"Router accuracy: {router_ok}/{len(queries)}")

    if args.json:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        latencies = [r["latency_ms"] for r in rows]
        report = {
            "built_at": datetime.now(timezone.utc).isoformat(),
            "project": "baseline",
            "queries": len(queries),
            "router_accuracy": router_ok,
            "router_accuracy_pct": round(100 * router_ok / len(queries), 1),
            "latency_ms_avg": round(sum(latencies) / len(latencies), 1),
            "latency_ms_p95": round(sorted(latencies)[int(len(latencies) * 0.95)], 1),
            "rows": rows,
        }
        out = OUT_DIR / "benchmark-latest.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report: {out}")

    return 0 if router_ok == len(queries) else 1


if __name__ == "__main__":
    raise SystemExit(main())

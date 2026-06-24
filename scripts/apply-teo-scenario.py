#!/usr/bin/env python3
"""Apply or restore TEO what-if scenario (KPI + graph derivative)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from teo_rag.scenario_apply import active_scenario_id, apply_scenario, restore_baseline  # noqa: E402
from teo_rag.scenario_finance import derive_poultry_from_rabbit  # noqa: E402
from teo_rag.scenarios import list_scenarios  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply TEO what-if scenario to KPI + graph")
    parser.add_argument(
        "action",
        choices=["apply", "restore", "status", "derive-poultry"],
        help="apply <id> | restore baseline | status | derive-poultry",
    )
    parser.add_argument("scenario_id", nargs="?", default="poultry-variant")
    parser.add_argument("--no-graph", action="store_true", help="Skip graph patch")
    parser.add_argument("--no-kpi", action="store_true", help="Skip KPI rebuild")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.action == "status":
        payload = {
            "active": active_scenario_id() or "baseline",
            "available": list_scenarios(),
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Active: {payload['active']}")
            print("Scenarios:", ", ".join(payload["available"]))
        return 0

    if args.action == "derive-poultry":
        d = derive_poultry_from_rabbit()
        payload = d.__dict__
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Method: {d.method}")
            print(f"Output: {d.output_tons_year} т/год")
            print(f"CAPEX: {d.capex_bln_rub} млрд")
            print(f"NPV: {d.npv_thousand_rub:,} тыс. руб.".replace(",", " "))
            print(f"IRR: {d.irr_pct}%")
            print(f"Payback: {d.payback_months} мес.")
            print(f"Δ investment: +{d.investment_delta_bln_rub} млрд, Δ revenue: +{d.revenue_delta_bln_rub} млрд/год")
        return 0

    if args.action == "restore":
        payload = restore_baseline()
    else:
        if args.scenario_id not in list_scenarios():
            print(f"Unknown scenario: {args.scenario_id}", file=sys.stderr)
            return 1
        payload = apply_scenario(
            args.scenario_id,
            rebuild_kpi=not args.no_kpi,
            patch_graph=not args.no_graph,
        )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for k, v in payload.items():
            print(f"{k}: {v}")
        if args.action == "apply":
            print("\nNext (optional): python scripts/build-teo-vector-index.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

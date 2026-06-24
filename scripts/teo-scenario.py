#!/usr/bin/env python3
"""Compare TEO what-if scenarios (baseline vs variants)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from teo_rag.scenarios import compare_scenarios, list_scenarios, load_scenario  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="TEO scenario comparison")
    parser.add_argument("action", choices=["list", "show", "compare"])
    parser.add_argument("args", nargs="*", help="scenario id(s)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.action == "list":
        ids = list_scenarios()
        if args.json:
            print(json.dumps(ids, ensure_ascii=False, indent=2))
        else:
            for sid in ids:
                s = load_scenario(sid)
                tag = "active" if sid == "baseline" else s.status
                print(f"  {sid:20} [{tag}] {s.name}")
        return 0

    if args.action == "show":
        if not args.args:
            print("Usage: teo-scenario.py show <id>", file=sys.stderr)
            return 1
        s = load_scenario(args.args[0])
        if args.json:
            print(json.dumps(s.raw, ensure_ascii=False, indent=2))
        else:
            print(f"# {s.name} ({s.id})")
            print(f"status: {s.status}\n")
            import yaml
            print(yaml.dump(s.raw, allow_unicode=True, default_flow_style=False))
        return 0

    if args.action == "compare":
        if len(args.args) < 2:
            print("Usage: teo-scenario.py compare <baseline> <variant>", file=sys.stderr)
            return 1
        report = compare_scenarios(args.args[0], args.args[1])
        print(report)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 4: §4 export narrative (T10) — reuses phase3 engine."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PHASE4 = ROOT / "docs/inventory/pticevodstvo/pipeline/phase4-export.yaml"
DEFAULT_RULES = ROOT / "docs/inventory/pticevodstvo/pipeline/phase1-tables.yaml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase4", default=str(DEFAULT_PHASE4))
    parser.add_argument("--docx", default="")
    args = parser.parse_args()

    p3_path = ROOT / "scripts" / "apply-teo-poultry-phase3.py"
    spec = importlib.util.spec_from_file_location("apply_teo_poultry_phase3", p3_path)
    p3 = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(p3)

    if args.docx:
        docx = Path(args.docx)
    else:
        rules = yaml.safe_load(Path(DEFAULT_RULES).read_text(encoding="utf-8"))
        docx = ROOT / rules["meta"]["output"]

    if not docx.exists():
        print(f"Missing DOCX: {docx}. Run build-teo-poultry-from-baseline.py first.", file=sys.stderr)
        return 1

    p3.apply_phase3(docx, Path(args.phase4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Export a NotebookLM upload bundle from TEO corpus + generated reports."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_BASE = ROOT / "notebooklm-export"
LATEST = OUT_BASE / "latest"

# Baseline core sources (small enough for NotebookLM limits)
BASELINE_SOURCES = [
    ROOT / "docs/graphify-corpus/00-summary.md",
    ROOT / "docs/graphify-corpus/01-vvedenie-i-resume.md",
    ROOT / "docs/graphify-corpus/06-vyvody-i-riski.md",
    ROOT / "docs/TEO_ПРОСТЫМИ_СЛОВАМИ.md",
    ROOT / "docs/TEO_RAG.md",
]

REPORTS_DIR = ROOT / "docs/reports"


def _stamp_dir() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    return OUT_BASE / ts


def copy_file(src: Path, dest_dir: Path, subdir: str = "") -> Path | None:
    if not src.exists():
        return None
    target_root = dest_dir / subdir if subdir else dest_dir
    target_root.mkdir(parents=True, exist_ok=True)
    dest = target_root / src.name
    shutil.copy2(src, dest)
    return dest


def build_bundle(*, reports_only: bool = False, include_reports: bool = True) -> Path:
    out = _stamp_dir()
    out.mkdir(parents=True, exist_ok=True)
    manifest: dict = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "project": "baseline",
        "notebook_suggestion": "МОЯ МЕЧТА — baseline (кролики)",
        "files": [],
    }

    if not reports_only:
        corpus_dir = out / "corpus"
        corpus_dir.mkdir(exist_ok=True)
        for src in BASELINE_SOURCES:
            if dest := copy_file(src, corpus_dir):
                manifest["files"].append({"path": str(dest.relative_to(out)), "role": "corpus"})

    if include_reports and REPORTS_DIR.exists():
        reports_out = out / "reports"
        reports_out.mkdir(exist_ok=True)
        for src in sorted(REPORTS_DIR.glob("*")):
            if src.suffix.lower() in (".md", ".docx", ".pdf", ".txt"):
                if dest := copy_file(src, reports_out):
                    manifest["files"].append({"path": str(dest.relative_to(out)), "role": "report"})

    readme = out / "README_UPLOAD.txt"
    readme.write_text(
        "\n".join(
            [
                "NotebookLM upload bundle — МОЯ МЕЧТА baseline",
                "",
                "1. Открой https://notebooklm.google.com",
                "2. Notebook: «МОЯ МЕЧТА — baseline (кролики)»",
                "3. Add source → загрузи файлы из corpus/ и reports/",
                "4. Для цифр NPV/IRR используй teo-query.py, не только NotebookLM",
                "",
                f"Files: {len(manifest['files'])}",
            ]
        ),
        encoding="utf-8",
    )

    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if LATEST.exists():
        if LATEST.is_symlink():
            LATEST.unlink()
        else:
            shutil.rmtree(LATEST)
    shutil.copytree(out, LATEST, dirs_exist_ok=True)

    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Export NotebookLM upload bundle")
    parser.add_argument(
        "--reports-only",
        action="store_true",
        help="Only copy docs/reports/ (incremental update)",
    )
    parser.add_argument("--no-reports", action="store_true", help="Skip docs/reports/")
    args = parser.parse_args()

    out = build_bundle(reports_only=args.reports_only, include_reports=not args.no_reports)
    print(f"Bundle: {out}")
    print(f"Latest: {LATEST}")
    print("Upload files from corpus/ and reports/ to NotebookLM (Add source).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

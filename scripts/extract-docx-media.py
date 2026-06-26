#!/usr/bin/env python3
"""Extract embedded media from a DOCX file (word/media/*)."""

from __future__ import annotations

import argparse
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract DOCX embedded media")
    parser.add_argument("--input", required=True, help="Path to .docx")
    parser.add_argument("--output", required=True, help="Output directory for media files")
    args = parser.parse_args()

    src = Path(args.input)
    out_dir = Path(args.output)
    if not src.exists():
        print(f"ERROR: not found: {src}", flush=True)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    with zipfile.ZipFile(src, "r") as zf:
        for name in sorted(zf.namelist()):
            if not name.startswith("word/media/"):
                continue
            data = zf.read(name)
            fname = Path(name).name
            dest = out_dir / fname
            dest.write_bytes(data)
            manifest.append(
                {
                    "archive_path": name,
                    "filename": fname,
                    "bytes": len(data),
                    "output": str(dest),
                }
            )

    meta = {
        "source": str(src),
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "count": len(manifest),
        "files": manifest,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(manifest)} files → {out_dir}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

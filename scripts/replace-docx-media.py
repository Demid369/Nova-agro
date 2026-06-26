#!/usr/bin/env python3
"""Replace embedded media files inside a DOCX (same filename in word/media/)."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_media(docx: Path, media_name: str, new_file: Path) -> None:
    if not docx.exists():
        raise FileNotFoundError(docx)
    if not new_file.exists():
        raise FileNotFoundError(new_file)

    tmp = docx.with_suffix(".docx.tmp")
    target = f"word/media/{media_name}"

    with zipfile.ZipFile(docx, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        found = False
        for item in zin.infolist():
            if item.filename == target:
                zout.writestr(item, new_file.read_bytes())
                found = True
            else:
                zout.writestr(item, zin.read(item.filename))
        if not found:
            raise FileNotFoundError(f"{target} not in {docx}")

    tmp.replace(docx)
    print(f"Replaced {target} ← {new_file}")


def replace_all_from_dir(docx: Path, media_dir: Path) -> int:
    count = 0
    for f in sorted(media_dir.iterdir()):
        if f.suffix.lower() in {".jpeg", ".jpg", ".png", ".gif", ".emf", ".wmf"}:
            replace_media(docx, f.name, f)
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Swap DOCX embedded images by filename")
    parser.add_argument("--docx", required=True)
    parser.add_argument("--file", help="Single replacement file")
    parser.add_argument("--name", help="Target media filename e.g. image7.png")
    parser.add_argument("--dir", help="Replace all matching filenames from directory")
    args = parser.parse_args()

    docx = Path(args.docx)
    try:
        if args.dir:
            n = replace_all_from_dir(docx, Path(args.dir))
            print(f"Replaced {n} files")
        elif args.file and args.name:
            replace_media(docx, args.name, Path(args.file))
        else:
            print("Use --file + --name or --dir", file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

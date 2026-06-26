#!/usr/bin/env python3
"""Phase 2: poultry narrative §7, Tab P-141, image captions (binaries unchanged)."""

from __future__ import annotations

import argparse
import glob
import re
import sys
import zipfile
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import yaml

ROOT = Path(__file__).resolve().parents[1]
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "a": A_NS, "r": R_NS}
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"

DEFAULT_PHASE2 = ROOT / "docs/inventory/pticevodstvo/poultry-phase2.yaml"
DEFAULT_RULES = ROOT / "docs/inventory/pticevodstvo/poultry-baseline-replace.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def parse_md_tables(md_path: Path) -> list[list[list[str]]]:
    """Return list of tables; each table is list of rows."""
    text = md_path.read_text(encoding="utf-8")
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|"):
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            current.append(cells)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def parse_narrative_chunks(md_path: Path) -> list[str]:
    chunks: list[str] = []
    skip_prefixes = (">", "`", "Источник:")
    buf: list[str] = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if any(line.strip().startswith(p) for p in skip_prefixes):
            continue
        if line.startswith("#"):
            if buf:
                chunks.append("\n".join(buf))
                buf = []
            chunks.append(line.lstrip("#").strip())
            continue
        if line.startswith("|"):
            if buf:
                chunks.append("\n".join(buf))
                buf = []
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not re.match(r"^[\s\-:|]+$", "|".join(cells)):
                chunks.append(" | ".join(cells))
            continue
        if line.strip() == "":
            if buf:
                chunks.append("\n".join(buf))
                buf = []
            continue
        buf.append(line)
    if buf:
        chunks.append("\n".join(buf))
    # trim to production sections only (stop before duplicate feed/greenhouse if any)
    out: list[str] = []
    for c in chunks:
        if c.startswith("8. Сводный") or c.startswith("### Таблица"):
            break
        out.append(c[:4000])  # Word para sanity
    return out


def para_has_drawing(p: ET.Element) -> bool:
    return bool(p.findall(".//w:drawing", NS))


def para_text(p: ET.Element) -> str:
    return "".join(t.text or "" for t in p.findall(".//w:t", NS))


def set_paragraph_text(p: ET.Element, text: str) -> None:
    for r in list(p.findall("w:r", NS)):
        p.remove(r)
    if not text:
        return
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.text = text
    if text.startswith(" ") or text.endswith(" "):
        t.set(XML_SPACE, "preserve")


def apply_text_rules(text: str, rules: list[dict[str, str]]) -> str:
    out = text
    for rule in rules:
        out = re.sub(rule["pattern"], rule["replace"], out, flags=re.IGNORECASE)
    return out


def build_table_xml(rows: list[list[str]], template_tbl: ET.Element) -> ET.Element:
    tbl = deepcopy(template_tbl)
    # remove existing rows
    for tr in list(tbl.findall("w:tr", NS)):
        tbl.remove(tr)
    width = max(len(r) for r in rows) if rows else 1
    for row_data in rows:
        tr = ET.SubElement(tbl, f"{{{W_NS}}}tr")
        for j in range(width):
            tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
            p = ET.SubElement(tc, f"{{{W_NS}}}p")
            val = row_data[j] if j < len(row_data) else ""
            set_paragraph_text(p, val)
    return tbl


def find_body_children(doc_root: ET.Element) -> list[ET.Element]:
    body = doc_root.find("w:body", NS)
    return list(body)


def apply_phase2(docx_path: Path, phase2_path: Path) -> None:
    cfg = load_yaml(phase2_path)
    narr = cfg.get("narrative", {})
    start = int(narr.get("body_start", 9873))
    end = int(narr.get("body_end", 9952))
    md_narr = ROOT / narr["source"]

    chunks = parse_narrative_chunks(md_narr)
    caption_rules = cfg.get("image_caption_replacements") or []

    with zipfile.ZipFile(docx_path, "r") as zin:
        buf = BytesIO(zin.read("word/document.xml"))
        doc = ET.parse(buf).getroot()
        children = find_body_children(doc)

        # §7 narrative
        text_slots = []
        for i in range(start, end + 1):
            if i >= len(children):
                break
            el = children[i]
            if not el.tag.endswith("p"):
                continue
            if narr.get("preserve_image_paragraphs") and para_has_drawing(el):
                continue
            if para_text(el).strip():
                text_slots.append(i)

        for idx, chunk in zip(text_slots, chunks):
            set_paragraph_text(children[idx], chunk)
        for idx in text_slots[len(chunks) :]:
            set_paragraph_text(children[idx], "")

        # caption rules on all paragraphs + table cell text (never remove drawings)
        for el in children:
            if el.tag.endswith("p") and not para_has_drawing(el):
                old = para_text(el)
                new = apply_text_rules(old, caption_rules)
                if new != old:
                    set_paragraph_text(el, new)
            elif el.tag.endswith("tbl"):
                for tc in el.findall(".//w:tc", NS):
                    if tc.findall(".//w:drawing", NS):
                        continue
                    for p in tc.findall(".//w:p", NS):
                        if para_has_drawing(p):
                            continue
                        old = para_text(p)
                        new = apply_text_rules(old, caption_rules)
                        if new != old:
                            set_paragraph_text(p, new)

        # Tab P-141 title + first rabbit table
        tab = cfg.get("tab141", {})
        search = tab.get("title_body_search", "")
        for i, el in enumerate(children):
            if el.tag.endswith("p") and search in para_text(el):
                set_paragraph_text(el, tab.get("title_replace", para_text(el)))
                # next tbl element
                for j in range(i + 1, min(i + 8, len(children))):
                    if children[j].tag.endswith("tbl"):
                        md = ROOT / tab["md_source"]
                        tables = parse_md_tables(md)
                        if tables:
                            children[j] = build_table_xml(tables[0], children[j])
                        break
                break

        out_xml = ET.tostring(doc, encoding="utf-8", xml_declaration=True)

        out_buf = BytesIO()
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = out_xml
                zout.writestr(item, data)

    docx_path.write_bytes(out_buf.getvalue())
    print(f"Phase2 applied: {docx_path}")
    print(f"  §7 narrative chunks: {len(chunks)} → {len(text_slots)} slots")
    print(f"  Tab P-141: {tab.get('title_replace', '—')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2", default=str(DEFAULT_PHASE2))
    parser.add_argument("--docx", default="")
    args = parser.parse_args()

    phase2 = load_yaml(Path(args.phase2))
    if args.docx:
        docx = Path(args.docx)
    else:
        rules = load_yaml(DEFAULT_RULES)
        docx = ROOT / rules["meta"]["output"]

    if not docx.exists():
        print(f"Missing DOCX: {docx}. Run build-teo-poultry-from-baseline.py first.", file=sys.stderr)
        return 1

    apply_phase2(docx, Path(args.phase2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

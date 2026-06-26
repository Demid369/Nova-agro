#!/usr/bin/env python3
"""Phase 3: §4 market narrative, genetics, yield/world tables (images unchanged)."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import yaml

# Reuse phase2 helpers
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DEFAULT_PHASE3 = ROOT / "docs/inventory/pticevodstvo/pipeline/phase3-market.yaml"
DEFAULT_RULES = ROOT / "docs/inventory/pticevodstvo/pipeline/phase1-tables.yaml"


def _load_phase2():
    import importlib.util

    p2_path = SCRIPTS / "apply-teo-poultry-phase2.py"
    spec = importlib.util.spec_from_file_location("apply_teo_poultry_phase2", p2_path)
    p2 = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(p2)
    return p2


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def find_text_slots(
    children: list[ET.Element],
    start: int,
    end: int,
    preserve_images: bool,
    p2: Any,
) -> list[int]:
    slots: list[int] = []
    for i in range(start, min(end + 1, len(children))):
        el = children[i]
        if not el.tag.endswith("p"):
            continue
        if preserve_images and p2.para_has_drawing(el):
            continue
        if p2.para_text(el).strip():
            slots.append(i)
    return slots


def apply_narrative_block(
    children: list[ET.Element],
    block: dict[str, Any],
    p2: Any,
) -> tuple[str, int, int]:
    start = int(block["body_start"])
    end = int(block["body_end"])
    md_path = ROOT / block["source"]
    chunks = p2.parse_narrative_chunks(md_path)
    preserve = bool(block.get("preserve_image_paragraphs", True))
    slots = find_text_slots(children, start, end, preserve, p2)

    if block.get("clear_slots_first", True):
        for idx in slots:
            p2.set_paragraph_text(children[idx], "")

    for idx, chunk in zip(slots, chunks):
        p2.set_paragraph_text(children[idx], chunk)
    for idx in slots[len(chunks) :]:
        p2.set_paragraph_text(children[idx], "")

    return block.get("name", "?"), len(chunks), len(slots)


def replace_table_by_index(
    body: ET.Element,
    table_index: int,
    title_index: int | None,
    title_replace: str | None,
    md_source: str,
    p2: Any,
) -> bool:
    children = list(body)
    if table_index >= len(children) or not children[table_index].tag.endswith("tbl"):
        return False
    if title_index is not None and title_replace and title_index < len(children):
        p2.set_paragraph_text(children[title_index], title_replace)
    tables = p2.parse_md_tables(ROOT / md_source)
    if not tables:
        return False
    body[table_index] = p2.build_table_xml(tables[0], children[table_index])
    return True


def replace_table_after_paragraph(
    body: ET.Element,
    search: str,
    title_replace: str | None,
    md_source: str,
    p2: Any,
    search_alternatives: list[str] | None = None,
    max_lookahead: int = 80,
) -> bool:
    children = list(body)
    needles = [search] + (search_alternatives or [])
    for i, el in enumerate(children):
        if not el.tag.endswith("p"):
            continue
        text = p2.para_text(el)
        if not any(n in text for n in needles):
            continue
        if title_replace:
            p2.set_paragraph_text(el, title_replace)
        tables = p2.parse_md_tables(ROOT / md_source)
        if not tables:
            return False
        for j in range(i + 1, min(i + max_lookahead, len(children))):
            if children[j].tag.endswith("tbl"):
                body[j] = p2.build_table_xml(tables[0], children[j])
                return True
        return False
    return False


def apply_captions(children: list[ET.Element], rules: list[dict[str, str]], p2: Any) -> int:
    changed = 0
    for el in children:
        if el.tag.endswith("p") and not p2.para_has_drawing(el):
            old = p2.para_text(el)
            new = p2.apply_text_rules(old, rules)
            if new != old:
                p2.set_paragraph_text(el, new)
                changed += 1
        elif el.tag.endswith("tbl"):
            for tc in el.findall(".//w:tc", p2.NS):
                if tc.findall(".//w:drawing", p2.NS):
                    continue
                for p in tc.findall(".//w:p", p2.NS):
                    if p2.para_has_drawing(p):
                        continue
                    old = p2.para_text(p)
                    new = p2.apply_text_rules(old, rules)
                    if new != old:
                        p2.set_paragraph_text(p, new)
                        changed += 1
    return changed


def apply_phase3(docx_path: Path, phase3_path: Path) -> None:
    p2 = _load_phase2()
    cfg = load_yaml(phase3_path)

    with zipfile.ZipFile(docx_path, "r") as zin:
        doc = ET.parse(BytesIO(zin.read("word/document.xml"))).getroot()
        body = doc.find(f"{{{p2.W_NS}}}body")
        assert body is not None
        children = list(body)

        block_stats: list[str] = []
        for block in cfg.get("narrative_blocks") or []:
            name, n_chunks, n_slots = apply_narrative_block(children, block, p2)
            block_stats.append(f"{name}: {n_chunks}→{n_slots}")

        table_stats: list[str] = []
        deferred_tables: list[dict[str, Any]] = []
        for tab in cfg.get("table_replacements") or []:
            if tab.get("after_section7_reapply"):
                deferred_tables.append(tab)
                continue
            if tab.get("body_table_index") is not None:
                ok = replace_table_by_index(
                    body,
                    int(tab["body_table_index"]),
                    int(tab["title_body_index"]) if tab.get("title_body_index") is not None else None,
                    tab.get("title_replace"),
                    tab["md_source"],
                    p2,
                )
            else:
                ok = replace_table_after_paragraph(
                    body,
                    tab["search_paragraph"],
                    tab.get("title_replace"),
                    tab["md_source"],
                    p2,
                    search_alternatives=tab.get("search_alternatives"),
                    max_lookahead=int(tab.get("max_lookahead", 80)),
                )
            table_stats.append(f"{tab.get('name', '?')}: {'OK' if ok else 'MISS'}")

        captions = apply_captions(children, cfg.get("caption_replacements") or [], p2)

        # Re-apply §7 narrative last — phase2 captions can collide with §7 slots
        reapply = cfg.get("reapply_phase2_narrative")
        if reapply:
            p2_cfg = load_yaml(ROOT / reapply["config"])
            narr = p2_cfg.get("narrative", {})
            block = {
                "name": "section7_reapply",
                "body_start": int(narr.get("body_start", 9873)),
                "body_end": int(narr.get("body_end", 9952)),
                "source": narr["source"],
                "preserve_image_paragraphs": narr.get("preserve_image_paragraphs", True),
                "clear_slots_first": True,
            }
            name, n_chunks, n_slots = apply_narrative_block(children, block, p2)
            block_stats.append(f"{name}: {n_chunks}→{n_slots} (reapply)")

        for tab in deferred_tables:
            if tab.get("body_table_index") is not None:
                ok = replace_table_by_index(
                    body,
                    int(tab["body_table_index"]),
                    int(tab["title_body_index"]) if tab.get("title_body_index") is not None else None,
                    tab.get("title_replace"),
                    tab["md_source"],
                    p2,
                )
            else:
                ok = replace_table_after_paragraph(
                    body,
                    tab["search_paragraph"],
                    tab.get("title_replace"),
                    tab["md_source"],
                    p2,
                    search_alternatives=tab.get("search_alternatives"),
                    max_lookahead=int(tab.get("max_lookahead", 80)),
                )
            table_stats.append(f"{tab.get('name', '?')}: {'OK' if ok else 'MISS'}")

        out_xml = ET.tostring(doc, encoding="utf-8", xml_declaration=True)
        out_buf = BytesIO()
        with zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = out_xml if item.filename == "word/document.xml" else zin.read(item.filename)
                zout.writestr(item, data)

    docx_path.write_bytes(out_buf.getvalue())
    print(f"Phase3 applied: {docx_path}")
    for line in block_stats:
        print(f"  narrative {line}")
    for line in table_stats:
        print(f"  table {line}")
    print(f"  caption rules changed: {captions}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase3", default=str(DEFAULT_PHASE3))
    parser.add_argument("--docx", default="")
    args = parser.parse_args()

    if args.docx:
        docx = Path(args.docx)
    else:
        rules = load_yaml(DEFAULT_RULES)
        docx = ROOT / rules["meta"]["output"]

    if not docx.exists():
        print(f"Missing DOCX: {docx}. Run build-teo-poultry-from-baseline.py first.", file=sys.stderr)
        return 1

    apply_phase3(docx, Path(args.phase3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

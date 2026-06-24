#!/usr/bin/env python3
"""Generate DOCX files per rabbit-farming theme from docs/inventory/krolikovodstvo/registry.yaml."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from krolikovodstvo_inventory import (
    DOCX_DIR,
    INVENTORY_DIR,
    REPORTS_DIR,
    gather_theme_content,
    load_registry,
)

MAX_BODY_CHARS = 120_000


def add_meta(doc: Document, subtitle: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"Проект «МОЯ МЕЧТА» | baseline кролиководство | {date.today().isoformat()}")
    r.italic = True
    r.font.size = Pt(10)
    if subtitle:
        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = p2.add_run(subtitle)
        r2.font.size = Pt(10)
    doc.add_paragraph()


def write_blocks(doc: Document, chunks: list[tuple[str, str]]) -> None:
    for header, body in chunks:
        doc.add_heading(header, level=2)
        text = body if len(body) <= MAX_BODY_CHARS else body[:MAX_BODY_CHARS] + "\n\n[… обрезано …]"
        for para in text.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            if para.startswith("#"):
                level = len(para) - len(para.lstrip("#"))
                title = para.lstrip("#").strip()
                doc.add_heading(title, level=min(level + 1, 4))
            else:
                doc.add_paragraph(para)


def build_theme_docx(theme_id: str, theme: dict) -> Path:
    DOCX_DIR.mkdir(parents=True, exist_ok=True)
    out = DOCX_DIR / theme["docx"]
    doc = Document()
    title = doc.add_heading(f"{theme_id}. {theme['name']}", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_meta(doc, theme.get("description", ""))

    doc.add_heading("Действие при замене блока", level=1)
    doc.add_paragraph(f"action_on_replace: {theme.get('action_on_replace', 'replace')}")

    chunks = gather_theme_content(theme)
    if not chunks:
        doc.add_paragraph("Нет извлечённых фрагментов — проверьте registry.yaml.")
    else:
        doc.add_heading("Содержание по источникам", level=1)
        write_blocks(doc, chunks)

    doc.save(out)
    return out


def build_index_docx(registry: dict) -> Path:
    DOCX_DIR.mkdir(parents=True, exist_ok=True)
    out = DOCX_DIR / "00-index-krolikovodstvo.docx"
    doc = Document()
    t = doc.add_heading("Инвентарь кролиководства — оглавление", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_meta(doc, "Все направления для будущей замены в новом ТЭО")

    doc.add_heading("Канонические KPI блока", level=1)
    facts = registry.get("canonical_facts", {})
    table = doc.add_table(rows=1, cols=2)
    table.style = "Table Grid"
    table.rows[0].cells[0].text = "Параметр"
    table.rows[0].cells[1].text = "Значение"
    for k, v in facts.items():
        row = table.add_row().cells
        row[0].text = str(k)
        row[1].text = str(v)
    doc.add_paragraph()

    doc.add_heading("DOCX по направлениям", level=1)
    for tid in sorted(k for k in registry.get("themes", {}) if k.startswith("T")):
        th = registry["themes"][tid]
        doc.add_paragraph(f"{tid} — {th['name']}: {th['docx']}", style="List Bullet")

    doc.add_heading("Все файлы-источники (замена)", level=1)
    all_files = registry.get("all_source_files", {})
    for group, files in all_files.items():
        doc.add_heading(group, level=2)
        for f in files:
            doc.add_paragraph(f, style="List Bullet")

    doc.save(out)
    return out


def main() -> None:
    registry = load_registry()
    paths: list[Path] = [build_index_docx(registry)]
    for tid in sorted(k for k in registry.get("themes", {}) if k.startswith("T")):
        paths.append(build_theme_docx(tid, registry["themes"][tid]))
    print(f"Generated {len(paths)} DOCX in {DOCX_DIR.relative_to(INVENTORY_DIR.parent.parent)}")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()

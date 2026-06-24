"""Shared helpers for rabbit-farming inventory (docs/inventory/krolikovodstvo)."""

from __future__ import annotations

import json
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_DIR = ROOT / "docs" / "inventory" / "krolikovodstvo"
REGISTRY_PATH = INVENTORY_DIR / "registry.yaml"
DOCX_DIR = INVENTORY_DIR / "docx"
REPORTS_DIR = INVENTORY_DIR / "reports"

RABBIT_RE = re.compile(
    r"кролик|крольчат|кроликовод|Meneghin|ANCI|крольчих",
    re.I,
)


def load_registry() -> dict[str, Any]:
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


def resolve_path(rel: str) -> Path:
    return ROOT / rel


def read_text(rel: str) -> str:
    path = resolve_path(rel)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown by # headings; returns (heading, body) pairs."""
    parts = re.split(r"(?m)^(#{1,6}\s+.+)$", text)
    if not parts:
        return [("", text)]
    sections: list[tuple[str, str]] = []
    if parts[0].strip():
        sections.append(("", parts[0].strip()))
    i = 1
    while i < len(parts) - 1:
        heading = parts[i].strip()
        body = parts[i + 1].strip()
        sections.append((heading, body))
        i += 2
    return sections


def extract_by_sections(text: str, patterns: list[str]) -> str:
    if not patterns:
        return ""
    compiled = [re.compile(p, re.I) for p in patterns]
    blocks: list[str] = []
    for heading, body in split_sections(text):
        label = f"{heading}\n{body[:200]}"
        if any(c.search(label) for c in compiled):
            block = f"{heading}\n\n{body}".strip() if heading else body
            if block:
                blocks.append(block)
    return "\n\n---\n\n".join(blocks)


def extract_by_keywords(text: str, keywords: list[str], context_lines: int = 2) -> str:
    if not keywords:
        return ""
    compiled = [re.compile(str(k), re.I) for k in keywords]
    lines = text.splitlines()
    picked: set[int] = set()
    for i, line in enumerate(lines):
        if any(c.search(line) for c in compiled):
            for j in range(max(0, i - context_lines), min(len(lines), i + context_lines + 1)):
                picked.add(j)
    if not picked:
        return ""
    out: list[str] = []
    prev = -2
    for idx in sorted(picked):
        if idx > prev + 1 and out:
            out.append("")
        out.append(lines[idx])
        prev = idx
    return "\n".join(out)


def extract_source_content(source: dict[str, Any]) -> tuple[str, str]:
    """Return (label, extracted_text) for one registry source entry."""
    rel = source.get("file", "")
    if not rel:
        return ("", "")

    path = resolve_path(rel)
    label = rel
    if not path.exists():
        return (label, f"[ФАЙЛ НЕ НАЙДЕН: {rel}]")

    text = path.read_text(encoding="utf-8", errors="replace")
    role = source.get("role", "")

    # Dedicated rabbit teo files — full text
    if role == "source_teo" and RABBIT_RE.search(path.name):
        return (label, text.strip())

    sections = source.get("sections")
    if sections:
        block = extract_by_sections(text, sections)
        if block:
            return (label, block)

    keywords = source.get("keywords")
    if keywords:
        block = extract_by_keywords(text, keywords, context_lines=3)
        if block:
            return (label, block)

    # Structured yaml/json
    if rel.endswith((".yaml", ".yml")):
        data = yaml.safe_load(text)
        sub = source.get("path", "")
        if sub and isinstance(data, dict):
            node: Any = data
            for part in sub.split("."):
                if part == "blocks":
                    continue
                if isinstance(node, dict):
                    node = node.get(part, {})
            return (label, yaml.dump(node, allow_unicode=True, sort_keys=False))
        return (label, text.strip())

    if rel.endswith(".json"):
        data = json.loads(text)
        sub = source.get("path", "")
        if sub and isinstance(data, dict):
            node = data
            for part in sub.split("."):
                if part == "blocks":
                    continue
                if isinstance(node, dict):
                    node = node.get(part, {})
            return (label, json.dumps(node, ensure_ascii=False, indent=2))
        return (label, text.strip())

    # Fallback: rabbit-related paragraphs only for large files
    if len(text) > 8000:
        block = extract_by_keywords(text, [r"кролик", r"кроль", r"Meneghin", r"ANCI"], context_lines=4)
        return (label, block or "[нет совпадений по ключевым словам]")

    if RABBIT_RE.search(text):
        return (label, text.strip())

    return (label, "[нет релевантного фрагмента]")


def gather_theme_content(theme: dict[str, Any]) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    for src in theme.get("sources", []):
        label, body = extract_source_content(src)
        if body and body not in ("[нет релевантного фрагмента]", ""):
            note = src.get("note")
            header = f"Источник: {label}"
            if note:
                header += f" ({note})"
            chunks.append((header, body))
    return chunks

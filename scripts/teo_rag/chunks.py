"""Chunk collection and splitting for TEO RAG."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import (
    CHUNK_OVERLAP,
    CORPUS_DETAIL,
    CORPUS_SUMMARY,
    MARKET_FILE_HINT,
    MAX_CHUNK_CHARS,
    ROOT,
)

TRADE_FILE_RE = re.compile(r"табл[_-]\d+", re.I)
STAT_FILE_RE = re.compile(r"(\d{4}[-–]\d{4}-гг-|в-\d{4}-\d{4}-гг-)", re.I)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")

BLOCK_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"кролик", re.I), "кролиководство"),
    (re.compile(r"теплиц|огурц|цветовод", re.I), "теплицы"),
    (re.compile(r"животновод|крс|мрс|овец|кьянин|лимузин|фризон|меринос", re.I), "животноводство"),
    (re.compile(r"рыб|осетр|икр|белуг|узв", re.I), "рыбоводство"),
    (re.compile(r"масл|маргарин|желатин|кож|шрот|подсолнеч", re.I), "масложировой"),
    (re.compile(r"биогаз|солнечн|энерг|электро", re.I), "энергия"),
    (re.compile(r"финанс|npv|irr|бюджет|окупаем", re.I), "финансы"),
    (re.compile(r"риск", re.I), "риски"),
    (re.compile(r"rynok|analitika|экспорт|импорт|рынок|сбыт|маркетинг", re.I), "рынок"),
    (re.compile(r"производств|технолог|схем", re.I), "производство"),
    (re.compile(r"00-summary|01-vvedenie|resume|моя мечта", re.I), "ядро"),
]


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    tier: str
    block: str
    section: str
    section_level: int
    word_count: int
    has_tables: bool
    project_relevant: bool
    char_start: int
    char_end: int
    metadata: dict = field(default_factory=dict)

    def to_metadata(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "tier": self.tier,
            "block": self.block,
            "section": self.section,
            "section_level": self.section_level,
            "word_count": self.word_count,
            "has_tables": self.has_tables,
            "project_relevant": self.project_relevant,
            "char_start": self.char_start,
            "char_end": self.char_end,
        }


def slugify(text: str, max_len: int = 48) -> str:
    s = re.sub(r"[^a-z0-9а-яё]+", "_", text.lower(), flags=re.I)[:max_len].strip("_")
    if not s:
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        s = f"x_{digest}"
    return s


def is_trade_stat_file(path: Path) -> bool:
    name = path.stem.lower()
    # Проектные таблицы/рецепты (кролики, комбикорм) — не отфильтровывать
    if re.search(r"кролик|крольчат|комбикорм.*кролик|рецепт.*кролик", name):
        return False
    if TRADE_FILE_RE.search(name):
        return True
    if STAT_FILE_RE.search(name):
        return True
    if "весь-мир" in name and "табл" in name:
        return True
    if name.startswith("экспорт-товаров-группы"):
        return True
    return False


def infer_block(path: Path, section: str = "") -> str:
    hay = f"{path.stem} {section}".lower()
    for pattern, block in BLOCK_RULES:
        if pattern.search(hay):
            return block
    if path.parent.name == "graphify-corpus":
        stem = path.stem.lower()
        if stem.startswith("04-"):
            return "рынок"
        if stem.startswith("05-"):
            return "финансы"
        if stem.startswith("06-"):
            return "риски"
        if stem.startswith("03-"):
            return "производство"
        return "ядро"
    return "прочее"


def rel_source(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def has_tables(text: str) -> bool:
    return "||" in text or bool(re.search(r"\|.+\|", text))


def split_long_text(text: str, max_chars: int, overlap: int) -> list[tuple[str, int, int]]:
    if len(text) <= max_chars:
        return [(text, 0, len(text))]

    parts: list[tuple[str, int, int]] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            break_at = text.rfind("\n\n", start + max_chars // 2, end)
            if break_at == -1:
                break_at = text.rfind(" ", start + max_chars // 2, end)
            if break_at > start:
                end = break_at
        chunk = text[start:end].strip()
        if chunk:
            parts.append((chunk, start, end))
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return parts or [(text[:max_chars], 0, min(max_chars, len(text)))]


def split_by_headings(text: str) -> list[tuple[str, int, str, int]]:
    """Return (section_title, level, body, char_offset)."""
    lines = text.splitlines(keepends=True)
    sections: list[tuple[str, int, str, int]] = []
    current_title = "(начало)"
    current_level = 1
    current_lines: list[str] = []
    offset = 0
    section_start = 0

    for line in lines:
        m = HEADING_RE.match(line.strip())
        if m:
            if current_lines:
                body = "".join(current_lines).strip()
                if body:
                    sections.append((current_title, current_level, body, section_start))
            current_level = len(m.group(1))
            current_title = m.group(2).strip()
            current_lines = []
            section_start = offset
        else:
            current_lines.append(line)
        offset += len(line)

    body = "".join(current_lines).strip()
    if body:
        sections.append((current_title, current_level, body, section_start))
    if not sections and text.strip():
        sections.append(("(весь файл)", 1, text.strip(), 0))
    return sections


def make_chunk_id(source: str, section: str, index: int, char_start: int) -> str:
    return f"{source}::{slugify(section)}::{char_start}::{index}"


def chunk_file(path: Path, tier: str) -> list[Chunk]:
    if path.name.lower() == "readme.md":
        return []

    text = path.read_text(encoding="utf-8", errors="replace")
    trade_stat = is_trade_stat_file(path)
    if trade_stat:
        return []

    source = rel_source(path)
    is_market = MARKET_FILE_HINT in path.stem.lower() or "rynok" in source
    max_chars = MAX_CHUNK_CHARS if is_market else MAX_CHUNK_CHARS * 2

    chunks: list[Chunk] = []
    for section_title, level, body, base_offset in split_by_headings(text):
        block = infer_block(path, section_title)
        parts = (
            split_long_text(body, max_chars, CHUNK_OVERLAP)
            if is_market and len(body) > max_chars
            else [(body, 0, len(body))]
        )
        for idx, (part_text, part_start, part_end) in enumerate(parts):
            char_start = base_offset + part_start
            char_end = base_offset + part_end
            chunk_id = make_chunk_id(source, section_title, idx, char_start)
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    text=part_text,
                    source=source,
                    tier=tier,
                    block=block,
                    section=section_title,
                    section_level=level,
                    word_count=len(part_text.split()),
                    has_tables=has_tables(part_text),
                    project_relevant=True,
                    char_start=char_start,
                    char_end=char_end,
                )
            )
    return chunks


def collect_chunks() -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for path in sorted(CORPUS_SUMMARY.glob("*.md")):
        all_chunks.extend(chunk_file(path, tier="summary"))
    for path in sorted(CORPUS_DETAIL.glob("*.md")):
        all_chunks.extend(chunk_file(path, tier="detail"))
    return all_chunks

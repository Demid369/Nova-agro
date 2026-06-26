"""Shared helpers for rabbit-farming inventory (docs/inventory/krolikovodstvo)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_DIR = ROOT / "docs" / "inventory" / "krolikovodstvo"
REGISTRY_PATH = INVENTORY_DIR / "registry.yaml"
DOCX_DIR = INVENTORY_DIR / "docx"
REPORTS_DIR = INVENTORY_DIR / "reports"
AUDIT_JSON_PATH = REPORTS_DIR / "docx-audit.json"
BASELINE_PATH = ROOT / "docs" / "scenarios" / "baseline.yaml"

RABBIT_RE = re.compile(
    r"кролик|крольчат|кроликовод|Meneghin|ANCI|крольчих",
    re.I,
)
HS_TABLE_RE = re.compile(r"табл[_-]\d+|весь-мир|экспорт-товаров-группы", re.I)

AUDIT_FILE_GROUPS = (
    "project_corpus",
    "source_teo_primary",
    "source_teo_secondary",
    "structured",
)


class RegistryValidationError(Exception):
    """registry.yaml failed schema/consistency checks."""


@dataclass
class SourceFragment:
    file: str
    line_start: int
    line_end: int
    text: str
    note: str | None = None

    @property
    def ref(self) -> str:
        if self.line_start == self.line_end:
            return f"{self.file}:{self.line_start}"
        return f"{self.file}:{self.line_start}–{self.line_end}"


@dataclass
class ThemeChunk:
    header: str
    fragments: list[SourceFragment] = field(default_factory=list)

    @property
    def refs(self) -> list[str]:
        return [f.ref for f in self.fragments]


def load_registry() -> dict[str, Any]:
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


def resolve_path(rel: str) -> Path:
    return ROOT / rel


def read_text(rel: str) -> str:
    path = resolve_path(rel)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def line_count(text: str) -> int:
    return len(text.splitlines()) or 1


def lines_to_range(lines: list[str], indices: set[int]) -> tuple[int, int]:
    if not indices:
        return (1, 1)
    start = min(indices) + 1
    end = max(indices) + 1
    return start, end


def find_section_line_range(text: str, heading: str, body: str) -> tuple[int, int]:
    lines = text.splitlines()
    heading_plain = heading.lstrip("#").strip()
    start = 1
    for i, line in enumerate(lines):
        if heading and heading_plain and heading_plain.lower() in line.lower():
            start = i + 1
            break
    end = start
    if body:
        probe = body[:80].strip()
        for i, line in enumerate(lines):
            if probe and probe in line:
                start = i + 1
                break
        end = min(start + body.count("\n"), line_count(text))
    else:
        end = min(start + 20, line_count(text))
    return start, max(end, start)


def split_sections(text: str) -> list[tuple[str, str, int]]:
    """Return (heading, body, heading_line_1based)."""
    lines = text.splitlines()
    sections: list[tuple[str, str, int]] = []
    current_heading = ""
    current_start = 1
    current_lines: list[str] = []

    for i, line in enumerate(lines):
        if re.match(r"^#{1,6}\s+", line):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body or current_heading:
                    sections.append((current_heading, body, current_start))
            current_heading = line.strip()
            current_start = i + 1
            current_lines = []
        else:
            current_lines.append(line)

    body = "\n".join(current_lines).strip()
    if body or current_heading:
        sections.append((current_heading, body, current_start))
    if not sections and text.strip():
        sections.append(("", text.strip(), 1))
    return sections


def extract_fragments_by_sections(text: str, rel: str, patterns: list[str]) -> list[SourceFragment]:
    if not patterns:
        return []
    compiled = [re.compile(str(p), re.I) for p in patterns]
    frags: list[SourceFragment] = []
    lines = text.splitlines()
    for heading, body, start_line in split_sections(text):
        label = f"{heading}\n{body[:200]}"
        if not any(c.search(label) for c in compiled):
            continue
        block = f"{heading}\n\n{body}".strip() if heading else body
        end_line = start_line
        if body:
            end_line = start_line + len(body.splitlines())
            if heading:
                end_line += 0  # body lines only after heading line
        else:
            end_line = start_line
        end_line = min(max(end_line, start_line), len(lines))
        frags.append(
            SourceFragment(
                file=rel,
                line_start=start_line,
                line_end=end_line,
                text=block,
            )
        )
    return frags


def extract_fragments_by_keywords(
    text: str,
    rel: str,
    keywords: list[str],
    context_lines: int = 3,
) -> list[SourceFragment]:
    if not keywords:
        return []
    compiled = [re.compile(str(k), re.I) for k in keywords]
    lines = text.splitlines()
    picked: set[int] = set()
    for i, line in enumerate(lines):
        if any(c.search(line) for c in compiled):
            for j in range(max(0, i - context_lines), min(len(lines), i + context_lines + 1)):
                picked.add(j)
    if not picked:
        return []

    # Group contiguous line ranges
    frags: list[SourceFragment] = []
    sorted_idx = sorted(picked)
    range_start = sorted_idx[0]
    prev = sorted_idx[0]
    ranges: list[tuple[int, int]] = []
    for idx in sorted_idx[1:]:
        if idx > prev + 1:
            ranges.append((range_start, prev))
            range_start = idx
        prev = idx
    ranges.append((range_start, prev))

    for a, b in ranges:
        chunk_lines = lines[a : b + 1]
        frags.append(
            SourceFragment(
                file=rel,
                line_start=a + 1,
                line_end=b + 1,
                text="\n".join(chunk_lines),
            )
        )
    return frags


def _extract_graph_rabbit_fragments(text: str, rel: str, note: str | None) -> list[SourceFragment]:
    """Pull rabbit-related nodes/edges from graph.json — not the whole file."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return [SourceFragment(file=rel, line_start=0, line_end=0, text="[graph.json parse error]", note=note)]
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    hits: list[str] = []
    for n in nodes:
        label = n.get("label", "")
        if RABBIT_RE.search(label):
            src = n.get("source", "")
            hits.append(f"• {label} ← {src}")
    for e in edges:
        blob = f"{e.get('source','')} {e.get('relation','')} {e.get('target','')}"
        if RABBIT_RE.search(blob):
            hits.append(f"  {e.get('source')} --{e.get('relation')}--> {e.get('target')}")
    body = "\n".join(hits[:80]) if hits else "[нет узлов кролиководства в graph.json]"
    if len(hits) > 80:
        body += f"\n\n… ещё {len(hits) - 80} связей"
    return [
        SourceFragment(
            file=rel,
            line_start=1,
            line_end=min(len(hits), 80),
            text=body,
            note=(note or "") + " только узлы/рёбра кроликов",
        )
    ]


def extract_source_fragments(source: dict[str, Any]) -> list[SourceFragment]:
    rel = source.get("file", "")
    if not rel:
        return []

    path = resolve_path(rel)
    note = source.get("note")
    if not path.exists():
        return [
            SourceFragment(
                file=rel,
                line_start=0,
                line_end=0,
                text=f"[ФАЙЛ НЕ НАЙДЕН: {rel}]",
                note=note,
            )
        ]

    text = path.read_text(encoding="utf-8", errors="replace")
    role = source.get("role", "")
    n_lines = line_count(text)

    if role == "source_teo" and RABBIT_RE.search(path.name):
        return [
            SourceFragment(
                file=rel,
                line_start=1,
                line_end=n_lines,
                text=text.strip(),
                note=note,
            )
        ]

    sections = source.get("sections")
    keywords = source.get("keywords")
    merged: list[SourceFragment] = []
    if sections:
        merged.extend(extract_fragments_by_sections(text, rel, sections))
    if keywords:
        merged.extend(extract_fragments_by_keywords(text, rel, keywords, context_lines=3))
    if merged:
        for f in merged:
            f.note = note
        return merged

    if rel.endswith((".yaml", ".yml")):
        data = yaml.safe_load(text)
        sub = source.get("path", "")
        body = text.strip()
        if sub and isinstance(data, dict):
            node: Any = data
            for part in sub.split("."):
                if part == "blocks":
                    continue
                if isinstance(node, dict):
                    node = node.get(part, {})
            body = yaml.dump(node, allow_unicode=True, sort_keys=False)
        return [SourceFragment(file=rel, line_start=1, line_end=n_lines, text=body, note=note)]

    if rel.endswith(".json"):
        if "graph.json" in rel.replace("\\", "/"):
            return _extract_graph_rabbit_fragments(text, rel, note)
        data = json.loads(text)
        sub = source.get("path", "")
        body = text.strip()
        if sub and isinstance(data, dict):
            node = data
            for part in sub.split("."):
                if part == "blocks":
                    continue
                if isinstance(node, dict):
                    node = node.get(part, {})
            body = json.dumps(node, ensure_ascii=False, indent=2)
        return [SourceFragment(file=rel, line_start=1, line_end=n_lines, text=body, note=note)]

    if len(text) > 8000:
        frags = extract_fragments_by_keywords(
            text,
            rel,
            [r"кролик", r"кроль", r"Meneghin", r"ANCI"],
            context_lines=4,
        )
        if frags:
            for f in frags:
                f.note = note
            return frags
        return [
            SourceFragment(
                file=rel,
                line_start=0,
                line_end=0,
                text="[нет совпадений по ключевым словам]",
                note=note,
            )
        ]

    if RABBIT_RE.search(text):
        return [
            SourceFragment(
                file=rel,
                line_start=1,
                line_end=n_lines,
                text=text.strip(),
                note=note,
            )
        ]

    return []


def gather_theme_content(theme: dict[str, Any]) -> list[ThemeChunk]:
    by_file: dict[str, ThemeChunk] = {}
    for src in theme.get("sources", []):
        frags = extract_source_fragments(src)
        if not frags:
            continue
        rel = src.get("file", "?")
        if rel not in by_file:
            header = f"Источник: {rel}"
            if src.get("note"):
                header += f" ({src['note']})"
            by_file[rel] = ThemeChunk(header=header)
        by_file[rel].fragments.extend(frags)

    return list(by_file.values())


def canonical_fact_refs(registry: dict[str, Any]) -> list[dict[str, str]]:
    """Map canonical KPI to file:line in corpus (for index DOCX)."""
    anchors = [
        ("output_t_per_year", r"7\s*000", "docs/graphify-corpus/00-summary.md"),
        ("capex_bln_rub", r"\|\s*Кролиководство\s*\|\s*12", "docs/graphify-corpus/00-summary.md"),
        ("npv_thousand_rub", r"2\s*779\s*519", "docs/graphify-corpus/00-summary.md"),
        ("irr_pct", r"15,19", "docs/graphify-corpus/00-summary.md"),
        ("payback_months", r"\|\s*Кролиководство\s*\|[^|]+\|[^|]+\|\s*84", "docs/graphify-corpus/00-summary.md"),
        ("equipment", r"Meneghin", "docs/graphify-corpus/01-vvedenie-i-resume.md"),
        ("slaughter_heads_per_hour", r"2400 голов", "docs/graphify-corpus/01-vvedenie-i-resume.md"),
        ("manure_t_per_year", r"43\s*800", "docs/graphify-corpus/01-vvedenie-i-resume.md"),
        ("genetics", r"ANCI", "docs/graphify-corpus/01-vvedenie-i-resume.md"),
    ]
    rows: list[dict[str, str]] = []
    facts = registry.get("canonical_facts", {})
    for key, pattern, rel in anchors:
        text = read_text(rel)
        line_no = "—"
        if text:
            rx = re.compile(pattern, re.I)
            for i, line in enumerate(text.splitlines(), start=1):
                if rx.search(line):
                    line_no = str(i)
                    break
        rows.append(
            {
                "fact": key,
                "label": str(facts.get(key, key)),
                "ref": f"{rel}:{line_no}" if line_no != "—" else rel,
            }
        )
    return rows


def flatten_all_source_files(registry: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for files in registry.get("all_source_files", {}).values():
        out.update(files)
    return out


def collect_theme_source_files(registry: dict[str, Any]) -> set[str]:
    files: set[str] = set()
    for theme in registry.get("themes", {}).values():
        for src in theme.get("sources", []):
            rel = src.get("file")
            if rel:
                files.add(rel.replace("\\", "/"))
    return files


def duplicates_by_teo(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["teo"].replace("\\", "/"): row
        for row in registry.get("duplicates_map", [])
        if row.get("teo")
    }


def registry_hash(registry: dict[str, Any]) -> str:
    payload = yaml.dump(registry, allow_unicode=True, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def validate_registry(registry: dict[str, Any] | None = None) -> list[str]:
    """Return list of validation errors (empty = OK)."""
    registry = registry or load_registry()
    errors: list[str] = []

    all_files = flatten_all_source_files(registry)
    theme_files = collect_theme_source_files(registry)
    dup_map = duplicates_by_teo(registry)

    for row in registry.get("duplicates_map", []):
        teo = row.get("teo", "").replace("\\", "/")
        if teo and teo not in all_files:
            errors.append(f"duplicates_map teo not in all_source_files: {teo}")
        in_docx = bool(row.get("in_docx"))
        in_themes = teo in theme_files
        if not in_docx and in_themes:
            errors.append(f"duplicates_map in_docx=false but teo in themes.sources: {teo}")
        if in_docx and not in_themes and row.get("status") != "episodic":
            errors.append(f"duplicates_map in_docx=true but teo missing from themes.sources: {teo}")

    for tid, theme in registry.get("themes", {}).items():
        if not theme.get("action_on_replace"):
            errors.append(f"theme {tid} missing action_on_replace")
        if not theme.get("docx"):
            errors.append(f"theme {tid} missing docx filename")

    if not BASELINE_PATH.exists():
        errors.append(f"baseline missing: {BASELINE_PATH}")
    else:
        baseline = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8"))
        block = baseline.get("blocks", {}).get("кролиководство", {})
        facts = registry.get("canonical_facts", {})
        checks: list[tuple[str, bool, str]] = [
            (
                "output_t_per_year",
                str(facts.get("output_t_per_year", "")) in block.get("output", "").replace(" ", ""),
                f"registry={facts.get('output_t_per_year')} baseline output={block.get('output')}",
            ),
            (
                "capex_bln_rub",
                facts.get("capex_bln_rub") == block.get("capex_bln_rub"),
                f"registry={facts.get('capex_bln_rub')} baseline={block.get('capex_bln_rub')}",
            ),
            (
                "npv_thousand_rub",
                facts.get("npv_thousand_rub") == block.get("npv_thousand_rub"),
                f"registry={facts.get('npv_thousand_rub')} baseline={block.get('npv_thousand_rub')}",
            ),
            (
                "irr_pct",
                float(facts.get("irr_pct", 0)) == float(block.get("irr_pct", -1)),
                f"registry={facts.get('irr_pct')} baseline={block.get('irr_pct')}",
            ),
            (
                "payback_months",
                facts.get("payback_months") == block.get("payback_months"),
                f"registry={facts.get('payback_months')} baseline={block.get('payback_months')}",
            ),
        ]
        for key, ok, detail in checks:
            if not ok:
                errors.append(f"canonical_facts.{key} != baseline.yaml blocks.кролиководство ({detail})")

    return errors


def assert_registry_valid(registry: dict[str, Any] | None = None) -> None:
    errors = validate_registry(registry)
    if errors:
        raise RegistryValidationError("\n".join(errors))


def gather_all_theme_fragments(registry: dict[str, Any]) -> dict[str, list[SourceFragment]]:
    """theme_id -> fragments (T13 excluded — duplicates table only)."""
    out: dict[str, list[SourceFragment]] = {}
    for tid, theme in registry.get("themes", {}).items():
        if tid == "T13":
            continue
        frags: list[SourceFragment] = []
        for src in theme.get("sources", []):
            frags.extend(extract_source_fragments(src))
        out[tid] = frags
    return out


def _line_covered(line_no: int, theme_frags: dict[str, list[SourceFragment]], rel: str) -> list[str]:
    themes: list[str] = []
    for tid, frags in theme_frags.items():
        for f in frags:
            if f.file.replace("\\", "/") != rel:
                continue
            if f.line_start <= 0:
                continue
            if f.line_start <= line_no <= f.line_end:
                themes.append(tid)
                break
    return themes


def _classify_uncovered(
    rel: str,
    dup: dict[str, Any] | None,
) -> str:
    if dup:
        status = dup.get("status", "")
        if status == "episodic":
            return "episodic"
        if status == "duplicate" and not dup.get("in_docx"):
            return "duplicate"
        if status == "partial" and not dup.get("in_docx"):
            return "partial-duplicate"
    name = Path(rel).name
    if HS_TABLE_RE.search(name):
        return "HS-table"
    if dup and dup.get("status") == "partial":
        return "partial"
    return "uncovered"


def build_docx_audit(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or load_registry()
    theme_frags = gather_all_theme_fragments(registry)
    dup_map = duplicates_by_teo(registry)

    lines_out: list[dict[str, Any]] = []
    by_reason: dict[str, int] = {}
    covered_count = 0

    all_files = registry.get("all_source_files", {})
    for group in AUDIT_FILE_GROUPS:
        for rel in all_files.get(group, []):
            rel = rel.replace("\\", "/")
            text = read_text(rel)
            if not text:
                continue
            dup = dup_map.get(rel)
            for i, line in enumerate(text.splitlines(), start=1):
                if not RABBIT_RE.search(line):
                    continue
                ref = f"{rel}:{i}"
                themes = _line_covered(i, theme_frags, rel)
                if themes:
                    covered = True
                    reason = None
                    covered_count += 1
                else:
                    covered = False
                    reason = _classify_uncovered(rel, dup)
                    by_reason[reason] = by_reason.get(reason, 0) + 1
                lines_out.append(
                    {
                        "ref": ref,
                        "file": rel,
                        "line": i,
                        "themes": themes,
                        "covered": covered,
                        "reason": reason,
                    }
                )

    total = len(lines_out)
    intentional = sum(by_reason.get(r, 0) for r in ("duplicate", "episodic", "partial-duplicate", "HS-table", "partial"))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_hash": registry_hash(registry),
        "summary": {
            "total_mention_lines": total,
            "covered": covered_count,
            "intentional_gaps": intentional,
            "unexpected_gaps": by_reason.get("uncovered", 0),
            "by_reason": by_reason,
        },
        "lines": lines_out,
    }


def write_docx_audit(registry: dict[str, Any] | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    audit = build_docx_audit(registry)
    AUDIT_JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return AUDIT_JSON_PATH

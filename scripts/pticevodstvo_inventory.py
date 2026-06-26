"""Shared helpers for poultry inventory (docs/inventory/pticevodstvo)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_DIR = ROOT / "docs" / "inventory" / "pticevodstvo"
PIPELINE_DIR = INVENTORY_DIR / "pipeline"
REGISTRY_PATH = INVENTORY_DIR / "registry.yaml"
ASSEMBLY_PATH = PIPELINE_DIR / "assembly-standalone.yaml"
PHASE1_PATH = PIPELINE_DIR / "phase1-tables.yaml"
DOCX_DIR = INVENTORY_DIR / "docx"
REPORTS_DIR = INVENTORY_DIR / "reports"
AUDIT_JSON_PATH = REPORTS_DIR / "docx-audit.json"
POULTRY_TEO_PATH = ROOT / "docs" / "scenarios" / "poultry-teo.yaml"
CRITICAL_DIR = ROOT / "docs" / "teo-tables" / "critical"


class RegistryValidationError(Exception):
    """registry.yaml failed schema/consistency checks."""


@dataclass
class SourceRef:
    kind: str  # file | theme | critical
    path: str
    label: str


def load_registry() -> dict[str, Any]:
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))


def load_master_assembly() -> dict[str, Any]:
    return yaml.safe_load(ASSEMBLY_PATH.read_text(encoding="utf-8"))


def resolve_path(rel: str) -> Path:
    return ROOT / rel.replace("\\", "/")


def read_text(rel: str) -> str:
    path = resolve_path(rel)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def registry_hash(registry: dict[str, Any]) -> str:
    payload = yaml.dump(registry, allow_unicode=True, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def critical_path(registry: dict[str, Any], key: str) -> str | None:
    facts = registry.get("canonical_facts", {})
    tables = facts.get("critical_tables", {})
    if key in tables:
        return str(tables[key]).replace("\\", "/")

    key = key.replace("\\", "/")
    if key.startswith("docs/"):
        return key

    candidates = [CRITICAL_DIR / key, CRITICAL_DIR / f"{key}.md"]
    for c in candidates:
        if c.exists():
            return str(c.relative_to(ROOT)).replace("\\", "/")

    for path in sorted(CRITICAL_DIR.glob("*.md")):
        if path.stem == key or path.name == key:
            return str(path.relative_to(ROOT)).replace("\\", "/")
    return None


def resolve_source(source: dict[str, Any], registry: dict[str, Any]) -> SourceRef | None:
    if "theme" in source:
        tid = source["theme"]
        theme = registry.get("themes", {}).get(tid, {})
        rel = theme.get("file", "")
        if not rel:
            return None
        return SourceRef("theme", rel, f"{tid} — {theme.get('name', tid)}")
    if "critical" in source:
        key = source["critical"]
        rel = critical_path(registry, key)
        if not rel:
            return SourceRef("critical", "", f"[НЕ НАЙДЕН: {key}]")
        return SourceRef("critical", rel, key)
    rel = source.get("file", "").replace("\\", "/")
    if not rel:
        return None
    return SourceRef("file", rel, rel)


def gather_theme_files(theme: dict[str, Any]) -> list[str]:
    files: list[str] = []
    main = theme.get("file")
    if main:
        files.append(main.replace("\\", "/"))
    for extra in theme.get("sources", []) or []:
        if isinstance(extra, str):
            files.append(extra.replace("\\", "/"))
        elif isinstance(extra, dict) and extra.get("file"):
            files.append(extra["file"].replace("\\", "/"))
    return files


def gather_section_sources(section: dict[str, Any], registry: dict[str, Any]) -> list[SourceRef]:
    out: list[SourceRef] = []
    seen: set[str] = set()
    for src in section.get("sources", []) or []:
        ref = resolve_source(src, registry)
        if not ref or not ref.path:
            if ref:
                out.append(ref)
            continue
        if ref.path in seen:
            continue
        seen.add(ref.path)
        out.append(ref)
    return out


def canonical_fact_refs(registry: dict[str, Any]) -> list[dict[str, str]]:
    facts = registry.get("canonical_facts", {})
    anchors: list[tuple[str, str, str]] = [
        ("capex_bln_rub", "12 000", "docs/teo-poultry/T01-finance.md"),
        ("revenue_mln_rub_per_year", "5 559", "docs/teo-poultry/T01-finance.md"),
        ("ebitda_mln_rub_per_year", "2 216", "docs/teo-poultry/T01-finance.md"),
        ("npv_mln_rub_at_10pct", "2 253", "docs/teo-tables/critical/T007-npv-pticevodstvo.md"),
        ("irr_pct", "12,8", "docs/teo-tables/critical/T007-npv-pticevodstvo.md"),
        ("staff_fte", "476", "docs/teo-tables/critical/T236-staff-pticevodstvo.md"),
        ("poultry_houses", "118", "docs/teo-poultry/T04-equipment.md"),
        ("slaughter_heads_per_hour", "6 000", "docs/teo-poultry/T05-slaughter-processing.md"),
    ]
    rows: list[dict[str, str]] = []
    for key, pattern, rel in anchors:
        text = read_text(rel)
        line_no = "—"
        if text and pattern:
            for i, line in enumerate(text.splitlines(), start=1):
                if pattern.replace(" ", "") in line.replace(" ", "") or pattern in line:
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


def validate_registry(registry: dict[str, Any] | None = None) -> list[str]:
    registry = registry or load_registry()
    errors: list[str] = []

    if not ASSEMBLY_PATH.exists():
        errors.append(f"missing assembly manifest: {ASSEMBLY_PATH}")
    if not POULTRY_TEO_PATH.exists():
        errors.append(f"missing poultry-teo.yaml: {POULTRY_TEO_PATH}")

    for tid, theme in registry.get("themes", {}).items():
        if not theme.get("file"):
            errors.append(f"theme {tid} missing file")
        elif not resolve_path(theme["file"]).exists():
            errors.append(f"theme {tid} file not found: {theme['file']}")
        if not theme.get("action_on_replace"):
            errors.append(f"theme {tid} missing action_on_replace")

    facts = registry.get("canonical_facts", {})
    for key, rel in (facts.get("critical_tables") or {}).items():
        if not resolve_path(rel).exists():
            errors.append(f"critical table missing: {key} -> {rel}")

    if POULTRY_TEO_PATH.exists():
        teo = yaml.safe_load(POULTRY_TEO_PATH.read_text(encoding="utf-8"))
        block = teo.get("blocks", {}).get("птицеводство", {})
        if not block:
            errors.append("poultry-teo.yaml: blocks.птицеводство missing")
        else:
            checks = [
                ("capex_bln_rub", block.get("capex_bln_rub"), facts.get("capex_bln_rub")),
                ("revenue_mln_rub_per_year", block.get("revenue_mln_rub_per_year"), facts.get("revenue_mln_rub_per_year")),
                ("staff_fte", block.get("staff_fte"), facts.get("staff_fte")),
                ("npv_mln_rub_at_10pct", round(block.get("npv_thousand_rub", 0) / 1000), facts.get("npv_mln_rub_at_10pct")),
            ]
            for key, teo_val, reg_val in checks:
                if teo_val != reg_val and not (key == "npv_mln_rub_at_10pct" and abs(float(teo_val or 0) - float(reg_val or 0)) < 1):
                    errors.append(f"canonical_facts.{key} ({reg_val}) != poultry-teo ({teo_val})")

    if ASSEMBLY_PATH.exists():
        assembly = load_master_assembly()
        for sec in assembly.get("sections", []):
            for src in sec.get("sources", []) or []:
                ref = resolve_source(src, registry)
                if ref and ref.path and not resolve_path(ref.path).exists():
                    errors.append(f"assembly [{sec.get('id')}] missing source: {ref.path}")

    return errors


def assert_registry_valid(registry: dict[str, Any] | None = None) -> None:
    errors = validate_registry(registry)
    if errors:
        raise RegistryValidationError("\n".join(errors))


def build_docx_audit(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or load_registry()
    assembly = load_master_assembly()
    theme_files: dict[str, list[str]] = {}
    for tid, theme in registry.get("themes", {}).items():
        theme_files[tid] = gather_theme_files(theme)

    section_coverage: list[dict[str, Any]] = []
    for sec in assembly.get("sections", []):
        refs = gather_section_sources(sec, registry)
        section_coverage.append(
            {
                "id": sec.get("id"),
                "title": sec.get("title"),
                "action": sec.get("action"),
                "sources": [{"kind": r.kind, "path": r.path, "label": r.label} for r in refs],
                "source_count": len(refs),
            }
        )

    missing_theme_docx = [
        tid
        for tid, theme in registry.get("themes", {}).items()
        if not (DOCX_DIR / f"{tid.lower()}-{theme.get('name', tid).split()[0].lower()}.docx").exists()
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry_hash": registry_hash(registry),
        "summary": {
            "themes": len(registry.get("themes", {})),
            "critical_tables": len((registry.get("canonical_facts", {}) or {}).get("critical_tables", {})),
            "assembly_sections": len(assembly.get("sections", [])),
        },
        "themes": {tid: files for tid, files in theme_files.items()},
        "assembly_sections": section_coverage,
        "note": "Run generate-pticevodstvo-docx.py to materialize DOCX",
    }


def write_docx_audit(registry: dict[str, Any] | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    audit = build_docx_audit(registry)
    AUDIT_JSON_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return AUDIT_JSON_PATH

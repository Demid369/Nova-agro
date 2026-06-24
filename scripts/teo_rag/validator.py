"""Validate answers against retrieved evidence (anti-hallucination for numbers)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Numbers with optional grouping, decimals, units
NUM_TOKEN_RE = re.compile(
    r"(?<!\w)"
    r"(\d[\d\s]{0,15}(?:[,.]\d+)?)"
    r"(?:\s*(%|млрд|млн|тыс\.?|руб\.?|мес\.?|га|мвт|т/год|долл\.?))?"
    r"(?!\w)",
    re.I,
)

SKIP_PLAIN = re.compile(r"^\d{1,2}$")  # 1, 2, 10 — section-like


@dataclass
class NumberCheck:
    raw: str
    normalized: str
    supported: bool
    matched_in: str | None = None


@dataclass
class ValidationResult:
    valid: bool
    numbers: list[NumberCheck] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "unsupported_numbers": self.unsupported,
            "numbers_checked": len(self.numbers),
            "warnings": self.warnings,
        }


def normalize_number(raw: str) -> str:
    s = raw.strip().lower()
    s = s.replace("\u00a0", " ").replace(" ", "")
    s = s.replace(",", ".")
    # collapse multiple dots (thousands vs decimal): keep last dot as decimal
    if s.count(".") > 1:
        head, tail = s.rsplit(".", 1)
        head = head.replace(".", "")
        s = f"{head}.{tail}"
    return s


def extract_significant_numbers(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in NUM_TOKEN_RE.finditer(text):
        num_part = m.group(1).strip()
        unit = (m.group(2) or "").strip()
        raw = f"{num_part} {unit}".strip() if unit else num_part
        norm = normalize_number(num_part)
        if SKIP_PLAIN.match(norm.replace(".", "")):
            continue
        # ignore bare years unless part of larger figure
        if re.fullmatch(r"20\d{2}", norm) and not unit:
            continue
        digits_only = re.sub(r"\D", "", norm)
        if len(digits_only) < 3 and not unit:
            continue
        key = norm + "|" + unit.lower()
        if key not in seen:
            seen.add(key)
            found.append(raw)
    return found


def corpus_number_set(corpus: str) -> set[str]:
    norms: set[str] = set()
    for raw in extract_significant_numbers(corpus):
        norms.add(normalize_number(raw.split()[0]))
    for m in re.finditer(r"\d[\d\s,.]{1,20}\d", corpus):
        norms.add(normalize_number(m.group(0)))
    return norms


def number_in_corpus(number_raw: str, corpus: str) -> bool:
    norm = normalize_number(number_raw.split()[0])
    digits = re.sub(r"\D", "", norm)
    if not digits:
        return False
    for cn in corpus_number_set(corpus):
        if norm == cn:
            return True
        cd = re.sub(r"\D", "", cn)
        if digits == cd:
            return True
    return False


def validate_answer(answer: str, corpus: str, *, strict: bool = True) -> ValidationResult:
    checks: list[NumberCheck] = []
    unsupported: list[str] = []
    warnings: list[str] = []

    if not corpus.strip():
        warnings.append("empty evidence corpus")
        return ValidationResult(valid=not strict, numbers=[], unsupported=[], warnings=warnings)

    for raw in extract_significant_numbers(answer):
        ok = number_in_corpus(raw, corpus)
        checks.append(
            NumberCheck(raw=raw, normalized=normalize_number(raw.split()[0]), supported=ok)
        )
        if not ok:
            unsupported.append(raw)

    valid = len(unsupported) == 0
    if not checks and strict:
        warnings.append("no significant numbers to verify")

    return ValidationResult(
        valid=valid,
        numbers=checks,
        unsupported=unsupported,
        warnings=warnings,
    )

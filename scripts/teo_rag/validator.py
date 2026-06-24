"""Validate answers against retrieved evidence (anti-hallucination)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

NUM_TOKEN_RE = re.compile(
    r"(?<!\w)"
    r"(\d[\d\s]{0,15}(?:[,.]\d+)?)"
    r"(?:\s*(%|млрд|млн|тыс\.?|руб\.?|мес\.?|га|мвт|т/год|долл\.?))?"
    r"(?!\w)",
    re.I,
)

SKIP_PLAIN = re.compile(r"^\d{1,2}$")
CITATION_TAG_RE = re.compile(r"\[[^\]]+\]")
QUOTE_RE = re.compile(r"«([^»]{4,120})»")
WORD_RE = re.compile(r"[a-zа-яё0-9]+", re.I)

CLAIM_STOP = {
    "этот", "этого", "который", "которые", "также", "более", "менее", "может",
    "будет", "были", "была", "быть", "только", "после", "перед", "через",
}


@dataclass
class NumberCheck:
    raw: str
    normalized: str
    supported: bool
    matched_in: str | None = None


@dataclass
class ClaimCheck:
    text: str
    supported: bool
    overlap: float


@dataclass
class ValidationResult:
    valid: bool
    numbers: list[NumberCheck] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    claims: list[ClaimCheck] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "unsupported_numbers": self.unsupported,
            "unsupported_claims": self.unsupported_claims,
            "numbers_checked": len(self.numbers),
            "claims_checked": len(self.claims),
            "warnings": self.warnings,
        }


def normalize_number(raw: str) -> str:
    s = raw.strip().lower()
    s = s.replace("\u00a0", " ").replace(" ", "")
    s = s.replace(",", ".")
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


def _content_words(text: str) -> list[str]:
    return [
        w.lower()
        for w in WORD_RE.findall(text)
        if len(w) > 3 and w.lower() not in CLAIM_STOP
    ]


def _word_match(word: str, corpus_words: set[str]) -> bool:
    if word in corpus_words:
        return True
    if len(word) >= 5:
        prefix = word[:5]
        return any(cw.startswith(prefix) or prefix.startswith(cw[:5]) for cw in corpus_words)
    return False


def sentence_overlap(sentence: str, corpus: str) -> float:
    sent_clean = CITATION_TAG_RE.sub("", sentence).strip()
    words = _content_words(sent_clean)
    if len(words) < 5:
        return 1.0
    corpus_words = set(_content_words(corpus))
    if not corpus_words:
        return 0.0
    hits = sum(1 for w in words if _word_match(w, corpus_words))
    return hits / len(words)


def quote_in_corpus(quote: str, corpus: str) -> bool:
    q = quote.strip().lower()
    if len(q) < 4:
        return True
    return q in corpus.lower()


def extract_claim_sentences(answer: str) -> list[str]:
    """Sentences worth fact-checking (skip headers/meta)."""
    claims: list[str] = []
    for block in re.split(r"\n+", answer):
        block = block.strip()
        if not block or block.startswith("Ответ по ТЭО") or block.startswith("Запрос"):
            continue
        if block.startswith("Связи (граф):"):
            continue
        line = re.sub(r"^[•\-]\s*", "", block)
        line = CITATION_TAG_RE.sub("", line).strip()
        if len(line) < 50:
            continue
        if "|" in line and "NODE" not in line:
            claims.append(line)
        elif re.search(r"\d", line) or "«" in line or len(_content_words(line)) >= 8:
            claims.append(line)
    return claims


def validate_claims(answer: str, corpus: str, *, min_overlap: float = 0.42) -> tuple[list[ClaimCheck], list[str]]:
    checks: list[ClaimCheck] = []
    unsupported: list[str] = []

    for quote in QUOTE_RE.findall(answer):
        ok = quote_in_corpus(quote, corpus)
        checks.append(ClaimCheck(text=f"«{quote}»", supported=ok, overlap=1.0 if ok else 0.0))
        if not ok:
            unsupported.append(f"«{quote}»")

    for sent in extract_claim_sentences(answer):
        overlap = sentence_overlap(sent, corpus)
        ok = overlap >= min_overlap
        checks.append(ClaimCheck(text=sent[:120], supported=ok, overlap=round(overlap, 3)))
        if not ok:
            unsupported.append(sent[:120])

    return checks, unsupported


def validate_answer(
    answer: str,
    corpus: str,
    *,
    strict: bool = True,
    check_claims: bool = True,
) -> ValidationResult:
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

    claim_checks: list[ClaimCheck] = []
    unsupported_claims: list[str] = []
    if check_claims:
        claim_checks, unsupported_claims = validate_claims(answer, corpus)

    valid = len(unsupported) == 0 and len(unsupported_claims) == 0
    if not checks and strict and not claim_checks:
        warnings.append("no significant facts to verify")

    return ValidationResult(
        valid=valid,
        numbers=checks,
        unsupported=unsupported,
        claims=claim_checks,
        unsupported_claims=unsupported_claims,
        warnings=warnings,
    )

"""Query routing: graph / vector / hybrid / summary / memory."""

from __future__ import annotations

import re
from dataclasses import dataclass

GRAPH_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\bpath\b",
        r"связ",
        r"цепочк",
        r"как связан",
        r"от .+ к ",
        r"между .+ и ",
        r"explain",
        r"граф",
        r"сообществ",
        r"узл",
    )
]

VECTOR_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\bnpv\b",
        r"\birr\b",
        r"цитат",
        r"сколько",
        r"таблиц",
        r"цифр",
        r"млрд",
        r"млн",
        r"руб",
        r"окупаем",
        r"что пишет",
        r"прибыл",
        r"выручк",
        r"инвестиц",
        r"риск\w* .+ мер",
    )
]

HYBRID_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"риск\w*",
        r"экспорт",
        r"меры снижен",
        r"бизнес.?модел",
        r"вертикал",
        r"комбикорм",
    )
]

SUMMARY_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"обзор",
        r"структур",
        r"блоки проекта",
        r"сводк",
        r"что за проект",
    )
]


@dataclass
class RouteDecision:
    mode: str
    reason: str
    scores: dict[str, int]


def score_patterns(query: str, patterns: list[re.Pattern[str]]) -> int:
    return sum(1 for p in patterns if p.search(query))


def classify_query(query: str, force_mode: str | None = None) -> RouteDecision:
    if force_mode and force_mode != "auto":
        return RouteDecision(mode=force_mode, reason=f"forced:{force_mode}", scores={})

    q = query.strip()
    scores = {
        "graph": score_patterns(q, GRAPH_PATTERNS),
        "vector": score_patterns(q, VECTOR_PATTERNS),
        "hybrid": score_patterns(q, HYBRID_PATTERNS),
        "summary": score_patterns(q, SUMMARY_PATTERNS),
    }

    if scores["summary"] >= 2 or (scores["summary"] >= 1 and max(scores.values()) == scores["summary"]):
        return RouteDecision(mode="summary", reason="summary keywords", scores=scores)

    if scores["graph"] >= 2 and scores["vector"] == 0:
        return RouteDecision(mode="graph", reason="relation/path keywords", scores=scores)

    if scores["vector"] >= 2 and scores["graph"] == 0:
        return RouteDecision(mode="vector", reason="fact/quote keywords", scores=scores)

    if scores["hybrid"] >= 1 or (scores["graph"] >= 1 and scores["vector"] >= 1):
        return RouteDecision(mode="hybrid", reason="mixed intent", scores=scores)

    if scores["graph"] > scores["vector"]:
        return RouteDecision(mode="graph", reason="graph tie-break", scores=scores)
    if scores["vector"] > 0:
        return RouteDecision(mode="vector", reason="vector tie-break", scores=scores)
    return RouteDecision(mode="hybrid", reason="default hybrid", scores=scores)

"""Answer synthesis strictly from retrieved evidence."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from .context import EvidenceBundle
from .graph_client import GraphResult
from .retrieval import RetrievedChunk

SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")


@dataclass
class SynthesisResult:
    answer: str
    method: str  # extractive | llm | passthrough
    model: str | None = None


def _query_tokens(query: str) -> set[str]:
    stop = {"как", "что", "где", "когда", "для", "при", "или", "и", "в", "на", "по", "от", "до", "с", "у", "о", "the", "a"}
    return {t for t in re.findall(r"[a-zа-яё0-9]+", query.lower()) if t not in stop and len(t) > 2}


def score_sentence(sentence: str, tokens: set[str]) -> float:
    words = set(re.findall(r"[a-zа-яё0-9]+", sentence.lower()))
    if not words:
        return 0.0
    overlap = len(words & tokens)
    return overlap / max(len(tokens), 1) + min(len(sentence), 400) / 4000


def extractive_synthesize(
    bundle: EvidenceBundle,
    max_sentences: int = 6,
) -> SynthesisResult:
    tokens = _query_tokens(bundle.query)
    wants_numbers = bool(
        re.search(r"npv|irr|сколько|млрд|млн|цифр|таблиц|payback|окупаем", bundle.query, re.I)
    )
    scored: list[tuple[float, str, str]] = []

    for rank, hit in enumerate(bundle.chunks):
        rank_bonus = max(0, (5 - rank) * 0.08)
        # таблицы KPI — целиком из top-чанков
        if rank < 2 and "|" in hit.text and wants_numbers:
            for block in re.split(r"\n{2,}", hit.text):
                if "|" in block and re.search(r"\d", block):
                    tag = f"[{hit.source} :: {hit.section}]"
                    scored.append((2.0 + hit.score, block.strip(), tag))

        for sent in SENTENCE_SPLIT.split(hit.text):
            sent = sent.strip()
            if len(sent) < 30:
                continue
            sc = score_sentence(sent, tokens) + hit.score * 0.25 + rank_bonus
            if wants_numbers and re.search(r"\d{2,}", sent):
                sc += 0.6
            if sc <= 0.05:
                continue
            tag = f"[{hit.source} :: {hit.section}]"
            scored.append((sc, sent, tag))

    scored.sort(key=lambda x: x[0], reverse=True)
    lines: list[str] = []
    used: set[str] = set()
    for _, sent, tag in scored:
        key = sent[:80]
        if key in used:
            continue
        used.add(key)
        lines.append(f"• {sent} {tag}")
        if len(lines) >= max_sentences:
            break

    if bundle.graph and bundle.graph.edges:
        lines.append("")
        lines.append("Связи (граф):")
        for edge in bundle.graph.edges[:5]:
            lines.append(f"• {edge.source} --{edge.relation}--> {edge.target}")

    if not lines:
        return SynthesisResult(
            answer="Недостаточно evidence для синтеза. См. citations.",
            method="extractive",
        )

    header = f"Ответ по ТЭО (только из retrieved, {len(lines)} фрагментов):\n"
    return SynthesisResult(answer=header + "\n".join(lines), method="extractive")


def _gemini_api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def llm_synthesize(bundle: EvidenceBundle, model: str | None = None) -> SynthesisResult:
    api_key = _gemini_api_key()
    if not api_key:
        fallback = extractive_synthesize(bundle)
        fallback.method = "extractive"
        return SynthesisResult(
            answer=fallback.answer + "\n\n[llm недоступен: нет GEMINI_API_KEY]",
            method="extractive",
        )

    model = model or os.environ.get("GRAPHIFY_GEMINI_MODEL", "gemini-2.0-flash")
    context = bundle.corpus_text()[:24000]
    prompt = f"""Ты отвечаешь на вопрос по ТЭО «МОЯ МЕЧТА».

СТРОГИЕ ПРАВИЛА:
1. Используй ТОЛЬКО факты из блока КОНТЕКСТ ниже.
2. Не выдумывай цифры — если числа нет в контексте, не указывай его.
3. После каждого факта укажи источник в скобках: (source :: section).
4. Если контекста недостаточно — скажи об этом прямо.
5. Отвечай на русском, кратко (5–8 предложений).

ВОПРОС: {bundle.query}

КОНТЕКСТ:
{context}
"""

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024},
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return SynthesisResult(answer=text, method="llm", model=model)
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        fallback = extractive_synthesize(bundle)
        return SynthesisResult(
            answer=fallback.answer + f"\n\n[llm ошибка: {exc}]",
            method="extractive",
        )


def synthesize(
    bundle: EvidenceBundle,
    method: str = "extractive",
) -> SynthesisResult:
    if method == "llm":
        return llm_synthesize(bundle)
    if method == "extractive":
        return extractive_synthesize(bundle)
    raise ValueError(f"unknown synthesis method: {method}")

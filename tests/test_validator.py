"""Tests for answer validation against evidence corpus."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from teo_rag.validator import (  # noqa: E402
    extract_significant_numbers,
    normalize_number,
    validate_answer,
)


CORPUS = """
| Блок | NPV | IRR |
| Теплицы | 33 861 691 | 28,99% |
| Кролиководство | 2 779 519 | 15,19% |
инвестиции 100 млрд руб.
экспорт 10,2 млрд
"""


def test_normalize_grouped_number():
    assert normalize_number("33 861 691") == "33861691"
    assert normalize_number("28,99") == "28.99"


def test_extract_significant_numbers():
    nums = extract_significant_numbers("NPV теплиц 33 861 691 при IRR 28,99%")
    assert any("33" in n for n in nums)
    assert any("28" in n for n in nums)


def test_validate_supported_numbers():
    answer = "NPV теплиц составляет 33 861 691 при IRR 28,99%"
    result = validate_answer(answer, CORPUS)
    assert result.valid is True
    assert result.unsupported == []


def test_validate_rejects_hallucinated():
    answer = "NPV теплиц 99 999 999 млрд"
    result = validate_answer(answer, CORPUS)
    assert result.valid is False
    assert len(result.unsupported) >= 1


def test_validate_claims_supported():
    answer = "Проект в Херсонской области, инвестиции 100 млрд"
    corpus = "Херсонская область инвестиции 100 млрд руб."
    result = validate_answer(answer, corpus, check_claims=True)
    assert result.valid is True


def test_validate_empty_corpus_non_strict():
    result = validate_answer("100 млрд", "", strict=False)
    assert result.valid is True


def test_validate_claims_reject():
    answer = "Проект расположен на Марсе и финансируется из параллельной вселенной"
    corpus = "Херсонская область инвестиции 100 млрд"
    result = validate_answer(answer, corpus, check_claims=True)
    assert result.valid is False
    assert result.unsupported_claims

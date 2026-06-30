# Phase 3 — §4 market + genetics + yield tables (jun 2026)

> **Команда:** `python3 scripts/build-teo-poultry-from-baseline.py` (phase3 включён)  
> **Или:** `python3 scripts/apply-teo-poultry-phase3.py`

## Результат

| Проверка | Статус |
|----------|--------|
| Drawings preserved | **394 / 394** ✓ |
| Block 1 marketing (485–530) | **35 chunks → 34 slots** |
| Genetics T03 (955–1030) | **17 → 50** |
| §4.1.1.1 product (2139–2146) | **7 → 5** |
| §4.1.1.2 world T12 (3567–3604) | **14 → 17** |
| §7 reapply (fix hyperlinks) | **32 → 32** |
| Tab. 23-P / 39-P / 140-P | **OK** |
| «Кролик» в XML | **~199** (было ~315 после phase2) |

## Исправления инфраструктуры

1. **`set_paragraph_text`** — удаляет все дочерние элементы кроме `pPr` (fix hyperlink runs → склейка caption+narrative)
2. **`body[i] = tbl`** — замена таблиц в XML tree (не Python list copy)

## Tab. 140-P (yield)

| Показатель | ROSS 308 | BUT Big 6 | … |
|------------|----------|-----------|---|
| Убойный выход | 75% | 78% | finmodel |

Источник: `docs/teo-tables/critical/T005-poultry-yield-matrix.md`

## Следующее

- Binary swap image7–9, 311–313 (`replace-docx-media.py`)
- Rabbit blocks §4 export appendix (3623+) — отдельный pass или AS-IS
- Trade HS appendix «А» — AS-IS

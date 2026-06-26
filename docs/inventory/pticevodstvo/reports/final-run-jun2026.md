# Final run — master draft птицеводство (jun 2026)

> **Дата:** 2026-06-26  
> **Команда:** `python3 scripts/generate-pticevodstvo-docx.py`  
> **Выход:** `docs/inventory/pticevodstvo/docx/00-master-teo-pticevodstvo-draft.docx`

## Результат

| Проверка | Статус |
|----------|--------|
| `validate_registry()` | **0 errors** |
| Секций assembly | **18** |
| Theme DOCX | **12 + index + master = 14** |
| Critical tables в registry | **11** |
| Master объём | **~7 900 слов**, **892** para, **149** tables |

## KPI в master (paragraphs + table cells)

| KPI | Канon | В master |
|-----|-------|----------|
| CAPEX | 12 000 | ✓ |
| Выручка блока | 5 559 | ✓ |
| EBITDA | 2 216 | ✓ |
| NPV @10%, 16y | +2 253 | ✓ |
| IRR | 12,8% | ✓ |
| FTE | 476 | ✓ |
| Птичники | 118 | ✓ |
| T004-merged ВСЕГО | 72 158 537 | ✓ |
| T241-P «Птицеводство» | rename | ✓ (в таблице §8–9) |
| Export 10 208 vs finmodel 5 559 | R-02 | ✓ |
| DCF 16 лет | R-03 | ✓ |

## Секции master (18)

| ID | § | Источников |
|----|---|------------|
| front | — | 1 |
| s01 | §1 | 1 |
| s02_customer | §2 | 1 |
| s03_strategy | §3 | 1 |
| s02_potential | §2.3 | 2 |
| s04_market | §4 | 3 |
| s04_export | §4/§10 | 3 |
| s05_materials | §5 | 3 |
| s05_energy | §5.3 | 2 |
| s06_location | §6 | 2 |
| s07_capacity | §7.1 | 2 |
| s07_technology | §7.2 | 5 |
| s08_org | §8–9 | 3 |
| s10_schedule | §10 | 3 |
| s11_poultry | §11 | 5 |
| s11_apk_other | §11 APK | 5 |
| s12 | §12 | 1 |
| s07_byproducts | §7 | 1 |

## Ожидаемые упоминания «кролик» (~80)

**Норма** — не баг:

- **T004-merged / T001-merged** — patch-notes и строки baseline APK (блоки 2–5)
- **T005 export** — Tab#5 as-is (исторические строки кролика в consolidated)
- **T241-P footnote** — «Baseline: Кролиководство» (1 строка)
- **Сравнительные таблицы** — strategiya, T236-P, risks

**Не должно быть в narrative блока 1:** Meneghin, ANCI, крольчатина как продукт блока — **отсутствуют** ✓

## Known gaps (не блокируют standalone)

| # | Gap | Комментарий |
|---|-----|-------------|
| 1 | `production_site: null` | R-04 TBD |
| 2 | Corpus §4 APK-wide (~400 стр.) | не в draft |
| 3 | Приложение «А» 103 HS-tab | не в draft |
| 4 | 346 media baseline | не в draft |
| 5 | Два контура земли | footnote R-01 |

## Вердикт

**Master draft блока птицы (12 млрд) — PASS** для standalone review.

Следующий этап (опционально): corpus merge → полный APK master 100 млрд.

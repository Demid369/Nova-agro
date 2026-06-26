# Phase 10 — final QA (jun 2026)

> **Команда:** `python3 scripts/build-teo-poultry-from-baseline.py`  
> **Verify:** `python3 scripts/verify-baseline-poultry-docx.py`

## Результат

| Проверка | Статус |
|----------|--------|
| Drawings | **394 / 394** |
| Residual «кролик/кроль/кролич» | **68** (target ≤80, приложение «А» AS-IS) |
| CAPEX 12 000 | OK |
| Revenue 5 559 | OK |
| NPV +2 253 @10% | OK |
| IRR 12,8% | OK |
| 476 FTE / 118 птичников | OK |
| SINT 6 000 | OK |

## Phases 5–10 (этот PR)

| Phase | Зона | Файл |
|-------|------|------|
| 5 | §1–§3 front + APK concept | `phase5-front.yaml` |
| 6 | §4 SWOT, RF market, pricing | `phase6-rf-market.yaml` |
| 7 | §8–§12 + §7.2.2 env | `phase7-conclusions.yaml` |
| 8 | Global regex cleanup | `phase8-cleanup.yaml` |
| 9 | Media captions (binaries AS-IS) | `phase9-media.yaml` |
| 10 | QA + report | этот файл |

## Phase 9 — media

PNG assets для `image7–9`, `311–313` **не в `_incoming/`** — бинарники baseline сохранены.  
После появления assets:

```bash
python3 scripts/replace-docx-media.py --docx docs/inventory/pticevodstvo/docx/1.ТЭO_МOЯ_МEЧTA_ПTIЦA.docx --dir docs/teo-poultry/_incoming/
```

## Остаточный «кролик» (68)

Footnote phase1, review-pass, приложение «А» (HS/trade), legacy image captions — **by design**.

## Output

`docs/inventory/pticevodstvo/docx/1.ТЭO_МOЯ_МEЧTA_ПTIЦA.docx` (~64 MB, gitignore)

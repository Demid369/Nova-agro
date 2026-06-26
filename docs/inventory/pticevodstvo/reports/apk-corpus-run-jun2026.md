# APK corpus merge — first run (jun 2026)

> **Команда:** `python3 scripts/generate-apk-master-docx.py`  
> **Выход:** `docs/inventory/pticevodstvo/docx/00-apk-master-teo-full-draft.docx`

## Результат

| Проверка | Статус |
|----------|--------|
| Registry validation | **0 errors** |
| Standalone секций (часть I) | **18** |
| Corpus секций (часть II) | **5** |
| Patch rules (кролик skip) | **applied** |
| Appendix A reference_trade | **103** tables |
| APK master объём | **~63 500 слов**, **241 KB** |

## Сравнение

| DOCX | Слова | Назначение |
|------|-------|------------|
| `00-master-teo-pticevodstvo-draft.docx` | ~17 500 | Investor / блок 1 |
| `00-apk-master-teo-full-draft.docx` | ~63 500 | APK 100 млрд text+tables |

## Known gaps

| # | Gap | Комментарий |
|---|-----|-------------|
| 1 | 346 embedded images | baseline DOCX не в git — см. `media-extraction-plan.md` |
| 2 | Corpus §4 truncated at 500k chars | при необходимости — split по `#` headings |
| 3 | Pixel-perfect clone baseline | нужен merge с оригинальным DOCX + media |

## Вердict

**APK master pipeline v1 — PASS** (text + md-tables). Media re-embed — phase 2.

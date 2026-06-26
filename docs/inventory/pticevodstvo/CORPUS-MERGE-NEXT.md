# Corpus merge — следующая фаза

> **Статус jun 2026:** **STARTED** — pipeline scaffold готов  
> Standalone блок 1 (**12 млрд**) — **PASS** + merged PR #13  
> Investor-ready — one-pager, exec summary, stress-pack

## Что сделано

| Компонент | Файл | Статус |
|-----------|------|--------|
| APK assembly manifest | `pipeline/assembly-apk-full.yaml` | ✅ |
| Patch rules (кролик → skip) | `pipeline/corpus-patch-rules.yaml` | ✅ |
| Generator | `scripts/generate-apk-master-docx.py` | ✅ |
| Media plan | `reports/media-extraction-plan.md` | ✅ |
| Media extract script | `scripts/extract-docx-media.py` | ✅ scaffold |

## Команды

```bash
# Standalone (investor review блока 1)
python3 scripts/final-run-pticevodstvo.py

# Full APK master (text + tables; без embedded images)
python3 scripts/generate-apk-master-docx.py

# Быстрый прогон (10 trade tables)
python3 scripts/generate-apk-master-docx.py --appendix-limit 10

# Media (когда baseline docx локально)
python3 scripts/extract-docx-media.py \
  --input "docs/1.ТЭО_МОЯ МЕЧТА.docx" \
  --output docs/inventory/pticevodstvo/media/
```

## Выход

| DOCX | Содержание | ~объём |
|------|------------|--------|
| `00-master-teo-pticevodstvo-draft.docx` | Standalone 18 секций | ~60–80 стр. |
| `00-apk-master-teo-full-draft.docx` | Standalone + corpus + appendix A | ~300–500+ стр. |

## Остаётся

1. **Re-embed 346 images** — нужен baseline DOCX локально
2. **Poultry images** — Facco/SINT схемы вместо кролика
3. **Единый land footnote** R-01 на уровне финального DOCX (авто-insert в pipeline v2)
4. **RAG index** — по approval

## Зачем отдельно от standalone

| | Standalone (готово) | Full APK master |
|--|---------------------|-----------------|
| Объём | ~60–80 стр. | ~500–700+ стр. с media |
| Scope | Блок 1 замена | + corpus §4, блоки 2–5, приложение «А» |
| ROI | **investor review блока** | банк / грант / единый APK |

## Источники

- [`reports/final-run-jun2026.md`](reports/final-run-jun2026.md)
- [`../../teo-poultry/appendix/master-docx-assembly.md`](../../teo-poultry/appendix/master-docx-assembly.md)
- PR #13 (merged)

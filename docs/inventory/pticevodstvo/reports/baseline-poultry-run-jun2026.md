# Baseline TEO → птица — first run (jun 2026)

> **Команда:** `python3 scripts/build-teo-poultry-from-baseline.py`  
> **Выход:** `docs/inventory/pticevodstvo/docx/1.ТЭО_МОЯ_МЕЧТА_ПТИЦА.docx`  
> **Карта картинок:** `docs/inventory/pticevodstvo/media/image-map.json`

## Результат

| Проверка | Baseline | Птица | Статус |
|----------|----------|-------|--------|
| **Страниц (оценка)** | **~693** | **~694** | ✓ parity |
| Слова | 191 878 | 192 113 | ✓ |
| Таблицы | 243 | 243 | ✓ |
| Media files | 346 | 346 | ✓ |
| Drawings (inline) | 394 | 394 | **OK** |
| Размер | 65 MB | 64 MB | ✓ |

## Что сделано

1. **Копия baseline** — все 346 изображений на исходных местах (186 inline-параграфов)
2. **Critical tables заменены:** T001, T003, T004, T007, T014 (patch), T021 (skip image cells), T022, T236, T241
3. **Текст block 1** — regex-замены в параграфах/ячейках **без** drawing (картинки + подписи — as-is для последующей замены)
4. **Review footnote** в начале документа

## KPI в документе

CAPEX 12 000 | 5 559 | NPV +2 253 | IRR 12,8% | 476 FTE | 118 | Птицеводство | Нова-Агро — **все ✓**

## «Кролик» остался (~358 упоминаний) — норма

| Источник | Действие позже |
|----------|----------------|
| 186 параграфов с **images** (подписи «кролик», фото пород) | **Заменить картинки** по `image-map.json` |
| Trade tables приложение «А» (HS крольчатина) | AS-IS или отдельный pass |
| Blocks 2–5 narrative | AS-IS baseline APK |

## Regenerate media extract

```bash
python3 scripts/build-teo-poultry-from-baseline.py --extract-media
# → docs/inventory/pticevodstvo/media/* (346 files, gitignored)
```

## Следующие шаги

1. Точечная замена image-параграфов block 1 (Facco/SINT схемы)
2. Narrative §7 кролик → `appendix/01-tehnologicheskiy-cikl.md` (без потери layout)
3. T141-P вставка в §5 (Tab.141 slot)

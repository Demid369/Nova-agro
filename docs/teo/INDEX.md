# ТЭО «МОЯ МЕЧТА» — карта документов

> Два контура: **baseline (кролики, APK 100 млрд)** и **птица (блок I, 12 млрд, сценарий C)**.  
> KPI птицы: `docs/scenarios/poultry-teo.yaml`

## Быстрый выбор пути

| Задача | Что делать | Результат |
|--------|------------|-----------|
| **Полное ТЭO ~694 стр. с картинками** | `python3 scripts/build-teo-poultry-from-baseline.py` | `docx/1.ТЭО_МОЯ_МЕЧТА_ПТИЦА.docx` |
| **Investor pack (текст, ~60–80 стр.)** | `python3 scripts/generate-pticevodstvo-docx.py` | `docx/00-master-teo-pticevodstvo-draft.docx` |
| **APK corpus без images (~220–250 стр.)** | `python3 scripts/generate-apk-master-docx.py` | `docx/00-apk-master-teo-full-draft.docx` |
| **Graph / RAG (baseline)** | `docs/graphify-corpus/` + `graphify query …` | `graphify-out/` |
| **Править KPI / сценарий** | `docs/scenarios/poultry-teo.yaml` | — |

---

## Дерево каталогов

```
docs/
├── 1.ТЭО_МОЯ МЕЧТА.docx          ← ИСХОДНИК (66 MB, не в git)
├── 1.2-слайд Фин модель.xlsx     ← finmodel APK 100 млрд
│
├── teo/                          ← нарезка baseline docx (140 md, RAG full-text)
├── graphify-corpus/              ← сводный корпус для Graphify (7 файлов)
├── teo-tables/                   ← 241 таблица из Word + critical/
│   ├── all/T001…T241.md
│   └── critical/                 ← таблицы для замены (baseline + poultry)
│
├── teo-poultry/                  ← КОНТЕНТ птицы (канон текста)
│   ├── T01…T12-*.md              ← темы
│   ├── appendix/                 ← §7 цикл, риски, front matter, …
│   ├── land-budget.yaml
│   └── _incoming/                ← сырые docx/xlsx (не в git)
│
├── inventory/
│   ├── krolikovodstvo/           ← baseline inventory (T01–T13, RAG audit)
│   └── pticevodstvo/             ← ПАЙПЛАЙН птица → DOCX
│       ├── pipeline/             ← yaml фазы 1–4, assembly, patch-rules
│       ├── sources/narrative/    ← тексты для вставки в baseline DOCX
│       ├── media/                ← image-map, slots замены
│       ├── docx/                 ← СГЕНЕРИРОВАННЫЕ Word (gitignore)
│       └── reports/              ← отчёты прогонов
│
└── scenarios/
    ├── baseline.yaml             ← APK кролики (active graph)
    └── poultry-teo.yaml        ← KPI птицы (draft, канон блока I)
```

---

## Baseline vs птица

| | Baseline | Птица (блок I) |
|--|----------|----------------|
| Блок 1 | Кролики 12 млрд, 7k т | **12 млрд, 18 170 т, 476 FTE** |
| Земля APK | 100k га, Херсон | **250k га, Запорожье, слот 400 га** |
| Блоки 2–5 | AS-IS в baseline DOCX | **AS-IS** (не трогаем) |
| RAG/Graph | ✅ indexed | ❌ draft, не в индексе |
| Master DOCX | `1.ТЭО_МОЯ МЕЧТА.docx` | **`1.ТЭО_МOЯ_МEЧTA_ПTIЦA.docx`** (clone+replace) |

---

## Pipeline baseline → птица

См. [`inventory/pticevodstvo/pipeline/README.md`](../inventory/pticevodstvo/pipeline/README.md)

| Фаза | YAML | Что меняет |
|------|------|------------|
| 1 | `phase1-tables.yaml` | Critical tables + regex block 1 |
| 2 | `phase2-section7.yaml` | §7 технологический цикл + Tab P-141 |
| 3 | `phase3-market.yaml` | §4 market, genetics, Tab 140/23/39-P |
| 4 | `phase4-export.yaml` | §4 export tail → T10 |
| 5 | `phase5-front.yaml` | §1–§3 front + APK concept |
| 6 | `phase6-rf-market.yaml` | §4 SWOT, RF market, pricing |
| 7 | `phase7-conclusions.yaml` | §8–§12 + §7.2.2 env |
| 8 | `phase8-cleanup.yaml` | Global regex cleanup |
| 9 | `phase9-media.yaml` | Media captions (PNG TBD) |
| 10 | `verify-baseline-poultry-docx.py` | QA: 394 drawings, KPI, krolik ≤80 |

Отчёт: [`reports/baseline-poultry-final-jun2026.md`](../inventory/pticevodstvo/reports/baseline-poultry-final-jun2026.md)

---

## Куда класть новые данные

| Тип | Путь |
|-----|------|
| Сырой docx/xlsx | `teo-poultry/_incoming/` |
| Тема T01–T12 | `teo-poultry/T*.md` |
| Большой appendix | `teo-poultry/appendix/` |
| Critical table | `teo-tables/critical/T*-poultry*.md` |
| Narrative для DOCX-фазы | `inventory/pticevodstvo/sources/narrative/` |
| KPI | `scenarios/poultry-teo.yaml` + `registry.yaml` |

---

## Связанные README

- [`inventory/pticevodstvo/README.md`](../inventory/pticevodstvo/README.md) — команды сборки
- [`teo-poultry/README.md`](../teo-poultry/README.md) — статус контента
- [`teo-tables/README.md`](../teo-tables/README.md) — таблицы
- [`scenarios/README.md`](../scenarios/README.md) — сценарии

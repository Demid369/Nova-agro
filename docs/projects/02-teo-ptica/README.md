# Проект 2 — птица «Нова-Агро» (блок I, 12 млрд)

Замена кроликов в слоте I-фазы APK (сценарий **C**).

## Структура

```
02-teo-ptica/
├── content/        ← T01–T12, appendix, land/energy yaml (канon текста)
├── pipeline/       ← phases 1–10, narrative sources, media, reports
│   └── docx/       ← сгенерированные Word (gitignore)
├── scenarios/
│   ├── poultry-teo.yaml
│   └── poultry-variant.yaml
└── exports/        ← готовые выгрузки (release mirror)
```

## Команды

```bash
python3 scripts/build-teo-poultry-from-baseline.py
python3 scripts/verify-baseline-poultry-docx.py
python3 scripts/generate-pticevodstvo-docx.py      # investor pack
python3 scripts/generate-apk-master-docx.py        # corpus APK
```

## KPI (канon)

CAPEX **12 000** | выручка **5 559** | NPV **+2 253** @10% 16y | IRR **12,8%** | **476** FTE | **118** птичников

Baseline для clone: `../01-teo-kroliki/docx/1.ТЭO_МOЯ МEЧTA.docx`

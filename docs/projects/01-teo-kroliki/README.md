# Проект 1 — основное ТЭO (кролики, APK baseline)

**APK «МОЯ МЕЧТА» 100 млрд ₽**, блок I = кролиководство (baseline).

## Структура

```
01-teo-kroliki/
├── docx/           ← master 1.ТЭO_МOЯ МEЧTA.docx (~66 MB, не в git)
├── finmodel/       ← 1.2-слайд Фин модель.xlsx
├── corpus/
│   ├── graphify-corpus/   ← 7 сводных md (RAG primary)
│   └── teo/              ← 140 md-слайсов baseline DOCX
├── inventory/      ← registry T01–T13, reports, theme docx
└── scenarios/
    └── baseline.yaml
```

## Команды

```bash
python3 scripts/extract-teo-docx-tables.py    # tables → docs/teo-tables/
python3 scripts/generate-krolikovodstvo-docx.py
python3 scripts/validate-krolikovodstvo-rag.py
graphify query "NPV кролиководство"
```

## KPI (канon)

См. `scenarios/baseline.yaml` и `docs/teo-tables/critical/T007-npv-krolikovodstvo.md`.

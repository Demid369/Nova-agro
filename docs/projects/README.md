# Проекты «МОЯ МЕЧТА» / Nova-Agro

Три изолированных контура в одном репозитории.

| # | Папка | Содержание |
|---|--------|------------|
| **1** | [`01-teo-kroliki/`](01-teo-kroliki/) | Основное ТЭO APK **100 млрд**, блок I = **кролики** (baseline) |
| **2** | [`02-teo-ptica/`](02-teo-ptica/) | Блок I **птица «Нова-Агро»** 12 млрд — контент, pipeline, DOCX |
| **3** | [`03-proekt-tbd/`](03-proekt-tbd/) | Резерв под **третий проект** (пусто) |

## Общее (shared)

| Путь | Назначение |
|------|------------|
| [`docs/teo-tables/`](../teo-tables/) | 241 таблица Word + critical (baseline + poultry) |
| [`graphify-out/`](../../graphify-out/) | Graph baseline (RAG) |
| [`teo-rag-out/`](../../teo-rag-out/) | Vector/BM25 индекс |
| [`scripts/`](../../scripts/) | Сборка, RAG, inventory |

## Быстрые команды

```bash
# Птица: полное ТЭO ~694 стр. из baseline DOCX
python3 scripts/build-teo-poultry-from-baseline.py
python3 scripts/verify-baseline-poultry-docx.py

# Кролики: theme DOCX + RAG validate
python3 scripts/generate-krolikovodstvo-docx.py
python3 scripts/validate-krolikovodstvo-rag.py
```

Карта документов (legacy INDEX): [`01-teo-kroliki/corpus/teo/INDEX.md`](01-teo-kroliki/corpus/teo/INDEX.md)

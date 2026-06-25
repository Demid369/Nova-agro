# Graphify — граф знаний ТЭО «МОЯ МЕЧТА»

> **Рабочий проект = baseline** — текущее ТЭО (кролиководство, теплицы, КРС/МРС, рыба, масложир).  
> **Птица = parked** — черновик **второго ТЭО** в `docs/scenarios/poultry-variant.*`. Не применять к корпусу и графу. См. `docs/scenarios/README.md`.

Этот репозиторий настроен для [Graphify](https://github.com/safishamsi/graphify): документ `docs/1.ТЭО_МОЯ МЕЧТА.docx` преобразован в markdown-корпус и подключён к Cursor.

## Структура

| Путь | Назначение |
|------|------------|
| `docs/1.ТЭО_МОЯ МЕЧТА.docx` | Исходный ТЭО (66 МБ, **не индексируется** Graphify — лимит 50 МБ) |
| `docs/teo/` | Нарезка docx по заголовкам (140 файлов) |
| `docs/graphify-corpus/` | **Корпус для Graphify** — 6 сводных markdown-файлов |
| `graphify-out/` | Граф: `graph.json`, `GRAPH_REPORT.md`, `graph.html`, `QUERY_WALKTHROUGH.md` |

## Быстрый старт в Cursor

1. Установите CLI (один раз на машине):

```bash
uv tool install "graphifyy[office]==0.8.49"
graphify cursor install
```

2. В чате Cursor:

```
/graphify docs/graphify-corpus
```

Для обновления после правок:

```
/graphify docs/graphify-corpus --update
```

## Запросы к графу

```bash
graphify query "какие блоки дают экспортную выручку?"
graphify query "нулевая себестоимость мяса побочные продукты" --budget 2500
graphify path "Убойный цех" "Халяльный желатин"
graphify path "ООО МОЯ МЕЧТА" "Чёрная икра"
graphify explain "Животноводство КРС/МРС"
```

Откройте `graphify-out/graph.html` в браузере для интерактивной карты.

Разбор ключевых цепочек: `graphify-out/QUERY_WALKTHROUGH.md`

## Именование сообществ

```bash
uv tool run --from graphifyy==0.8.49 python scripts/label-teo-communities.py
```

Русские имена сообществ → `.graphify_labels.json`, обновление `GRAPH_REPORT.md` и `graph.html` (без LLM API).

## Пересборка полного графа

```bash
uv tool run --from graphifyy==0.8.49 python scripts/build-full-teo-graph.py
```

Обрабатывает **146 markdown-файлов**. Фильтр шума + **norm_id с кириллицей** + ограничение co-occurrence в `04-rynok` (только секции 4.2/4.3/5.1/6.1 и project-relevant параграфы).

## Семантическая экстракция (умные связи, deep mode)

```bash
uv tool run --from graphifyy==0.8.49 python scripts/build-smart-semantic-graph.py
```

Сливает:
- структурный граф (`extraction-full.json`, 146 md-файлов)
- доменную онтологию ТЭО (бизнес-модель, цепочки, риски)
- LLM-чанки из `graphify-out/.graphify_chunk_*.json` (если есть)

Для перегенерации LLM-чанков в Cursor: `/graphify docs/graphify-corpus --mode deep`

Текущий граф (после fix norm_id + semantic merge): **~8 400** узлов, **~24 700** рёбер, **~595** сообществ. `graph.html` — агрегированный вид по сообществам (>5000 узлов).

Стартовый мини-граф (29 узлов):

```bash
uv tool run --from graphifyy==0.8.49 python scripts/build-teo-graph.py
```

Опционально — headless LLM-экстракция (нужен `GEMINI_API_KEY`):

```bash
export GEMINI_API_KEY=...
graphify extract docs/graphify-corpus --mode deep
```

## Что уже настроено в репозитории

- `.cursor/rules/graphify.mdc` — Cursor всегда учитывает граф
- `.cursor/rules/teo-rag.mdc` — гибридный RAG (graph + vector)
- `.claude/skills/graphify/` — skill для Claude Code
- `CLAUDE.md` / `AGENTS.md` — инструкции для ассистентов
- `.graphifyignore` — исключает тяжёлый docx и детальную нарезку

## TEO RAG (гибрид Graph + Vector + Memory)

Полнотекстовый поиск по всему корпусу (`docs/teo/` + `docs/graphify-corpus/`) поверх графа Graphify.

```bash
pip install -r requirements-teo-rag.txt
python scripts/build-teo-vector-index.py
python scripts/teo-query.py "NPV теплиц" --mode auto
python scripts/teo-query.py "как убой связан с желатином?" --mode hybrid
python scripts/teo-query.py "NPV теплиц" --synthesize --save-memory  # validation + memory
python scripts/test-teo-system.py  # полная проверка (118 проверок, 50 запросов)
python scripts/benchmark-teo-rag.py --json  # роутер + latency → teo-rag-out/benchmark-latest.json
```

Дорожная карта: `docs/TEO_ROADMAP.md`  
Простыми словами: `docs/TEO_ПРОСТЫМИ_СЛОВАМИ.md`  
NotebookLM (витрина отчётов): `docs/NOTEBOOKLM.md`

| Режим | Когда |
|-------|-------|
| `graph` | связи, path, цепочки |
| `vector` | факты, NPV, цитаты |
| `hybrid` | риски + меры, экспорт + продукты |
| `summary` | обзор проекта (corpus) |
| `memory` | кэш проверенных ответов |

Документация: `docs/TEO_RAG.md`, архитектура: `docs/TEO_RAG_ARCH.md`


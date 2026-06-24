# Graphify — граф знаний ТЭО «МОЯ МЕЧТА»

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
uv tool install "graphifyy[office]"
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
uv tool run --from graphifyy python scripts/label-teo-communities.py
```

Русские имена сообществ → `.graphify_labels.json`, обновление `GRAPH_REPORT.md` и `graph.html` (без LLM API).

## Пересборка полного графа

```bash
uv tool run --from graphifyy python scripts/build-full-teo-graph.py
```

Обрабатывает **146 markdown-файлов** (`docs/graphify-corpus/` + `docs/teo/`), строит структурный граф. Встроенный **фильтр шума** отсекает торговую статистику (`*-табл-*`, экспорт/импорт по странам, метрики).

## Семантическая экстракция (умные связи, deep mode)

```bash
uv tool run --from graphifyy python scripts/build-smart-semantic-graph.py
```

Сливает:
- структурный граф (`extraction-full.json`, 146 md-файлов)
- доменную онтологию ТЭО (бизнес-модель, цепочки, риски)
- LLM-чанки из `graphify-out/.graphify_chunk_*.json` (если есть)

Для перегенерации LLM-чанков в Cursor: `/graphify docs/graphify-corpus --mode deep`

Текущий граф (после фильтра шума + semantic merge): **~2500 узлов**, **~6300 рёбер**, **~280 сообществ**.

Стартовый мини-граф (29 узлов):

```bash
uv tool run --from graphifyy python scripts/build-teo-graph.py
```

Опционально — headless LLM-экстракция (нужен `GEMINI_API_KEY`):

```bash
export GEMINI_API_KEY=...
graphify extract docs/graphify-corpus --mode deep
```

## Что уже настроено в репозитории

- `.cursor/rules/graphify.mdc` — Cursor всегда учитывает граф
- `.claude/skills/graphify/` — skill для Claude Code
- `CLAUDE.md` / `AGENTS.md` — инструкции для ассистентов
- `.graphifyignore` — исключает тяжёлый docx и детальную нарезку

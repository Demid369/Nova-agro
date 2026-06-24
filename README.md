# Graphify — граф знаний ТЭО «МОЯ МЕЧТА»

Этот репозиторий настроен для [Graphify](https://github.com/safishamsi/graphify): документ `docs/1.ТЭО_МОЯ МЕЧТА.docx` преобразован в markdown-корпус и подключён к Cursor.

## Структура

| Путь | Назначение |
|------|------------|
| `docs/1.ТЭО_МОЯ МЕЧТА.docx` | Исходный ТЭО (66 МБ, **не индексируется** Graphify — лимит 50 МБ) |
| `docs/teo/` | Нарезка docx по заголовкам (140 файлов) |
| `docs/graphify-corpus/` | **Корпус для Graphify** — 6 сводных markdown-файлов |
| `graphify-out/` | Граф: `graph.json`, `GRAPH_REPORT.md`, `graph.html` |

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
graphify path "ООО «МОЯ МЕЧТА»" "Халяльный желатин"
graphify explain "Нулевая себестоимость мяса"
```

Откройте `graphify-out/graph.html` в браузере для интерактивной карты.

## Пересборка полного графа

```bash
uv tool run --from graphifyy python scripts/build-full-teo-graph.py
```

Обрабатывает **146 markdown-файлов** (`docs/graphify-corpus/` + `docs/teo/`), строит полный граф со всеми извлечёнными связями.

Текущий граф: **~4200 узлов**, **~12000 рёбер**, **~300 сообществ**.

Стартовый мини-граф (29 узлов):

```bash
uv tool run --from graphifyy python scripts/build-teo-graph.py
```

```bash
export GEMINI_API_KEY=...   # или OPENAI_API_KEY / ANTHROPIC_API_KEY
graphify extract docs/graphify-corpus
```

## Что уже настроено в репозитории

- `.cursor/rules/graphify.mdc` — Cursor всегда учитывает граф
- `.claude/skills/graphify/` — skill для Claude Code
- `CLAUDE.md` / `AGENTS.md` — инструкции для ассистентов
- `.graphifyignore` — исключает тяжёлый docx и детальную нарезку

# Архитектура TEO RAG (Graph + Vector + Memory)

## Цель

Ориентация по всему ТЭО «МОЯ МЕЧТА»: связи между блоками (граф) + полнотекстовый поиск (вектор) + кэш проверенных ответов (память).

## Слои

| Слой | Технология | Путь | Назначение |
|------|------------|------|------------|
| Graph | Graphify | `graphify-out/graph.json` | path, explain, бизнес-цепочки |
| Vector | Chroma + multilingual embeddings | `teo-rag-out/chroma/` | факты, цитаты, NPV, риски |
| Memory | JSONL | `teo-rag-out/memory.jsonl` | validated Q&A |
| Corpus | Markdown | `docs/graphify-corpus/`, `docs/teo/` | источник чанков |

## Роутер запросов

```
                    ┌─────────────┐
                    │   Запрос    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         memory hit    классификация   default
              │            │            │
              ▼            ▼            ▼
           memory      graph /      hybrid
                      vector /     (graph+vector)
                      hybrid
```

| Тип | Триггеры | Маршрут |
|-----|----------|---------|
| `graph` | связь, цепочка, path, как связано, от … к … | `graphify query/path` |
| `vector` | цитата, NPV, IRR, таблица, сколько, что пишет | Chroma retrieval |
| `hybrid` | риски + меры, экспорт + продукты | graph + vector |
| `summary` | обзор, структура проекта | tier=summary only |
| `memory` | точное совпадение validated Q&A | memory.jsonl |

## Иерархический retrieval

1. **Уровень 1:** `tier=summary` (6 файлов corpus) — top 3
2. **Уровень 2:** все чанки `tier=detail` — top 8
3. Merge, dedupe по `source`, сортировка по score

## Индексация

- **Включено:** `docs/graphify-corpus/*.md`, `docs/teo/*.md` кроме exclude
- **Exclude:** `*-табл-*`, `в-*-гг-*`, trade-stat по имени файла
- **04-rynok:** нарезка по `##` / `#` заголовкам, max ~4000 символов, overlap 300
- **Metadata:** см. `schemas/chunk-metadata.json`

## CLI

```bash
# Индексация (после правок корпуса)
python scripts/build-teo-vector-index.py

# Запрос
python scripts/teo-query.py "как бесплатный убой связан с экспортом?" --mode auto
python scripts/teo-query.py "NPV теплиц" --mode vector
python scripts/teo-query.py "path убой желатин" --mode graph

# Сохранить ответ в память (только validation OK)
python scripts/teo-query.py "..." --synthesize --save-memory
```

## Валидация

- Числа в ответе сверяются с evidence corpus (retrieved chunks + graph)
- `--synthesize` автоматически включает `--validate`
- `--save-memory` → `teo-rag-out/memory.jsonl` + `graphify save-result`

## Citations

Каждый ответ содержит:
- `source` — путь к md
- `section` — заголовок чанка
- `graph` — узлы/рёбра (если graph/hybrid)

## Зависимости

См. `requirements-teo-rag.txt`: chromadb, sentence-transformers.

# TEO RAG — гибрид Graph + Vector + Memory

## Быстрый старт

```bash
pip install -r requirements-teo-rag.txt
python scripts/build-teo-vector-index.py
python scripts/teo-query.py "NPV теплиц" --mode auto
```

## Архитектура

| Слой | Путь | Когда |
|------|------|-------|
| Graph | `graphify-out/graph.json` | связи, path, цепочки |
| Vector | `teo-rag-out/chroma/` | факты, NPV, цитаты |
| Memory | `teo-rag-out/memory.jsonl` | проверенные Q&A |
| Corpus | `docs/graphify-corpus/`, `docs/teo/` | источник чанков |

Подробнее: `docs/TEO_RAG_ARCH.md`

## CLI

```bash
# Авто-роутер
python scripts/teo-query.py "как бесплатный убой связан с экспортом?"

# Явный режим
python scripts/teo-query.py "NPV теплиц" --mode vector
python scripts/teo-query.py "path убой желатин" --mode graph
python scripts/teo-query.py "обзор проекта" --mode summary

# JSON + сохранение в память
python scripts/teo-query.py "инвестиции 100 млрд" --json --save-memory
```

## Индексация

- **Включено:** все `docs/graphify-corpus/*.md` + `docs/teo/*.md` кроме trade-stat
- **Exclude:** `*-табл-*`, `в-*-гг-*`, экспорт товаров группы
- **04-rynok:** нарезка по заголовкам, max 4000 символов, overlap 300
- **Embeddings:** `intfloat/multilingual-e5-small` (prefix `query:` / `passage:`)

После правок корпуса:

```bash
python scripts/build-teo-vector-index.py
```

## Роутер

| mode | Триггеры |
|------|----------|
| `graph` | связь, path, цепочка, explain |
| `vector` | NPV, IRR, цитата, сколько, млрд |
| `hybrid` | риски, экспорт, комбикорм (default) |
| `summary` | обзор, структура проекта |
| `memory` | точное совпадение в `memory.jsonl` |

## Citations

Каждый ответ содержит `citations`:

- `chunk` — `source`, `section`, `chunk_id`, `excerpt`
- `graph_node` — `label`, `source`, `community`
- `graph_edge` — `source_node`, `relation`, `target_node`

## Тесты

```bash
# Роутер на 10 вопросах
python -c "
import yaml
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from teo_rag.router import classify_query
data = yaml.safe_load(Path('tests/teo-queries.yaml').read_text())
ok = 0
for q in data['queries']:
    d = classify_query(q['query'])
    match = d.mode == q['expected_mode']
    ok += match
    print(('OK' if match else 'MISS'), q['id'], d.mode, '!=', q['expected_mode'] if not match else '')
print(ok, '/', len(data['queries']))
"
```

## Файлы

| Файл | Назначение |
|------|------------|
| `scripts/teo_rag/chunks.py` | нарезка, exclude trade-stat |
| `scripts/teo_rag/retrieval.py` | Chroma + hierarchical search |
| `scripts/teo_rag/router.py` | классификация запросов |
| `scripts/teo-query.py` | единый CLI |
| `schemas/chunk-metadata.json` | схема metadata |
| `teo-rag-out/manifest.json` | статистика индекса |

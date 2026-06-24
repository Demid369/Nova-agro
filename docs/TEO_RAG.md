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
| KPI | `teo-rag-out/kpi.json` | NPV/IRR/CAPEX по блокам (fast path) |
| BM25 + rerank | `teo-rag-out/bm25-index.json` | лексический merge + cross-encoder |
| Scenarios | `docs/scenarios/*.yaml` | what-if сравнение вариантов |
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
python scripts/teo-query.py "сценарий птица вместо кроликов" --mode scenario

# KPI fast path (без embedding/rerank) — auto/vector без --synthesize
python scripts/teo-query.py "NPV теплиц" --mode vector

# JSON + сохранение в память (только после validation)
python scripts/teo-query.py "инвестиции 100 млрд" --synthesize --save-memory
python scripts/teo-query.py "NPV теплиц" --mode vector --synthesize llm
python scripts/teo-query.py "..." --validate  # проверка чисел без синтеза
```

## Индексация

- **Включено:** все `docs/graphify-corpus/*.md` + `docs/teo/*.md` кроме trade-stat
- **Exclude:** `*-табл-*`, `в-*-гг-*`, экспорт товаров группы
- **04-rynok:** нарезка по заголовкам, max 4000 символов, overlap 300
- **Embeddings:** `intfloat/multilingual-e5-small` (prefix `query:` / `passage:`)

После правок корпуса:

```bash
python scripts/build-teo-vector-index.py   # также обновляет kpi.json и сбрасывает bm25-кэш
python scripts/build-teo-kpi-index.py      # только KPI из 00-summary.md
```

**Retrieval (волна 1):** vector top-K + BM25 merge (веса 0.55/0.45) → `BAAI/bge-reranker-v2-m3` rerank top-8.

## Роутер

| mode | Триггеры |
|------|----------|
| `graph` | связь, path, цепочка, explain |
| `vector` | NPV, IRR, цитата, сколько, млрд |
| `kpi` | fast path при NPV/IRR (внутри auto/vector, без synthesize) |
| `scenario` | сценарий, what-if, замена, сравни вариант |
| `hybrid` | риски, экспорт, комбикорм (default) |
| `summary` | обзор, структура проекта |
| `memory` | точное совпадение в `memory.jsonl` |

## Валидация и синтез (фаза 4)

```bash
# Extractive — только предложения из retrieved
python scripts/teo-query.py "NPV теплиц" --mode vector --synthesize

# LLM (Gemini) — нужен GEMINI_API_KEY, ответ валидируется по corpus
python scripts/teo-query.py "NPV теплиц" --synthesize llm

# Сохранение в memory + graphify save-result (только validation OK)
python scripts/teo-query.py "NPV теплиц" --synthesize --save-memory
```

Валидатор проверяет **значимые числа** (≥3 цифр или с единицами) в ответе против evidence corpus (chunks + graph). Неподтверждённые числа → `validation.valid=false`, exit code 2.

`--save-memory` пишет в `teo-rag-out/memory.jsonl` и вызывает `graphify save-result` с graph nodes из citations.

## Citations

Каждый ответ содержит `citations`:

- `chunk` — `source`, `section`, `chunk_id`, `excerpt`
- `graph_node` — `label`, `source`, `community`
- `graph_edge` — `source_node`, `relation`, `target_node`

## Сценарии what-if

```bash
python scripts/teo-scenario.py list
python scripts/teo-scenario.py show poultry-variant
python scripts/teo-scenario.py compare baseline poultry-variant
python scripts/teo-query.py "what-if замена кроликов на птицеводство" --mode auto
```

Черновик `poultry-variant` — оценочные NPV/CAPEX, требует пересчёта финмодели.

## Полная проверка системы

```bash
python scripts/test-teo-system.py   # infra + router + graph + vector + KPI + BM25 + scenarios
python scripts/benchmark-teo-rag.py   # роутер + latency на 25 запросах
```

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
| `scripts/teo_rag/retrieval.py` | Chroma + BM25 hybrid + rerank |
| `scripts/teo_rag/kpi.py` | структурированные KPI из 00-summary |
| `scripts/teo_rag/bm25_index.py` | BM25 индекс по чанкам |
| `scripts/teo_rag/scenarios.py` | YAML what-if сценарии |
| `scripts/teo-scenario.py` | CLI сравнения сценариев |
| `scripts/teo_rag/router.py` | классификация запросов |
| `scripts/teo_rag/validator.py` | anti-hallucination для чисел |
| `scripts/teo_rag/synthesis.py` | extractive / LLM синтез |
| `scripts/teo_rag/memory.py` | memory.jsonl + graphify save-result |
| `schemas/chunk-metadata.json` | схема metadata |
| `teo-rag-out/manifest.json` | статистика индекса |

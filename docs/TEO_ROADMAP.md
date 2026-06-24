# TEO RAG — дорожная карта

## Текущий фокус

**Рабочий проект = baseline** (ТЭО «МОЯ МЕЧТА», кролиководство).  
**Птица = parked** — отдельное второе ТЭО, позже.

---

## Сделано

| Фаза | Что | Статус |
|------|-----|--------|
| 0–4 | Graph + Vector + Memory + validation + synthesis | main |
| Волна 1 | KPI fast path, BM25+rerank | main |
| Волна 2 | Scenario apply (инфраструктура), reranker cache | main |
| Волна 3 | README/roadmap, memory seed, benchmark report | main |
| Волна 4 | 50 тест-запросов + memory checklist | main |
| Волна 5 | Memory seed 15 ответов + объяснение | main |

Тесты: `python scripts/test-teo-system.py` → **120+** проверок

---

## Волна 3 — настройка baseline ✅

1. Явная политика baseline vs parked в README
2. Memory seed — `tests/teo-memory-seed.yaml`
3. Benchmark report — `teo-rag-out/benchmark-latest.json`

---

## Волна 4 — качество ответов baseline ✅

1. `tests/teo-queries.yaml` — **50 запросов** (кролики, убой, экспорт, блоки, риски)
2. `tests/teo-memory-checklist.md` — чек-лист для `--save-memory`
3. Benchmark: `python scripts/benchmark-teo-rag.py --json` → 50/50 router

```bash
python scripts/benchmark-teo-rag.py --json
python scripts/test-teo-system.py
```

---

## Волна 5 — память ✅

15 проверенных ответов в `tests/teo-memory-seed.yaml`. Объяснение для команды: `docs/TEO_ПРОСТЫМИ_СЛОВАМИ.md`.

```bash
python scripts/seed-teo-memory-baseline.py
```

---

## Волна 6 — второе ТЭО (птица, позже)

1. Отдельный корпус `docs/teo-poultry/` или новый scenario-id
2. Свой vector index / KPI — **без** перезаписи baseline
3. Сравнение baseline vs teo2 через `teo-scenario.py compare`

До волны 6 **не** менять `00-summary.md` и **не** `apply poultry-variant`.

---

## Ежедневные команды (baseline)

```bash
python scripts/teo-query.py "<вопрос>" --mode auto
python scripts/teo-query.py "NPV кролиководство" --mode vector      # KPI fast path
python scripts/teo-query.py "path убой желатин" --mode graph
python scripts/teo-query.py "..." --synthesize --validate --save-memory
python scripts/test-teo-system.py
```

После правок корпуса:

```bash
python scripts/build-teo-vector-index.py
uv tool run --from graphifyy python scripts/build-full-teo-graph.py
```

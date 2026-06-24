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
| Волна 3 | README/roadmap, memory seed, benchmark report | в работе |

Тесты: `python scripts/test-teo-system.py` → **72/72**

---

## Волна 3 — настройка baseline (сейчас)

1. Явная политика baseline vs parked в README
2. **Memory seed** — проверенные ответы по ключевым KPI/фактам (`tests/teo-memory-seed.yaml`)
3. **Benchmark report** — `teo-rag-out/benchmark-latest.json` (роутер + latency)
4. Обновить docs (TEO_RAG, ARCH) под BM25/KPI слои

```bash
python scripts/seed-teo-memory-baseline.py
python scripts/benchmark-teo-rag.py --json
python scripts/test-teo-system.py
```

---

## Волна 4 — качество ответов baseline

1. Расширить `tests/teo-queries.yaml` до 40–50 запросов (кролики, теплицы, убой, экспорт, риски)
2. Регрессия: benchmark в CI / перед релизом
3. Накопление memory через `--synthesize --save-memory` по чек-листу топ-вопросов
4. NotebookLM / витрина для людей (опционально) — поверх RAG, не вместо графа

---

## Волна 5 — второе ТЭО (птица, позже)

1. Отдельный корпус `docs/teo-poultry/` или новый scenario-id
2. Свой vector index / KPI — **без** перезаписи baseline
3. Сравнение baseline vs teo2 через `teo-scenario.py compare`

До волны 5 **не** менять `00-summary.md` и **не** `apply poultry-variant`.

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

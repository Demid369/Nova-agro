# Сценарии what-if

## Активный проект

| ID | Статус | Описание |
|----|--------|----------|
| **baseline** | **active** | Текущее ТЭО «МОЯ МЕЧТА» — кролиководство, теплицы, КРС/МРС и т.д. |

Корпус: `docs/graphify-corpus/00-summary.md`, граф `graphify-out/graph.json`, KPI `teo-rag-out/kpi.json`.

## Parked (второе ТЭО — позже)

| ID | Статус | Описание |
|----|--------|----------|
| poultry-variant | **parked** | Черновик what-if (эвристика KPI). **Не применять** к рабочему проекту. |
| **poultry-teo** | **draft** | Второе ТЭО: текст в `docs/teo-poultry/`, KPI в `docs/scenarios/poultry-teo.yaml`. |

Файлы `poultry-variant.*` — заготовка инфраструктуры what-if.  
**Рабочий контент птицы:** `docs/teo-poultry/` + `docs/inventory/pticevodstvo/`.

Когда будет готово второе ТЭО, оформится как отдельный корpus или `apply poultry-teo`.

**Не запускать** без явной необходимости:

```bash
# НЕ для текущей работы
python scripts/apply-teo-scenario.py apply poultry-variant
```

Вернуть baseline после экспериментов:

```bash
python scripts/apply-teo-scenario.py restore
```

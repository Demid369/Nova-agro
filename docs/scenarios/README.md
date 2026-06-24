# Сценарии what-if

## Активный проект

| ID | Статус | Описание |
|----|--------|----------|
| **baseline** | **active** | Текущее ТЭО «МОЯ МЕЧТА» — кролиководство, теплицы, КРС/МРС и т.д. |

Корпус: `docs/graphify-corpus/00-summary.md`, граф `graphify-out/graph.json`, KPI `teo-rag-out/kpi.json`.

## Parked (второе ТЭО — позже)

| ID | Статус | Описание |
|----|--------|----------|
| poultry-variant | **parked** | Черновик отдельного ТЭО с птицеводством. **Не применять** к рабочему проекту. |

Файлы `poultry-variant.*` — заготовка инфраструктуры. Когда будет готово второе ТЭО, оформится как отдельный корпус или новый scenario-id.

**Не запускать** без явной необходимости:

```bash
# НЕ для текущей работы
python scripts/apply-teo-scenario.py apply poultry-variant
```

Вернуть baseline после экспериментов:

```bash
python scripts/apply-teo-scenario.py restore
```

# ТЭО «МОЯ МЕЧТА» — блок птицеводства (draft)

**Статус:** черновик второго ТЭО. **Не active baseline.**  
**Baseline (кролики)** не трогаем: `docs/graphify-corpus/`, `docs/scenarios/baseline.yaml`, `docs/inventory/krolikovodstvo/`.

## Куда класть ваши материалы

| Что у вас есть | Куда положить |
|----------------|---------------|
| Любые готовые файлы (docx, pdf, xlsx, txt, md) — «как есть» | **`_incoming/`** — временная зона загрузки |
| Финмодель, NPV, CAPEX, цены | **`T01-finance.md`** + цифры в **`docs/scenarios/poultry-teo.yaml`** |
| Мощность, головы, цеха, фазы | **`T02-scale-phase.md`** |
| Породы, технология выращивания | **`T03-genetics-tech.md`** |
| Оборудование, площадки, линии | **`T04-equipment.md`** |
| Убой, переработка | **`T05-slaughter-processing.md`** |
| Корма, рецепты, FRAGOLA | **`T06-feed.md`** |
| Помёт, перья, побочка | **`T07-byproducts.md`** |
| Энергия на площадке | **`T08-energy.md`** |
| Рынок РФ, SWOT, оптовые цены | **`T09-market-swot.md`** |
| Экспорт, HS 0207 | **`T10-export.md`** |
| Миссия, цели, резюме проекта | **`T11-narrative-mission.md`** |
| Мировой рынок птицы | **`T12-world-market.md`** |
| Таблицы, расчёты, приложения | **`appendix/`** |

После переноса из `_incoming/` в тематические `T*.md` — помечайте в `_incoming/README.md`, что уже разобрано.

## Темы (T01–T12)

Зеркало структуры кроликов (`docs/inventory/krolikovodstvo/`), но **только птица**.

| ID | Файл | Содержание |
|----|------|------------|
| T01 | `T01-finance.md` | NPV, IRR, CAPEX, payback, цена ₽/кг |
| T02 | `T02-scale-phase.md` | т/год, головы, цеха, фазы |
| T03 | `T03-genetics-tech.md` | породы, схема выращивания |
| T04 | `T04-equipment.md` | линии, инкубаторы, площадки |
| T05 | `T05-slaughter-processing.md` | птицеубой, разделка |
| T06 | `T06-feed.md` | комбикорм, рецепты |
| T07 | `T07-byproducts.md` | помёт, перья, биогаз |
| T08 | `T08-energy.md` | солнечные, энергия |
| T09 | `T09-market-swot.md` | SWOT, цены РФ |
| T10 | `T10-export.md` | экспорт HS 0207 |
| T11 | `T11-narrative-mission.md` | narrative |
| T12 | `T12-world-market.md` | мировой рынок птицы |

## Structured KPI (YAML)

Цифры для RAG/KPI (когда согласованы):

```
docs/scenarios/poultry-teo.yaml
```

Пока `status: draft` — **не** подменяет `baseline.yaml`.

## Inventory (карта блока)

```
docs/inventory/pticevodstvo/registry.yaml
```

Машиночитаемая карта: тема → файлы. DOCX и audit — позже, когда текст заполнен.

## Чего пока нет (волна 2)

- `docs/graphify-corpus-poultry/` — сводка для Graphify/RAG
- `apply poultry-teo` — только после утверждения текста
- правки `docs/graphify-corpus/00-summary.md`

## Команды (когда появится corpus)

```bash
# эвристика от кроликов (ориентир, не финал):
python3 scripts/apply-teo-scenario.py derive-poultry

# НЕ запускать на baseline:
# python3 scripts/apply-teo-scenario.py apply poultry-variant
```

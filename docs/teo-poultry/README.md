# ТЭО «МОЯ МЕЧТА» — блок птицеводства (draft)

**Статус:** черновик с **реальными материалами Нова-Агро** (июнь 2026).  
**Baseline (кролики)** не тронут.

## Загруженные материалы (25.06.2026)

| Оригинал | Где лежит |
|----------|-----------|
| Технологический цикл | `_incoming/01-tehnologicheskiy-cikl-pticefabriki.docx` → `appendix/01-…md` → T03–T05 |
| Затраты, оргструктура, штат | `_incoming/02-zatraty-orgstruktura-shtat.docx` → `appendix/02-…md` |
| Сводный расчёт | `_incoming/03-svodnyy-raschet-kompleksa.docx` → `appendix/03-…md` → T02, T11 |
| Финмодель 12 млрд | `_incoming/finmodel-pticekompleks-12-mlrd.xlsx` → T01, T02, T06, T09 |

**Ключевые цифры (finmodel, sync с кроликами):** CAPEX **12 млрд ₽**, выручка **5 559 млн ₽/год**, EBITDA **2 216**, NPV **+2 253**, IRR **≈12,8%**, окупаемость **5,4 года**, **476** сотрудников, **118** птичников.

## Локация и земля (канон, июнь 2026)

| | |
|--|--|
| **Регион / юр. адрес** | Запорожская область, г. Мелитополь, просп. Богдана Хмельницкого, д. 24А |
| **APK холдинга (птица)** | **250 000 га** |
| **Под строительство (все блоки)** | **20 000 га** |
| **Слот блока птицеводства** | **400 га** |
| **Производственная площадка** | **не выделена** — см. `land-budget.yaml` |

Baseline «МОЯ МЕЧТА» — **100 000 га APK, Херсонская область**; контур птицы — отдельный, **Запорожская** — согласовать при интеграции.

## APK 100 млрд (канон)

**Сценарий C:** птица **12 000**, блоки 2–5 **−958,5** пропорционально → **ровно 100 000**.  
Детали: `appendix/apk-100bln-integration.md`, `docs/scenarios/poultry-teo.yaml` → `project.apk_100bln`.

## До уровня ТЭО кроликов — что ещё нужно

| # | Пробел | У кроликов | У птицы сейчас |
|---|--------|------------|----------------|
| 1 | **Master DOCX + 241 таблица** | `1.ТЭО_МОЯ МЕЧТА.docx` → `teo-tables/` | **master draft:** `inventory/pticevodstvo/docx/00-master-teo-pticevodstvo-draft.docx` |
| 2 | **Пакет T01–T12 DOCX** | `generate-krolikovodstvo-docx.py` | **`generate-pticevodstvo-docx.py`** → 12 тем + index |
| 3 | **RAG / graph / audit** | corpus, 50 queries, docx-audit | **draft**, не в индексе |
| 4 | **Вендоры + пропускная способность** | Meneghin, SINT 2400 г/ч | **Facco + SINT poultry 6000 + FRAGOLA/PRIMERANO/ASTORIOS** |
| 5 | **Рецептуры кормов** (Tab. P-141) | `teo/125-…` (фактически КРС+рыба; **без SKU**) | **draft** [`appendix/feed-recipes-table.md`](appendix/feed-recipes-table.md) + [`T141-feed-recipes-poultry`](../teo-tables/critical/T141-feed-recipes-poultry.md) |
| 6 | **График CAPEX по годам** | T022 investment schedule | **T022-P**: структура % + **фазировка 2026–2029** (модель под ramp) |
| 7 | **Экспорт** | Tab#5 baseline на блок 1 | `export-apk-baseline-tab5.md` |
| 8 | **Земля: кадастр, схема, разрешения** | T003 land budget | `production_site: null` |
| 9 | **Выводы + реестр рисков** | `graphify-corpus/06-vyvody-i-riski.md` | **draft** [`appendix/06-vyvody-i-riski.md`](appendix/06-vyvody-i-riski.md) — §12.3, 15 рисков R-P01…R-P15 |
| 10 | **Меморандум / front matter** | `00-меморандум-о-конфиденциальности.md` | **draft** [`appendix/00-front-matter-nova-agro.md`](appendix/00-front-matter-nova-agro.md) |
| 11 | **Качество переработки / выход** | corpus T05 | T05 — 16 строк |
| 12 | **NPV-методология vs tab#7** | 10 лет, единый горизонт | **16 лет** — [`appendix/dcf-policy.md`](appendix/dcf-policy.md) |

**Уже не хуже / лучше кроликов:** finmodel (NPV/IRR, чувствительность), штат 476 FTE, energy canon, APK-100, multi-product.

## Статус тем

| Тема | Статус |
|------|--------|
| T01 финансы + NPV/IRR + финансирование | **xlsx + md** |
| T10 экспорт | **10,2 млрд Tab#5** на блок 1; **птица 0% export** | `appendix/export-apk-baseline-tab5.md` |
| T04/T05 вендоры | **Facco + SINT poultry 6000/ч + baseline infra** | `appendix/vendors-equipment.md` |
| T12 мировой рынок | FAO 2023 |
| Энергия (= кролики) | `energy-budget.yaml`, листы CAPEX/OPEX |

## Куда добавлять новые данные

| Что | Куда |
|-----|------|
| Новые файлы «как есть» | `_incoming/` |
| Текст по темам | `T01-…` … `T12-…` |
| KPI | `docs/scenarios/poultry-teo.yaml` |
| Большие таблицы | `appendix/` |
| Critical-таблицы (T001-P…) | [`appendix/tables-poultry-index.md`](appendix/tables-poultry-index.md) → `docs/teo-tables/critical/` |
| §12.3 риски | [`appendix/06-vyvody-i-riski.md`](appendix/06-vyvody-i-riski.md) |

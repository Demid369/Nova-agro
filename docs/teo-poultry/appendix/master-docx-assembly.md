# Сборка master DOCX — птица вместо кроликов

> **Статус:** план сборки (jun 2026)  
> **Эталон:** `docs/1.ТЭО_МОЯ МЕЧТА.docx` → [`graphify-corpus/`](../../graphify-corpus/) + [`teo-tables/`](../../teo-tables/) (241 tab)  
> **Блок птицы:** [`docs/teo-poultry/`](..) + critical **T001-P…T236-P**

## Что такое «master DOCX» у кроликов

| Слой | Где | Роль |
|------|-----|------|
| **Оригинал** | `1.ТЭО_МОЯ МЕЧТА.docx` | Единый документ ~13 разделов + приложения |
| **Текст (RAG)** | `graphify-corpus/00–07` (7 файлов) | Оглавление §1–§13, narrative, рынок, производство |
| **Таблицы** | `teo-tables/all/` **241** + `critical/` **18** | Word-таблицы; graphify терял tab при конвертации |
| **Тематические DOCX** | `generate-krolikovodstvo-docx.py` → `inventory/krolikovodstvo/docx/` | **Не** master — 13 тем T01–T13 для замены блока |

**Вывод:** master = **склейка corpus + critical tables + правки I-фазы**. Отдельного `generate-master-teo-docx.py` **нет**; у птицы его тоже нет.

---

## Карта разделов оригинала → источник для master

| § | Раздел оригинала | AS-IS (без правок) | ЗАМЕНА (птица) | Статус птицы |
|---|------------------|--------------------|----------------|--------------|
| — | Меморандум, титул | `graphify-corpus/01-vvedenie` (начало) | [`00-front-matter-nova-agro.md`](00-front-matter-nova-agro.md) | ✅ draft |
| 1 | Цель, резюме | APK narrative (общее) | front matter §1 + `appendix/03-svodnyy-raschet` (T11 dedupe) | ✅ draft |
| 2 | Заказчик | baseline «МОЯ МЕЧТА» / Херсон | **ООО «Нова-Агро»**, Мелитополь — только блок 1 | ⚠️ частично |
| 2.3 | Потенциал | I-фаза **кролики** в `01-vvedenie` | `T02-scale-phase.md`, `T001-P` | ✅ |
| 3 | Стратегия | общие формулировки APK | адаптировать §3 под птицу | ⚠️ |
| 4 | Рынок, маркетинг | **APK-wide** в `04-rynok` (КРС, рыба, масло…) | `T09-market-swot.md` — **блок птицы** | ✅ draft |
| 4 | *кролик* | абзацы крольчатины в `04-rynok`, teo/08 | `T12-world-market.md` (FAO птица) | ✅ |
| 5 | Материалы, энергия | зерно APK, биогаз 20 МВт | `T06-feed`, `T08-energy`, `energy-budget.yaml` | ✅ |
| 6 | Местоположение | T003 baseline **100k га Херсон** | **T003-P** (250k / слот 400 га) | ✅ draft; кадастр TBD (R-04) |
| 7.1 | Мощность по годам | ramp кроликов в docx | `T02`, `T022-P`, finmodel «Экономика» | ✅ |
| 7.2 | Технология | **кролики** в `03-proizvodstvo` | `appendix/01-tehnologicheskiy-cikl.md`, T03–T05 | ✅ |
| 8 | Оргструктура, OPEX | общие + кролик | `appendix/02-zatraty…`, **T236-P** | ✅ |
| 9 | Кадры | T236 кролик 300 FTE | **T236-P** 476 FTE | ✅ |
| 10 | Схемы, график, бюджет | `05-finansy` (текст) + **T022** | **T022-P** (фазировка 2026–2029) | ✅ |
| 11 | Финансовая оценка | методология 10 лет @10% | **T007-P**, `npv-irr-derived.md` (**16 лет**, R-03) | ✅ draft |
| 11 | NPV других блоков | **T008–T011** | **AS-IS** (сценарий C CAPEX в T021-P) | ✅ as-is |
| 12.1–12.2 | Выводы | `06-vyvody-i-riski` (generic) | `appendix/06-vyvody-i-riski.md` | ✅ |
| 12.3 | Риски | generic + кролик | **R-P01…R-P15** | ✅ |
| 13 | Приложение «А» | teo/ trade HS (**103 tab**) | **AS-IS** | ✅ |

---

## Таблицы: AS-IS vs ЗАМЕНА

### Critical (18 baseline) — что делаем

| Tab# | Baseline (кролик) | Действие | Птица |
|------|-------------------|----------|-------|
| **1** | T001 master, I-фаза кролик | **patch строки I-фазы** | **T001-P** + II–III из [`T001-master-summary-phases.md`](../../teo-tables/critical/T001-master-summary-phases.md) as-is |
| **3** | T003 land 100k Херсон | **отдельный контур** или footnote | **T003-P** |
| **4** | T004 revenue, строки кролик | **заменить 4 строки** (мясо/субпр/удобр/итого блока) | **T004-P**; теплицы/КРС/рыба/МЖК — **без изменений** |
| **5** | T005 export APK | **AS-IS** Tab#5 (10 208 млн) | птица export **0** — строку в consolidated **не добавляли** |
| **7** | T007 NPV кролик | **replace** | **T007-P** |
| **8–11** | NPV теплицы/КРС/рыба/МЖК | **AS-IS** | — |
| **14** | T014 CAPEX по фазам | **patch** строку блока 1 + сценарий C totals | **T021-P** |
| **21** | T021 CAPEX кролик 12 000 | **replace** строка I-фазы | **T021-P** |
| **22** | T022 investment schedule | **replace** блок 1.1.x | **T022-P** |
| **141** | Tab.141 КРС+рыба (mislabel «кролик») | **AS-IS** для APK | **T141-P** — **отдельно** для птицы (66 712 t) |
| **236** | T236 staff кролик | **replace** | **T236-P** |
| **237–240** | штат других блоков | **AS-IS** | — |
| **241** | налоги | **rename** «Кролиководство» → «Птицеводство», ставки те же | из T236-P ФОТ |

### Остальные 223 таблицы

| Категория | Кол-во | Действие |
|-----------|--------|----------|
| `reference_trade` | 103 | **AS-IS** (HS-статистика) |
| `other` | 106 | **в основном AS-IS**; ~12 с «кролик» в title — заменить только если попадают в тело §7–§9 |
| `project_revenue` / прочие | 14 | сверить по manifest; кролик — только в tab 17–30, 184–186 |

---

## Текстовый слой: что забрать из baseline без изменений

### `graphify-corpus/` — целиком или почти

| Файл | Брать as-is | Вырезать / заменить |
|------|-------------|-------------------|
| **00-summary** | блоки 2–5, KPI теплицы/КРС/рыба/МЖК, экспорт 10,2 | строки «Кролиководство 7 000 т», land 50 гa кролик |
| **01-vvedenie** | §2.1–2.2 (если оставляем «МОЯ МЕЧТА»), demography, APK intro | титул «кроликов мясных пород», §I-фаза кролик, Meneghin/ANCI |
| **03-proizvodstvo** | КРС, рыба, теплицы, Tab.141 **КРС/рыба**, биогаз | разделы «Кролики», убой кролика 2400, рецепты «для кроликов» |
| **04-rynok** | рынки КРС, молоко, икра, масло, SWOT APK | крольчатина, BusinesStat кролик, HS кролик |
| **05-finansy** | §10–11 методология, налоги (текст) | ссылки на «кроликовodческую ферму» в таблицах |
| **06-vyvody** | категории рисков 1–9 (framework) | — (птица: свой `06-vyvody-i-riski`) |
| **07-docx-tables** | индекс + land baseline | дополнить секцией poultry index |

### `docs/teo/` (140 файлов)

- **AS-IS:** trade tables teo/09–109, меморандум `00-…`, финансы `138–139`
- **Archive:** teo/124–125 (кролики) → заменены corpus + T141-P
- **Не включать в master блок 1:** teo/08 (рынок крольчатины)

---

## Что уже есть по птице (готово к вставке в master)

### Critical tables (8)

См. [`tables-poultry-index.md`](tables-poultry-index.md).

### Темы T01–T12 (md → будущий DOCX)

| ID | Файл | Строк | Покрывает § |
|----|------|-------|-------------|
| T01 | `T01-finance.md` | ~73 | §11, finmodel |
| T02 | `T02-scale-phase.md` | ~32 | §7.1, 2.3 |
| T03 | `T03-genetics-tech.md` | ~35 | §7.2 |
| T04 | `T04-equipment.md` | ~51 | §7.2 Facco |
| T05 | `T05-slaughter-processing.md` | ~36 | §7.2 SINT 6000 |
| T06 | `T06-feed.md` | ~40 | §5, Tab P-141 |
| T07 | `T07-byproducts.md` | ~29 | помёт, compost |
| T08 | `T08-energy.md` | ~59 | §5.3 solar 10 |
| T09 | `T09-market-swot.md` | ~57 | §4 |
| T10 | `T10-export.md` | ~55 | §4.1.5 (птица 0%, Tab#5 APK) |
| T11 | `T11-narrative-mission.md` | ~30 | §1 |
| T12 | `T12-world-market.md` | ~42 | §4 FAO птица |

### Appendix (развёрнутый текст)

| Файл | Строк | Назначение |
|------|-------|------------|
| `01-tehnologicheskiy-cikl.md` | ~121 | §7.2 полный цикл |
| `02-zatraty-orgstruktura-shtat.md` | ~400+ | §8–9, T236-P деталь |
| `03-svodnyy-raschet-kompleksa.md` | ~200+ | §1, продукты, narrative |
| `feed-recipes-table.md` + T141-P | | §5.1 корма |
| `06-vyvody-i-riski.md` | | §12.3 |
| `finmodel-pticekompleks-12-mlrd.xlsx` | | источник tab NPV/CAPEX |

### Structured

- `docs/scenarios/poultry-teo.yaml` — KPI, vendors, risks
- `land-budget.yaml`, `energy-budget.yaml`

---

## Рекомендуемый порядок сборки master DOCX

```
1. Front matter (меморандум Нова-Агро)                    ← СОЗДАТЬ
2. §1–3: T11 + T02 + patch заказчик/регион               ← md готов, нужен merge
3. §4: T09 + T12 + (AS-IS 04-rynok для блоков 2–5)       ← частично
4. §5–6: T06 + T08 + T003-P                              ← готов
5. §7: appendix/01 + T03–T05 + T141-P                    ← готов
6. §8–9: appendix/02 + T236-P                            ← готов
7. §10: T022-P + 05-finansy §10                          ← готов
8. §11: T007-P + T004-P + T008–T011 + T021-P             ← готов; 10 vs 16 лет — решить
9. §12: appendix/06-vyvody-i-riski                       ← готов
10. Приложение А: teo-tables reference_trade AS-IS        ← готов
11. generate-pticevodstvo-docx.py (аналог кроликов)       ← СОЗДАТЬ
12. Склейка → 1.ТЭО_МОЯ_МЕЧТА_ПТИЦА.docx                  ← СОЗДАТЬ
```

---

## Пробелы (блокируют «как оригинал»)

| # | Пробел | Критичность |
|---|--------|-------------|
| 1 | Нет `generate-pticevodstvo-docx.py` | высокая |
| 2 | Нет единого `.docx` на выходе | высокая |
| 3 | Оригинал `1.ТЭО_МОЯ МЕЧТА.docx` не в git — только md/tab extract | средняя |
| 4 | Incoming docx 01–03 не в git (есть md) | низкая |
| 5 | Два контура земли (100k Херсon vs 250k Запорожье) | средняя |
| 6 | T004/T005 consolidated — строка птицы vs patch | средняя |
| 7 | NPV 16y vs baseline 10y в §11 | средняя |
| 8 | Меморандум / титул Нова-Агро | средняя |

---

## Оценка готовности master

| Компонент | % | Комментарий |
|-----------|---|-------------|
| Critical tables блок 1 | **~90%** | 8/8 draft; T241 rename; T001 merge II–III |
| Текст §7–9 (производство) | **~85%** | incoming md + T03–T05 |
| Финансы §10–11 | **~80%** | finmodel + T007/T022; политика DCF |
| Рынок §4 | **~70%** | T09/T12; нет полного §4.1 как в docx |
| Front / §1–3 APK | **~40%** | T11 короткий; много текста still in corpus-кролик |
| Приложение А (241 tab) | **~95%** | AS-IS; 12 tab с кроликом — точечная замена |
| **Итого master DOCX** | **~65%** | content есть; **склейки нет** |

Следующий шаг: **`generate-pticevodstvo-docx.py`** + **`00-master-assembly.yaml`** → draft DOCX, затем ручная склейка с baseline docx или pandoc pipeline.

**Реализовано (jun 2026):**

```bash
python3 scripts/generate-pticevodstvo-docx.py
# → docs/inventory/pticevodstvo/docx/00-master-teo-pticevodstvo-draft.docx
```

Манифест: [`docs/inventory/pticevodstvo/00-master-assembly.yaml`](../../inventory/pticevodstvo/00-master-assembly.yaml)

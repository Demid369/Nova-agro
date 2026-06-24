# Инвентарь кролиководства (baseline «МОЯ МЕЧТА»)

**Статус:** рабочий источник для будущей замены блока (птица — отдельное ТЭО, позже).  
**Не применять:** `apply poultry-variant`, правки `poultry-variant.yaml` как active baseline.

## Назначение

Единое место хранения всего, что относится к **проектному кролиководству** и связанному **рыночному контексту** (включая мировой рынок крольчатины). При переходе на новое ТЭО с птицей — заменяем документы из этого каталога.

## Структура

```
docs/inventory/krolikovodstvo/
  README.md              ← вы здесь
  registry.yaml            ← машиночитаемый реестр: тема → файлы → действие
  docx/                    ← готовые DOCX по направлениям (генерируются)
  reports/
    rag-validation.json    ← сверка RAG vs исходный ТЭО
    rag-validation.docx
```

## Темы (направления)

| ID | Файл DOCX | Содержание |
|----|-----------|------------|
| T01 | `T01-finance.docx` | NPV, IRR, CAPEX, payback, цена 560 ₽/кг |
| T02 | `T02-scale-phase.docx` | 6 млн голов, 7 000 т, 81 цех, I-фаза |
| T03 | `T03-genetics-zootech.docx` | ANCI, породы, F1, разведение |
| T04 | `T04-equipment.docx` | Meneghin Srl, 69 цехов, автоматизация |
| T05 | `T05-slaughter-processing.docx` | SINT 2400 г/ч, разделка, переработка |
| T06 | `T06-feed.docx` | FRAGOLA, табл. 141, рецепты |
| T07 | `T07-byproducts.docx` | навоз 43 800 т, мех/шкурка, компост |
| T08 | `T08-energy.docx` | солнечные 10 МВт·ч на фермах |
| T09 | `T09-market-swot.docx` | SWOT, цены РФ, ниша, конкуренция |
| T10 | `T10-export.docx` | экспортные рынки крольчатины (проект) |
| T11 | `T11-narrative-mission.docx` | миссия, цели, резюме про кроликов |
| T12 | `T12-world-market-reference.docx` | мировой рынок, FAOSTAT, табл. 23/39 |
| — | `00-index-krolikovodstvo.docx` | оглавление + сводная таблица файлов |
| — | `reports/rag-validation.docx` | проверка: исходный ТЭО vs RAG |

Каждый DOCX содержит **ссылки на исходный ТЭО** в формате `файл:строка` (например `docs/graphify-corpus/01-vvedenie-i-resume.md:712–810`).

## Команды

```bash
# Сгенерировать все DOCX по темам
python scripts/generate-krolikovodstvo-docx.py

# Сверка RAG с исходным docs/teo и corpus
python scripts/validate-krolikovodstvo-rag.py

# Обновить DOCX отчёта валидации
python scripts/validate-krolikovodstvo-rag.py --docx
```

## Слои данных

| Слой | Путь | Роль в инвентаре |
|------|------|------------------|
| Исходный ТЭО | `docs/teo/` | эталон для сверки RAG |
| RAG-корпус | `docs/graphify-corpus/` | то, что индексируется |
| Сценарий | `docs/scenarios/baseline.yaml` | структурированные KPI блока |
| Индексы | `teo-rag-out/`, `graphify-out/` | артефакты (пересборка после замены) |

## Действие при замене (позже)

В `registry.yaml` у каждого источника поле `action_on_replace`: `replace` | `adapt` | `archive` | `rebuild_index`.

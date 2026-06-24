# NotebookLM — витрина для сгенерированных материалов

> **NotebookLM ≠ TEO RAG.** RAG (graph + vector + KPI) — для точных ответов с citations.  
> NotebookLM — для **людей**: читать, обсуждать, слушать Audio Overview, показывать инвесторам.

---

## Что можно и нельзя

| | Consumer (notebooklm.google.com) | Enterprise (Google Cloud) |
|--|----------------------------------|---------------------------|
| API загрузки | **Нет** | **Да** (`uploadFile`, batchCreate) |
| Ручная загрузка | Да (pdf, md, docx, txt…) | Да |
| Автосинх REPO → Notebook | Нет официально | Да, через API + cron |
| Цена | бесплатно / Plus | GCP billing |

**Вывод:** без Enterprise — **полуавтомат**: мы генерируем файлы → ты (или скрипт) загружаешь в notebook.

---

## Рекомендуемая схема (baseline ТЭО)

```
TEO RAG / отчёты
       │
       ▼
docs/reports/          ← DOCX, MD отчёты
notebooklm-export/     ← bundle для загрузки (скрипт)
       │
       ▼
NotebookLM notebook «МОЯ МЕЧТА — baseline»
       │
       ▼
Люди: чат, summary, audio (не для production-цифр без проверки)
```

**Правило:** цифры NPV/IRR для банка/инвестора — из `teo-query.py` + KPI, не «как NotebookLM пересказал».

---

## Шаг 1 — создать notebook (один раз)

1. Открой https://notebooklm.google.com
2. **New notebook** → имя: `МОЯ МЕЧТА — baseline (кролики)`
3. **Не смешивай** с будущим вторым ТЭО (птица) — отдельный notebook позже.

---

## Шаг 2 — базовые источники (один раз)

Загрузи в notebook **минимальный набор** (не весь 04-rynok — лимит источников):

| Файл | Зачем |
|------|-------|
| `docs/graphify-corpus/00-summary.md` | KPI, блоки, модель |
| `docs/graphify-corpus/01-vvedenie-i-resume.md` | описание проекта |
| `docs/graphify-corpus/06-vyvody-i-riski.md` | риски |
| `docs/TEO_ПРОСТЫМИ_СЛОВАМИ.md` | как устроена система |

Или один bundle:

```bash
python scripts/export-notebooklm-bundle.py
# → notebooklm-export/latest/ — загрузи все .md оттуда
```

---

## Шаг 3 — когда генерируете новый файл

1. Сохраняете отчёт в `docs/reports/` (DOCX или MD).
2. Запускаете:

```bash
python scripts/export-notebooklm-bundle.py --reports-only
```

3. В NotebookLM: **Add source** → загрузить новый файл из `notebooklm-export/latest/reports/`.

**Частота:** после каждого значимого отчёта или раз в неделю — не после каждого `teo-query`.

---

## Шаг 4 (опционально) — Google Drive

Если удобнее:

1. Папка Drive: `TEO МОЯ МЕЧТА / notebooklm`
2. Скрипт копирует bundle туда (rclone / Drive desktop).
3. В NotebookLM: Add source → **Google Drive** → выбрать файл.

Так проще обновлять без повторной загрузки с диска.

---

## Enterprise API (если есть Google Cloud)

Официальная загрузка:

```bash
curl -X POST --data-binary "@docs/reports/отчет.md" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "X-Goog-Upload-File-Name: отчет.md" \
  -H "X-Goog-Upload-Protocol: raw" \
  -H "Content-Type: text/markdown" \
  "https://LOCATION-discoveryengine.googleapis.com/upload/v1alpha/projects/PROJECT/locations/LOCATION/notebooks/NOTEBOOK_ID/sources:uploadFile"
```

Документация: [Add and manage data sources (API)](https://cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks-sources)

Переменные для будущего скрипта:

```bash
export NOTEBOOKLM_PROJECT=...
export NOTEBOOKLM_LOCATION=...
export NOTEBOOKLM_NOTEBOOK_ID=...
```

---

## Что НЕ класть в NotebookLM

- `teo-rag-out/chroma/`, `graph.json` — не читается как документ
- `poultry-variant` — **parked**, отдельный notebook когда будет второе ТЭО
- trade-stat таблицы (`*-табл-*`) — шум, уже excluded из vector index

---

## Связка с TEO RAG

| Задача | Инструмент |
|--------|------------|
| Точный NPV, path, validation | `python scripts/teo-query.py` |
| Отчёт для людей | DOCX/MD → `docs/reports/` |
| Витрина / обсуждение | NotebookLM |
| Автопроверка системы | `python scripts/test-teo-system.py` |

---

## Чек-лист после настройки

- [ ] Notebook «МОЯ МЕЧТА — baseline» создан
- [ ] Загружен `00-summary.md` + bundle или ключевые md
- [ ] `docs/reports/` — место для новых отчётов
- [ ] Процесс: отчёт → `export-notebooklm-bundle.py` → Add source
- [ ] Второе ТЭО (птица) — **отдельный** notebook, не сейчас

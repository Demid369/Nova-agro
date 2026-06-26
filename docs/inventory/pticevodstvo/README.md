# Инвентарь птицеводства (draft)

**Статус:** standalone **PASS** + **investor-ready** (jun 2026). Corpus merge pipeline — **started**. RAG/graph — по approval.

## Investor-ready

| Артефакт | Путь |
|----------|------|
| One-pager | [`docs/teo-poultry/appendix/investor-one-pager.md`](../../teo-poultry/appendix/investor-one-pager.md) |
| Executive summary | front matter § «Executive summary» |
| Stress-pack | [`docs/teo-poultry/appendix/stress-pack.md`](../../teo-poultry/appendix/stress-pack.md) |

## Final run (рекомендуется перед review)

```bash
python3 scripts/final-run-pticevodstvo.py
```

Отчёт: [`reports/final-run-jun2026.md`](reports/final-run-jun2026.md)  
Corpus merge: [`CORPUS-MERGE-NEXT.md`](CORPUS-MERGE-NEXT.md)

## APK full master (corpus + appendix A)

```bash
python3 scripts/generate-apk-master-docx.py
# быстрый тест: --appendix-limit 10
```

Выход: `docx/00-apk-master-teo-full-draft.docx`

## Команды

```bash
# Валидация registry + assembly (без DOCX)
python3 scripts/generate-pticevodstvo-docx.py --skip-docx

# Темы T01–T12 + index + master draft
python3 scripts/generate-pticevodstvo-docx.py

# Только master
python3 scripts/generate-pticevodstvo-docx.py --master-only
```

## Выходные DOCX

| Файл | Содержание |
|------|------------|
| `00-index-pticevodstvo.docx` | KPI + оглавление тем |
| `t01-…` … `t12-…` | Темы из `docs/teo-poultry/T*.md` |
| **`00-master-teo-pticevodstvo-draft.docx`** | Master draft по `00-master-assembly.yaml` |
| **`00-apk-master-teo-full-draft.docx`** | APK full: standalone + corpus + appendix A |

План сборки: [`docs/teo-poultry/appendix/master-docx-assembly.md`](../../teo-poultry/appendix/master-docx-assembly.md)

## Куда добавлять данные

| Тип | Путь |
|-----|------|
| Темы | `docs/teo-poultry/T01-…` … `T12-…` |
| Сырые файлы | `docs/teo-poultry/_incoming/` |
| Приложения | `docs/teo-poultry/appendix/` |
| KPI | `docs/scenarios/poultry-teo.yaml` |
| Critical tab | `docs/teo-tables/critical/T*-pticevodstvo*.md`, T241-P |

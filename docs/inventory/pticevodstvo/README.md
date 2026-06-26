# Инвентарь птицеводства (draft)

**Статус:** черновик второго ТЭО. **Не active baseline.**

## Назначение

Аналог `docs/inventory/krolikovodstvo/`, но источник = **`docs/teo-poultry/`** + critical **T001-P…T236-P**.

## Структура

```
docs/inventory/pticevodstvo/
  README.md
  registry.yaml                 ← KPI, темы T01–T12, critical tables
  00-master-assembly.yaml       ← манифест master DOCX (§1–§12)
  docx/                         ← генерируется
  reports/docx-audit.json
```

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

План сборки: [`docs/teo-poultry/appendix/master-docx-assembly.md`](../../teo-poultry/appendix/master-docx-assembly.md)

## Куда добавлять данные

| Тип | Путь |
|-----|------|
| Темы | `docs/teo-poultry/T01-…` … `T12-…` |
| Сырые файлы | `docs/teo-poultry/_incoming/` |
| Приложения | `docs/teo-poultry/appendix/` |
| KPI | `docs/scenarios/poultry-teo.yaml` |
| Critical tab | `docs/teo-tables/critical/T*-pticevodstvo*.md` |

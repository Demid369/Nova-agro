# Таблицы ТЭО «МОЯ МЕЧТА» (из docx)

Канон: [`docs/1.ТЭО_МОЯ МЕЧТА.docx`](../1.ТЭО_МОЯ%20МЕЧТА.docx) · финмодель: [`1.2-слайд Фин модель.xlsx`](../1.2-%D1%81%D0%BB%D0%B0%D0%B9%D0%B4%20%D0%A4%D0%B8%D0%BD%20%D0%BC%D0%BE%D0%B4%D0%B5%D0%BB%D1%8C.xlsx) (Приложение 3Б, 100 млрд ₽)

| Каталог | Содержание |
|---------|------------|
| [`manifest.json`](manifest.json) | 241 таблиц, SHA256-хеши |
| [`all/`](all/) | все таблицы `T001`…`T241` |
| [`critical/`](critical/) | 18 проектных таблиц |
| [`land-budget.yaml`](land-budget.yaml) | структурированный земельный баланс (#3) |

Обновление:

```bash
python3 scripts/extract-teo-docx-tables.py
python3 scripts/validate-teo-docx-tables.py
```

# Media extraction plan — baseline DOCX → APK master

> **Статус:** план (jun 2026) | **Baseline:** `docs/1.ТЭО_МОЯ МЕЧТА.docx` — **не в git**  
> **Оценка:** ~346 embedded images в baseline

## Зачем

Corpus merge (`generate-apk-master-docx.py`) собирает **текст + md-таблицы**. Embedded images (схемы, фото оборудования, карты) остаются только в оригинальном DOCX.

## Pipeline (когда baseline docx доступен локально)

```bash
# 1. Извлечь media из baseline
python3 scripts/extract-docx-media.py \
  --input docs/1.ТЭО_МОЯ\ МЕЧТА.docx \
  --output docs/inventory/pticevodstvo/media/

# 2. Сгенерировать manifest (rId → filename → section hint)
# → docs/inventory/pticevodstvo/media/manifest.json

# 3. При финальной склейке APK master — re-embed по manifest
# (будущий: merge-apk-docx-with-media.py)
```

## Категории media (ожидаемые)

| Категор | ~шт | Действие для блока 1 |
|---------|-----|----------------------|
| Схемы технологии кролика | ~20 | **Заменить** на Facco/SINT poultry (incoming 01–03) |
| Карты / земля Херсон | ~15 | **Footnote** R-01; T003-P для блока 1 |
| Trade / HS графики | ~200 | **AS-IS** (приложение «А») |
| КРС / рыба / теплицы | ~100 | **AS-IS** |
| Прочее (логотипы, декор) | ~11 | **AS-IS** |

## Блокеры

1. Baseline DOCX не в репозитории — нужен локальный файл или S3
2. Нет `extract-docx-media.py` — scaffold в phase C2
3. Poultry-specific images (118 птичников, УПК) — из `_incoming/` docx или вендоров

## MVP без media

Текущий `00-apk-master-teo-full-draft.docx` — **text + tables only**. Достаточно для:
- RAG / graphify index
- Financial due diligence
- Недостаточно для **pixel-perfect** clone baseline

## Следующий commit (optional)

- `scripts/extract-docx-media.py` — unzip docx `word/media/*`
- `media/manifest.json` — после первого прогона на машине с baseline

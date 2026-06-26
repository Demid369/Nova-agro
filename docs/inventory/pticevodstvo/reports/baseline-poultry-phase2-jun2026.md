# Phase 2 — narrative §7 + Tab P-141 + captions (jun 2026)

> **Команда:** `python3 scripts/build-teo-poultry-from-baseline.py` (phase2 включён)  
> **Или:** `python3 scripts/apply-teo-poultry-phase2.py`

## Результат

| Проверка | Статус |
|----------|--------|
| Drawings preserved | **394 / 394** ✓ |
| §7 narrative (body 9873–9952) | **32 chunks poultry** → 69 slots |
| Tab P-141 title + balance table | **T141-P** ✓ |
| Image binaries | **AS-IS** (image7–9, image311–313) |
| Captions block 1 + §7 | **updated** (placeholder «фото — заменить») |

## §7 после замены (sample)

| body# | Текст |
|-------|-------|
| 9873 | Технологический цикл птицефабрики |
| 9875 | ПТИЦЕВОДЧЕСКИЙ КОМПЛЕКС «НОВА-АГРО» |
| 9888 | 4. Этап II. Выращивание и откорм по видам |
| 9970 | Tab. P-141. Рецепты комбикормов — птицеводство (баланс finmodel) |

## Image slots (замена binary)

| Файл | Слот | Было |
|------|------|------|
| image7.png, image8.jpeg | Tab#18 cell 0 | Кролики F1 |
| image9.png | Tab#18 cell 1 | Мясо кролика |
| image311.jpeg | §7 body 9889 | Убой кролика |
| image312.jpeg | §7 body 9928 | Разделка |
| image313.jpeg | §7 body 9935 | Оборудование |

```bash
python3 scripts/replace-docx-media.py \
  --docx docs/inventory/pticevodstvo/docx/1.ТЭO_МOЯ_МEЧTA_ПTIЦA.docx \
  --name image7.png --file path/to/facco.png
```

## «Кролик» ~315 — ожидаемо

Trade HS, blocks 2–5, **не тронутые image-paragraphs**, KRS/fish Tab.141 footnotes.

## Следующее

- Binary swap image7–9, 311–313 когда будут assets
- Rabbit yield table (body ~9939) → poultry FCR table
- Narrative §4 block 1 (рынок крольчатины в corpus) — отдельный pass

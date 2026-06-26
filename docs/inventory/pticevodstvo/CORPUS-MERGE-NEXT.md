# Corpus merge — следующая фаза (не начата)

> **Решение jun 2026:** standalone блок 1 (**12 млрд**) закрыт final run **PASS**.  
> Полный clone `1.ТЭО_МОЯ МЕЧТА.docx` — **отдельная задача**, не блокирует review standalone.

## Зачем отдельно

| | Standalone (готово) | Full APK master |
|--|---------------------|-----------------|
| Объём | ~60–80 стр. | ~500–700+ стр. |
| Scope | Блок 1 замена | + corpus §4, блоки 2–5, приложение «А» |
| Риск | низкий | высокий (Запорожье/Херсон, media, 241 tab) |
| ROI сейчас | **investor review блока** | позже, при merge 100 млрд |

## Что потребуется

1. **Pipeline:** baseline docx + patch sections из `00-master-assembly.yaml` (не только md→docx)
2. **Corpus as-is:** `graphify-corpus/04-rynok` (~111k слов), `03-proizvodstvo` (блоки 2–5)
3. **Приложение «А»:** 103 `reference_trade` из `docs/teo/`
4. **Media:** 346 embedded images из baseline docx
5. **Единый land/legal footnote** R-01 на уровне master

## Команда старта (когда решите)

```bash
# Сейчас — только standalone
python3 scripts/final-run-pticevodstvo.py

# Будущее — отдельная ветка cursor/apk-corpus-merge-7293
```

## Источники

- [`reports/final-run-jun2026.md`](reports/final-run-jun2026.md)
- [`../../teo-poultry/appendix/master-docx-assembly.md`](../../teo-poultry/appendix/master-docx-assembly.md)
- PR #13

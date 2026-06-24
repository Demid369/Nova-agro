# Чек-лист: накопление memory (baseline ТЭО)

Все пункты ниже — в `tests/teo-memory-seed.yaml`.  
Применить: `python scripts/seed-teo-memory-baseline.py`

## Seed (готово)

- [x] NPV теплиц
- [x] NPV кролиководство
- [x] NPV рыбоводство
- [x] NPV масложировой комбинат
- [x] инвестиции 100 млрд
- [x] выручка проекта
- [x] обзор структура проекта
- [x] экспорт 10,2 млрд
- [x] сколько тонн крольчатины в год
- [x] нулевая себестоимость 5,6 млрд
- [x] чёрная икра белуга
- [x] как бесплатный убой связан с желатином и кожей?
- [x] path убой желатин
- [x] комбикорм подсолнечник соя животноводство
- [x] риски биологические ветеринарные меры снижения

## Добавлять вручную (после --save-memory)

Новые уникальные вопросы из практики — только если `validation.valid=true`:

```bash
python scripts/teo-query.py "<новый вопрос>" --synthesize --save-memory
```

## Регрессия

```bash
python scripts/test-teo-system.py           # 120+ проверок
python scripts/benchmark-teo-rag.py --json   # 50/50 router
python scripts/seed-teo-memory-baseline.py
```

# Инвентарь птицеводства (draft)

**Статус:** черновик второго ТЭО. **Не active baseline.**

## Назначение

Карта блока «птица» `docs/inventory/krolikovodstvo/`, но источник текста = **`docs/teo-poultry/`**, не corpus кроликов.

## Куда добавлять данные

| Тип данных | Путь |
|------------|------|
| Основной текст по темам | `docs/teo-poultry/T01-…` … `T12-…` |
| Сырые файлы | `docs/teo-poultry/_incoming/` |
| Таблицы, приложения | `docs/teo-poultry/appendix/` |
| KPI (цифры) | `docs/scenarios/poultry-teo.yaml` |
| Карта тем (машиночитаемо) | `registry.yaml` (этот каталог) |

## DOCX / audit

Генерация DOCX — **волна 2** (когда T01–T03 заполнены).  
Скрипт `generate-krolikovodstvo-docx.py` пока заточен под кроликов; для птицы — отдельный скрипт или параметр позже.

## Связь с кроликами

При активации птицы: `docs/inventory/krolikovodstvo/` → archive/reference, этот каталог → active block map.

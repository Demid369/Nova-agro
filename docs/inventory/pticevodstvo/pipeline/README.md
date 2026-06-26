# Pipeline — baseline DOCX → птица

Оркестратор: **`manifest.yaml`**.  
Единая команда: `python3 scripts/build-teo-poultry-from-baseline.py`

## Фазы (порядок фиксирован)

| # | Файл | Скрипт | Содержание |
|---|------|--------|------------|
| 1 | [`phase1-tables.yaml`](phase1-tables.yaml) | `build-teo-poultry-from-baseline.py` | Копия baseline → critical tables T001/T003/T004/… + regex |
| 2 | [`phase2-section7.yaml`](phase2-section7.yaml) | `apply-teo-poultry-phase2.py` | §7 narrative (`appendix/01-tehnologicheskiy-cikl.md`) + Tab P-141 |
| 3 | [`phase3-market.yaml`](phase3-market.yaml) | `apply-teo-poultry-phase3.py` | Block1 marketing, T03 genetics, §4 product/world, Tab 140/23/39-P |
| 4 | [`phase4-export.yaml`](phase4-export.yaml) | `apply-teo-poultry-phase4.py` | §4 export RF tail (кролик → птица T10) |

Флаги: `--skip-phase2`, `--skip-phase3`, `--skip-phase4`

## Corpus merge (отдельный трек)

| Файл | Команда |
|------|---------|
| [`assembly-standalone.yaml`](assembly-standalone.yaml) | `generate-pticevodstvo-docx.py` |
| [`assembly-apk-full.yaml`](assembly-apk-full.yaml) | `generate-apk-master-docx.py` |
| [`corpus-patch-rules.yaml`](corpus-patch-rules.yaml) | patch при corpus merge |

## Источники narrative (не дублировать в teo-poultry)

| Файл | Назначение |
|------|------------|
| [`../sources/narrative/block1-marketing.md`](../sources/narrative/block1-marketing.md) | Block 1 intro (body 485–530) |
| [`../sources/narrative/product-poultry.md`](../sources/narrative/product-poultry.md) | §4.1.1.1 product |
| [`../sources/narrative/world-market-poultry.md`](../sources/narrative/world-market-poultry.md) | §4.1.1.2 FAO world |
| `docs/teo-poultry/T03-genetics-tech.md` | Genetics block (phase3) |
| `docs/teo-poultry/appendix/01-tehnologicheskiy-cikl.md` | §7 (phase2) |

## Body indices

Индексы `body_start` / `body_table_index` привязаны к **текущему** baseline DOCX.  
При обновлении оригинала — пересканировать:

```bash
python3 scripts/build-teo-poultry-from-baseline.py --verify-only
# + ручной scan body indices (см. reports/)
```

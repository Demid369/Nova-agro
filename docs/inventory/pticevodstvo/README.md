# Инвентарь птицевodство — hub

> **Карта всего ТЭO:** [`docs/teo/INDEX.md`](../../teo/INDEX.md)  
> **Pipeline yaml:** [`pipeline/`](pipeline/) · **Manifest:** [`pipeline/manifest.yaml`](pipeline/manifest.yaml)

## Главная команда (baseline → птица ~694 стр.)

```bash
python3 scripts/build-teo-poultry-from-baseline.py
# --skip-phase2 | --skip-phase3 | --skip-phase4
# --extract-media → media/* (346 files, gitignored)
```

| Фаза | Config | Что меняет |
|------|--------|------------|
| 1 | [`pipeline/phase1-tables.yaml`](pipeline/phase1-tables.yaml) | Critical tables + regex |
| 2 | [`pipeline/phase2-section7.yaml`](pipeline/phase2-section7.yaml) | §7 + Tab P-141 |
| 3 | [`pipeline/phase3-market.yaml`](pipeline/phase3-market.yaml) | §4 market, genetics, yield |
| 4 | [`pipeline/phase4-export.yaml`](pipeline/phase4-export.yaml) | §4 export (T10) |

## Выходные DOCX

См. [`outputs/README.md`](outputs/README.md) → каталог [`docx/`](docx/)

| DOCX | ~стр. | Команда |
|------|-------|---------|
| **`1.ТЭO_МOЯ_МEЧTA_ПTIЦA.docx`** | **~694** | `build-teo-poultry-from-baseline.py` |
| `00-master-teo-pticevodstvo-draft.docx` | ~60–80 | `generate-pticevodstvo-docx.py` |
| `00-apk-master-teo-full-draft.docx` | ~220–250 | `generate-apk-master-docx.py` |

## Контент vs pipeline

| Слой | Где | Роль |
|------|-----|------|
| **Канон текста** | [`docs/teo-poultry/`](../../teo-poultry/) | T01–T12, appendix, KPI |
| **Narrative-slice для Word** | [`sources/narrative/`](sources/narrative/) | Короткие вставки по body-range |
| **Critical tables** | [`docs/teo-tables/critical/`](../../teo-tables/critical/) | Tab 1,3,4,7,… P-variants |
| **Media** | [`media/`](media/) | image-map, slots замены |

## Investor-ready

| Артефакт | Путь |
|----------|------|
| One-pager | [`docs/teo-poultry/appendix/investor-one-pager.md`](../../teo-poultry/appendix/investor-one-pager.md) |
| Stress-pack | [`docs/teo-poultry/appendix/stress-pack.md`](../../teo-poultry/appendix/stress-pack.md) |

## Прочие команды

```bash
python3 scripts/final-run-pticevodstvo.py          # registry validate
python3 scripts/generate-pticevodstvo-docx.py      # standalone master
python3 scripts/generate-apk-master-docx.py        # APK corpus merge
python3 scripts/replace-docx-media.py --help       # binary image swap
```

## Отчёты

[`reports/`](reports/) — baseline-poultry-run, phase2, phase3, final-run, apk-corpus

## KPI

[`docs/scenarios/poultry-teo.yaml`](../../scenarios/poultry-teo.yaml) + [`registry.yaml`](registry.yaml)

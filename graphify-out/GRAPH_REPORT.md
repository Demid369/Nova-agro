# Graph Report - /workspace  (2026-06-24)

## Corpus Check
- Стартовый граф из сводки ТЭО. Для полного графа: /graphify docs/graphify-corpus

## Summary
- 29 nodes · 32 edges · 5 communities
- Extraction: 78% EXTRACTED · 22% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]

## God Nodes (most connected - your core abstractions)
1. `ООО «МОЯ МЕЧТА»` - 10 edges
2. `Животноводство КРС/МРС` - 7 edges
3. `Инвестиции 100 млрд руб.` - 6 edges
4. `Халяльный желатин 6 000 т` - 4 edges
5. `Переработка кожи 600 000 м²` - 3 edges
6. `Экспорт 10,2 млрд руб.` - 3 edges
7. `Выручка 71,4 млрд руб./год` - 2 edges
8. `Нулевая себестоимость мяса` - 2 edges
9. `Кролиководство 7 000 т/год` - 2 edges
10. `Рыбоводство белуга` - 2 edges

## Surprising Connections (you probably didn't know these)
- `ООО «МОЯ МЕЧТА»` --conceptually_related_to--> `Рыбоводство белуга`  [EXTRACTED]
  docs/graphify-corpus/00-summary.md → docs/graphify-corpus/03-proizvodstvo-i-tehnologii.md
- `ООО «МОЯ МЕЧТА»` --conceptually_related_to--> `Масложировой комбинат`  [EXTRACTED]
  docs/graphify-corpus/00-summary.md → docs/graphify-corpus/03-proizvodstvo-i-tehnologii.md
- `Переработка кожи 600 000 м²` --conceptually_related_to--> `Экспорт 10,2 млрд руб.`  [INFERRED]
  docs/graphify-corpus/03-proizvodstvo-i-tehnologii.md → docs/graphify-corpus/00-summary.md
- `ООО «МОЯ МЕЧТА»` --conceptually_related_to--> `Тепличный комплекс 100 га`  [EXTRACTED]
  docs/graphify-corpus/00-summary.md → docs/graphify-corpus/03-proizvodstvo-i-tehnologii.md
- `ООО «МОЯ МЕЧТА»` --conceptually_related_to--> `Животноводство КРС/МРС`  [EXTRACTED]
  docs/graphify-corpus/00-summary.md → docs/graphify-corpus/03-proizvodstvo-i-tehnologii.md

## Import Cycles
- None detected.

## Communities (5 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.29
Nodes (7): Биогазовая установка 20 МВт·ч, Комбикормовый завод, Животноводство КРС/МРС, Масложировой комбинат, Солнечные панели 50 МВт·ч, AIA Associazione Italiana Allevatori, SINT Technologies

### Community 1 - "Community 1"
Cohesion: 0.29
Nodes (7): Тепличный комплекс 100 га, Кролиководство 7 000 т/год, 5000 рабочих мест, Херсонская область, Земельный фонд 135 000 га, ООО «МОЯ МЕЧТА», Meneghin Srl

### Community 2 - "Community 2"
Cohesion: 0.33
Nodes (6): NPV рыбоводство 3,86 млрд, NPV теплицы 33,86 млрд, NPV животноводство 28,92 млрд, NPV масложировой 26,83 млрд, NPV кролиководство 2,78 млрд, Инвестиции 100 млрд руб.

### Community 3 - "Community 3"
Cohesion: 0.40
Nodes (5): Сертификат Халяль, Халяльный желатин 6 000 т, Переработка кожи 600 000 м², Нулевая себестоимость мяса, HOCEVAR

### Community 4 - "Community 4"
Cohesion: 0.50
Nodes (4): Экспорт 10,2 млрд руб., Чёрная икра 20 т/год, Рыбоводство белуга, Выручка 71,4 млрд руб./год

## Knowledge Gaps
- **15 isolated node(s):** `Херсонская область`, `5000 рабочих мест`, `Земельный фонд 135 000 га`, `Тепличный комплекс 100 га`, `Солнечные панели 50 МВт·ч` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ООО «МОЯ МЕЧТА»` connect `Community 1` to `Community 0`, `Community 2`, `Community 4`?**
  _High betweenness centrality (0.728) - this node is a cross-community bridge._
- **Why does `Животноводство КРС/МРС` connect `Community 0` to `Community 1`, `Community 3`?**
  _High betweenness centrality (0.522) - this node is a cross-community bridge._
- **Why does `Инвестиции 100 млрд руб.` connect `Community 2` to `Community 1`?**
  _High betweenness centrality (0.331) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Переработка кожи 600 000 м²` (e.g. with `Экспорт 10,2 млрд руб.` and `Нулевая себестоимость мяса`) actually correct?**
  _`Переработка кожи 600 000 м²` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Херсонская область`, `5000 рабочих мест`, `Земельный фонд 135 000 га` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._
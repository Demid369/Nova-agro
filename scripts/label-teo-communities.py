#!/usr/bin/env python3
"""Именование сообществ графа ТЭО по доменным эвристикам (без LLM API)."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"
GRAPH = OUT / "graph.json"
EXTRACTION = OUT / "extraction-merged.json"
LABELS_FILE = OUT / ".graphify_labels.json"
MIN_SIZE = 3

THEME_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"моя мечта|сводка проекта|ядро|ооо", re.I), "Ядро проекта «МОЯ МЕЧТА»"),
    (re.compile(r"нулев\w+ себестоимост|бесплатн\w+ убой|побочн\w+ продукт", re.I), "Модель нулевой себестоимости мяса"),
    (re.compile(r"животновод|крс|мрс|говяд|телят|ягнят|племен", re.I), "Животноводство КРС/МРС"),
    (re.compile(r"кролик", re.I), "Кролиководство"),
    (re.compile(r"белуг|икр|осетр|рыбовод", re.I), "Рыбоводство и икра"),
    (re.compile(r"молок|молоч|сыр|кефир|творог|сливк|йогурт", re.I), "Молочная переработка"),
    (re.compile(r"кож|дублен|заготовк\w+ шкур", re.I), "Кожевенное производство"),
    (re.compile(r"желатин|коллаген", re.I), "Халяльный желатин"),
    (re.compile(r"теплиц|гидропон|овощ|огурц|томат|цвет", re.I), "Теплицы и овощеводство"),
    (re.compile(r"масл|маргарин|подсолнеч|соя|шрот", re.I), "Масложировой комплекс"),
    (re.compile(r"комбикорм|корм|рацион", re.I), "Кормовая база"),
    (re.compile(r"биогаз|солнечн|энерг|мвт|электр", re.I), "Зелёная энергия"),
    (re.compile(r"экспорт|импорт|снг|халяль|араб|маркетинг|сбыт", re.I), "Рынок и экспорт"),
    (re.compile(r"риск|неопределенност", re.I), "Риски и меры"),
    (re.compile(r"npv|irr|инвест|выручк|окупаем|финанс|бюджет", re.I), "Финансы и KPI"),
    (re.compile(r"херсон|земл|га|заповедник", re.I), "Земля и локация"),
    (re.compile(r"aia|meneghin|sint|hocevar|итальян", re.I), "Технологии и поставщики"),
    (re.compile(r"кьянина|маркиджиана|лимузин|фризон|меринос|суффолк|дорпер", re.I), "Породы скота"),
    (re.compile(r"меморандум|введение|резюме|цель проекта", re.I), "Введение и стратегия"),
    (re.compile(r"аквакульт|ras|мальк", re.I), "Аквакультура RAS"),
    (re.compile(r"миров\w+ рынок|faostat|usda|businesstat", re.I), "Мировая рыночная аналитика"),
    (re.compile(r"^\d+[\d\s,.]*(?:млн|тыс|us\$|доллар)", re.I), "Статистика (шум)"),
    (re.compile(r"us\$|долларов\)", re.I), "Торговая статистика"),
]


def theme_for_text(text: str) -> str | None:
    for pat, name in THEME_RULES:
        if pat.search(text):
            return name
    return None


def label_community(node_labels: list[str], size: int) -> str:
    scores: Counter[str] = Counter()
    for lbl in node_labels:
        t = theme_for_text(lbl)
        if t:
            scores[t] += 3 if len(lbl) < 80 else 1
    if scores:
        return scores.most_common(1)[0][0]
    # fallback: shortest meaningful label
    candidates = [l for l in node_labels if 8 <= len(l) <= 70 and not re.match(r"^[\d\s,.]+$", l)]
    if candidates:
        candidates.sort(key=len)
        return candidates[0][:50]
    return f"Прочее ({size})"


def main() -> int:
    data = json.loads(GRAPH.read_text(encoding="utf-8"))
    nodes = data["nodes"]
    deg = Counter()
    for e in data.get("edges", []):
        deg[e["source"]] += 1
        deg[e["target"]] += 1

    by_c: dict[int, list[dict]] = defaultdict(list)
    for n in nodes:
        by_c[int(n.get("community", -1))].append(n)

    labels: dict[int, str] = {}
    used_names: Counter[str] = Counter()

    for cid, members in sorted(by_c.items()):
        if len(members) < MIN_SIZE:
            labels[cid] = f"Community {cid}"
            continue
        top = sorted(members, key=lambda x: deg.get(x["id"], 0), reverse=True)[:12]
        lbls = [n["label"] for n in top]
        name = label_community(lbls, len(members))
        if used_names[name]:
            name = f"{name} #{cid}"
        used_names[name] += 1
        labels[cid] = name

    LABELS_FILE.write_text(
        json.dumps({str(k): v for k, v in labels.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for n in nodes:
        cid = int(n.get("community", -1))
        n["community_name"] = labels.get(cid, f"Community {cid}")

    GRAPH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    # regenerate report
    from graphify.build import build_from_json
    from graphify.cluster import score_all
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
    from graphify.report import generate
    from graphify.export import to_html

    extraction = json.loads(EXTRACTION.read_text(encoding="utf-8"))
    G = build_from_json(extraction, root=ROOT)
    communities = {int(n["community"]): [] for n in nodes if "community" in n}
    for n in nodes:
        communities.setdefault(int(n["community"]), []).append(n["id"])
    cohesion = score_all(G, communities)
    gods = god_nodes(G)
    surprises = surprising_connections(G, communities)
    questions = suggest_questions(G, communities, labels)

    report = generate(
        G,
        communities,
        cohesion,
        labels,
        gods,
        surprises,
        {
            "total_files": 146,
            "total_words": 166762,
            "warning": "Структурный + семантический граф ТЭО с именованными сообществами",
        },
        {"input": 0, "output": 0},
        str(ROOT),
        suggested_questions=questions,
        min_community_size=MIN_SIZE,
    )
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    to_html(G, communities, str(OUT / "graph.html"), community_labels=labels)

    named = sum(1 for v in labels.values() if not v.startswith("Community "))
    print(f"Labeled {named}/{len(labels)} communities (size>={MIN_SIZE})")
    print("Top communities:")
    for cid, sz in sorted(((c, len(m)) for c, m in by_c.items()), key=lambda x: -x[1])[:15]:
        print(f"  C{cid:3d} ({sz:3d}): {labels.get(cid)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""End-to-end system test for TEO RAG (graph + vector + validation + memory)."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import yaml
except ImportError:
    print("FAIL: pip install pyyaml")
    raise SystemExit(1)

from teo_rag.config import BM25_INDEX_PATH, CHROMA_DIR, GRAPH_PATH, KPI_PATH, MANIFEST_PATH  # noqa: E402
from teo_rag.context import EvidenceBundle  # noqa: E402
from teo_rag.graph_client import run_graph_query  # noqa: E402
from teo_rag.kpi import format_kpi_answer, load_kpi  # noqa: E402
from teo_rag.memory import find_memory_hit, save_memory  # noqa: E402
from teo_rag.retrieval import get_collection, hierarchical_search  # noqa: E402
from teo_rag.router import classify_query  # noqa: E402
from teo_rag.scenarios import compare_scenarios, list_scenarios, resolve_scenario_compare  # noqa: E402
from teo_rag.synthesis import extractive_synthesize  # noqa: E402
from teo_rag.validator import validate_answer  # noqa: E402

PASS = 0
FAIL = 0


def ok(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK  {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL  {name}" + (f" — {detail}" if detail else ""))


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def run_validator_tests() -> None:
    section("Validator unit tests")
    spec = importlib.util.spec_from_file_location("tv", ROOT / "tests" / "test_validator.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for fn in (
        "test_normalize_grouped_number",
        "test_extract_significant_numbers",
        "test_validate_supported_numbers",
        "test_validate_rejects_hallucinated",
        "test_validate_empty_corpus_non_strict",
    ):
        try:
            getattr(mod, fn)()
            ok(fn, True)
        except Exception as exc:
            ok(fn, False, str(exc))

    vr = validate_answer(
        "Проект в Херсонской области с инвестициями 100 млрд",
        "инвестиции 100 млрд Херсонская область",
        check_claims=True,
    )
    ok("claims supported", vr.valid)
    vr_bad = validate_answer(
        "Проект построен на Луне с бюджетом 999 999 999 млрд",
        "инвестиции 100 млрд Херсонская область",
        check_claims=True,
    )
    ok("claims reject hallucination", not vr_bad.valid)


def run_infrastructure_checks() -> None:
    section("Infrastructure")
    ok("graph.json exists", GRAPH_PATH.exists(), str(GRAPH_PATH))
    ok("manifest exists", MANIFEST_PATH.exists())
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        ok("manifest chunk_count > 0", manifest.get("chunk_count", 0) > 0, str(manifest.get("chunk_count")))
    ok("chroma dir exists", CHROMA_DIR.exists())
    try:
        col = get_collection()
        ok("chroma collection non-empty", col.count() > 0, f"count={col.count()}")
    except Exception as exc:
        ok("chroma collection non-empty", False, str(exc))
    ok("graphify CLI", shutil.which("graphify") is not None)


def run_router_tests(data: dict) -> None:
    section("Router")
    queries = data["queries"]
    matched = sum(1 for q in queries if classify_query(q["query"]).mode == q["expected_mode"])
    ok(f"router accuracy", matched == len(queries), f"{matched}/{len(queries)}")


def run_retrieval_tests(data: dict) -> None:
    section("Vector retrieval + synthesis")
    for q in data["queries"]:
        if q["expected_mode"] not in ("vector", "summary", "hybrid"):
            continue
        if "expect_contains" not in q:
            continue
        hits = hierarchical_search(q["query"], mode=q["expected_mode"])
        ok(f"{q['id']} retrieval non-empty", len(hits) > 0)
        bundle = EvidenceBundle(query=q["query"], chunks=hits)
        syn = extractive_synthesize(bundle)
        vr = validate_answer(syn.answer, bundle.corpus_text(), check_claims=True)
        ok(f"{q['id']} synthesis validates", vr.valid)
        merged_text = syn.answer + "\n" + "\n".join(h.text for h in hits)
        for needle in q.get("expect_contains", []):
            ok(
                f"{q['id']} contains '{needle}'",
                needle.lower() in merged_text.lower(),
                syn.answer[:80],
            )


def run_graph_tests() -> None:
    section("Graph layer")
    result = run_graph_query("нулевая себестоимость мяса желатин", budget=1500)
    ok("graph returns nodes", len(result.nodes) > 0, f"nodes={len(result.nodes)}")
    labels = " ".join(n.label.lower() for n in result.nodes)
    ok("graph finds meat/gelatin cluster", "желатин" in labels or "мяс" in labels or "убой" in labels)
    noise = "связано это" in labels
    ok("graph avoids 'Связано это' hub", not noise)


def run_cli_smoke() -> None:
    section("CLI smoke")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "teo-query.py"), "NPV теплиц", "--mode", "vector", "--synthesize", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    ok("teo-query exit 0", proc.returncode == 0, proc.stderr[-200:] if proc.returncode else "")
    if proc.returncode == 0:
        payload = json.loads(proc.stdout)
        ok("cli validation valid", payload.get("validation", {}).get("valid") is True)
        ok("cli answer has NPV", "33 861 691" in payload.get("answer", ""))


def run_memory_roundtrip() -> None:
    section("Memory")
    with tempfile.TemporaryDirectory() as tmp:
        mem_path = Path(tmp) / "memory.jsonl"
        from teo_rag import memory as memmod

        old = memmod.MEMORY_PATH
        memmod.MEMORY_PATH = mem_path
        try:
            save_memory(
                query="тестовый уникальный запрос e2e xyz",
                answer="ответ e2e",
                mode="vector",
                citations=[],
                validated=True,
            )
            hit = find_memory_hit("тестовый уникальный запрос e2e xyz")
            ok("memory roundtrip", hit is not None and hit.answer == "ответ e2e")
        finally:
            memmod.MEMORY_PATH = old


def run_kpi_tests() -> None:
    section("KPI layer")
    store = load_kpi()
    ok("kpi store has blocks", len(store.blocks) > 0, f"blocks={len(store.blocks)}")
    ok("kpi file or build", KPI_PATH.exists() or len(store.blocks) > 0)
    hit = format_kpi_answer("NPV теплиц", store)
    ok("kpi NPV теплиц", hit is not None)
    if hit:
        ok("kpi NPV value", "33 861 691" in hit[0] or "33861691" in hit[0].replace(" ", ""))


def run_bm25_tests() -> None:
    section("BM25 hybrid")
    try:
        from teo_rag.bm25_index import bm25_search

        hits = bm25_search("NPV теплиц", top_k=5)
        ok("bm25 returns hits", len(hits) > 0, f"count={len(hits)}")
        ok("bm25 cache path parent", BM25_INDEX_PATH.parent.exists())
    except ImportError as exc:
        ok("rank_bm25 installed", False, str(exc))


def run_scenario_tests() -> None:
    section("Scenarios what-if")
    ids = list_scenarios()
    ok("scenarios listed", "baseline" in ids and "poultry-variant" in ids, str(ids))
    pair = resolve_scenario_compare("сценарий замена кроликов на птицеводство")
    ok("scenario resolve", pair == ("baseline", "poultry-variant"))
    report = compare_scenarios("baseline", "poultry-variant")
    ok("scenario compare", "птицеводство" in report.lower() and "кролик" in report.lower())
    ok("router scenario mode", classify_query("what-if птица вместо кроликов").mode == "scenario")


def run_kpi_cli_smoke() -> None:
    section("KPI CLI fast path")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "teo-query.py"), "NPV теплиц", "--mode", "vector", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    ok("kpi cli exit 0", proc.returncode == 0, proc.stderr[-200:] if proc.returncode else "")
    if proc.returncode == 0:
        payload = json.loads(proc.stdout)
        ok("kpi cli mode", payload.get("mode") == "kpi")
        ok("kpi cli answer", "33 861 691" in payload.get("answer", ""))


def run_llm_fallback() -> None:
    section("LLM fallback")
    from teo_rag.synthesis import llm_synthesize

    bundle = EvidenceBundle(
        query="NPV теплиц",
        chunks=hierarchical_search("NPV теплиц", mode="vector")[:3],
    )
    result = llm_synthesize(bundle)
    ok("llm fallback returns answer", len(result.answer) > 20)
    ok("llm fallback method", result.method in ("extractive", "llm"))


def main() -> int:
    print("TEO RAG System Test")
    print(f"ROOT: {ROOT}")
    data = yaml.safe_load((ROOT / "tests" / "teo-queries.yaml").read_text(encoding="utf-8"))

    run_infrastructure_checks()
    run_validator_tests()
    run_router_tests(data)
    run_graph_tests()
    run_retrieval_tests(data)
    run_kpi_tests()
    run_bm25_tests()
    run_scenario_tests()
    run_cli_smoke()
    run_kpi_cli_smoke()
    run_memory_roundtrip()
    run_llm_fallback()

    print(f"\n{'='*40}")
    print(f"PASSED: {PASS}  FAILED: {FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

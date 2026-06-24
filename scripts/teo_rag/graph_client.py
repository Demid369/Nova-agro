"""Thin wrapper around graphify CLI."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field

from .config import ROOT, resolve_graph_path


@dataclass
class GraphNode:
    label: str
    source: str
    community: str | None = None


@dataclass
class GraphEdge:
    source: str
    relation: str
    target: str


@dataclass
class GraphResult:
    raw: str
    traversal: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


NODE_RE = re.compile(
    r"^NODE (.+?) \[src=([^\s]+)(?:\s+loc=\S+)?(?:\s+community=([^\]]+))?\]",
    re.M,
)
EDGE_RE = re.compile(r"^EDGE (.+?) --(.+?) \[.+?\]--> (.+)$", re.M)
TRAVERSAL_RE = re.compile(r"^Traversal: (.+)$", re.M)


def _graphify_bin() -> str:
    return shutil.which("graphify") or "graphify"


def run_graph_query(query: str, budget: int = 2500) -> GraphResult:
    graph_path = resolve_graph_path()
    cmd = [_graphify_bin(), "query", query, "--budget", str(budget)]
    if graph_path.name != "graph.json":
        cmd.extend(["--graph", str(graph_path)])
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    raw = proc.stdout.strip() or proc.stderr.strip()
    return parse_graph_output(raw)


def run_graph_path(source: str, target: str) -> GraphResult:
    graph_path = resolve_graph_path()
    cmd = [_graphify_bin(), "path", source, target]
    if graph_path.name != "graph.json":
        cmd.extend(["--graph", str(graph_path)])
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    raw = proc.stdout.strip() or proc.stderr.strip()
    return parse_graph_output(raw)


def parse_graph_output(raw: str) -> GraphResult:
    traversal_m = TRAVERSAL_RE.search(raw)
    traversal = traversal_m.group(1) if traversal_m else ""
    nodes = [
        GraphNode(label=m.group(1), source=m.group(2), community=m.group(3))
        for m in NODE_RE.finditer(raw)
    ]
    edges = [
        GraphEdge(source=m.group(1), relation=m.group(2), target=m.group(3))
        for m in EDGE_RE.finditer(raw)
    ]
    return GraphResult(raw=raw, traversal=traversal, nodes=nodes, edges=edges)

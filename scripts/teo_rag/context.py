"""Build evidence corpus from retrieved chunks and graph results."""

from __future__ import annotations

from dataclasses import dataclass, field

from .graph_client import GraphResult
from .retrieval import RetrievedChunk


@dataclass
class EvidenceBundle:
    query: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    graph: GraphResult | None = None

    def corpus_text(self) -> str:
        parts: list[str] = []
        for hit in self.chunks:
            parts.append(f"[{hit.source} :: {hit.section}]\n{hit.text}")
        if self.graph:
            for node in self.graph.nodes:
                parts.append(f"[graph :: {node.source}] {node.label}")
            for edge in self.graph.edges:
                parts.append(
                    f"[graph] {edge.source} --{edge.relation}--> {edge.target}"
                )
        return "\n\n".join(parts)

    def graph_node_labels(self) -> list[str]:
        if not self.graph:
            return []
        return [n.label for n in self.graph.nodes[:12]]

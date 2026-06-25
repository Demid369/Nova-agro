## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering questions about ТЭО or project architecture, run `graphify query "<question>"` or read `graphify-out/GRAPH_REPORT.md`
- Corpus for full rebuild: `docs/graphify-corpus/`
- Source docx (66 MB) is excluded — use markdown corpus instead
- After editing corpus files, run `graphify extract docs/graphify-corpus --update` or `/graphify docs/graphify-corpus --update` in Cursor
- Pinned CLI version: `graphifyy==0.8.49` (see README.md) — install/update with this exact version, don't rely on "latest"
- `graphify-out/graph.json` has a merge driver declared in `.gitattributes`. One-time local setup per clone:
  ```bash
  git config merge.graphify.name "graphify graph.json union merge"
  git config merge.graphify.driver "graphify merge-driver %O %A %B"
  ```

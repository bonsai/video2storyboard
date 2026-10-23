# Standards MAP

This folder contains canonical design rules for `video2storyboard`.

- [Architecture Policy](architecture-policy.md) — proposed MCP-first Python plugin-service architecture: MCP tools, OpenAPI contracts, LangGraph orchestration, Docker-optional local execution, and runtime visualization.
- [Design Principles](design-principles.md) — 15 architecture and engineering principles; currently Draft.
- [Plugin Catalog](plugin-catalog.yaml) — proposed 16-plugin catalog, grouped into four domains, including responsibilities and I/O contracts.
- [Plugin 16: slot](plugins/slot.md) — layout-slot definitions and deterministic assignments; design proposal only.

## Authority

These files are the design source of truth for review. The catalog is **proposed**, not a statement that every plugin exists or is implemented. The architecture policy is also a proposal until reviewed and accepted. Update the canonical documents through reviewable commits and keep implementation aligned with accepted contracts.

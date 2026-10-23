# Canon: MCP-First Plugin Service Architecture Policy

- **Status:** Proposed policy for review
- **Version:** 0.1.0
- **Scope:** `bonsai/video2storyboard`
- **Related issue:** [#12 — MCP-first Python plugin services, OpenAPI, LangGraph, and visualization](https://github.com/bonsai/video2storyboard/issues/12)

## Mission

Build a locally runnable, observable video-to-storyboard factory in which each plugin has an independent service boundary, AI agents can invoke capabilities through MCP, HTTP interoperability is described by OpenAPI, and LangGraph coordinates the end-to-end workflow. Docker is optional and must not be a prerequisite for development or local execution.

## Architecture rules

1. **One plugin, one responsibility, one contract.** Every plugin declares its ID, purpose, inputs, outputs, errors, dependencies, version, and operational status.
2. **Python-first service implementation.** Plugin logic is implemented in Python and can be started, tested, and used without Docker. Services may run as separate local processes; packaging and deployment must not be coupled to containers.
3. **MCP is the agent-facing tool interface.** Each plugin capability must be exposable as a documented MCP tool through a Python MCP server. A shared server may host multiple plugin tools when operationally useful, provided plugin boundaries and contracts remain independent and discoverable.
4. **OpenAPI is the HTTP contract.** Where a plugin exposes HTTP endpoints, publish and validate an OpenAPI document. MCP and HTTP adapters call the same core implementation; do not duplicate business logic.
5. **LangGraph owns orchestration.** Ordering, parallel branches, joins, conditional routing, bounded retries, checkpoints, timeouts, and workflow-level error handling belong to the graph/orchestrator, not to individual plugins.
6. **YAML configures the factory.** Use versioned YAML manifests for plugin registry, service launch/configuration, workflow composition, dependencies, and visualization metadata. Keep secrets out of committed files; inject them through environment or an appropriate secret store.
7. **JSON is the canonical data contract; JSONL is the event log.** Version storyboard, job, plugin I/O, and artifact-manifest schemas. Append run lifecycle and plugin events to JSONL.
8. **One canonical storyboard.** HTML, SVG, thumbnails, and other exports are derived views/artifacts, not competing sources of truth.
9. **Observable by design.** Every run and plugin invocation carries `run_id`, `plugin_id`, `contract_version`, status, timestamps, duration, and structured error details where applicable. Record events without leaking credentials or sensitive media content.
10. **Visualize actual runtime state.** Dashboard status and workflow diagrams must be generated from the real plugin registry, LangGraph definition, and run events—not maintained as a disconnected illustration.
11. **Docker is an optional adapter.** Local Python execution is the default development path. Container-based deployment may be documented as an optional later mode, never as the service boundary itself.
12. **Local-first and explicit privacy.** Do not upload source media or invoke cloud inference automatically. Any remote execution must be explicit, opt-in, and visible in configuration and run records.
13. **Fail explicitly and preserve partial results.** Distinguish `success`, `partial`, `skipped`, and `failed`; validate inputs and output paths; report unavailable services and dependency errors; never silently convert a failure into success.
14. **Trace and safely rerun.** Preserve source IDs, source-media timestamps, hashes/config fingerprints, plugin/provider versions, and artifact paths. Never overwrite source media.
15. **Test contracts before full runs.** Each plugin has isolated contract tests; service adapters have MCP/HTTP tests; the graph has routing/failure tests; the complete pipeline is verified with a small synthetic video before private media.
16. **Incremental delivery.** Mark every catalog entry as `proposed`, `scaffolded`, or `implemented`. A catalog entry is not evidence that a working service exists.

## Responsibility boundaries

| Layer | Owns | Must not own |
|---|---|---|
| Plugin core | One capability; validated inputs/outputs; structured result | Workflow-wide routing or unrelated plugin state |
| Python service host | Process startup, configuration, health/readiness, lifecycle | Duplicate plugin business logic |
| MCP adapter | Agent-facing tool schema and invocation | Independent implementation of plugin logic |
| HTTP/OpenAPI adapter | HTTP routes, schemas, API documentation | A second copy of plugin logic |
| LangGraph | Sequence, branches, joins, retries, checkpoints, run state | Plugin-specific analysis implementation |
| YAML registry/config | Declared plugin/service/workflow settings | Runtime claims unsupported by observed status |
| JSON/JSONL | Canonical artifacts/contracts and append-only events | Secrets or huge embedded media blobs |
| Dashboard | Runtime status, graph progress, durations, failures, artifacts | A separately maintained fake status model |

## Required plugin service manifest

Each plugin entry should declare at minimum:

- `id`, `responsibility`, `status`, `contract_version`
- `inputs`, `outputs`, `errors`, `optional_dependencies`
- `mcp`: tool names and input/output schema references
- `http`: enabled flag and OpenAPI operation/schema references, when applicable
- `runtime`: Python module/entry point, launch method, health check, timeout
- `observability`: event types and artifact references

Keep manifests declarative and validate them. Do not hard-code service URLs, credentials, or machine-specific paths into the canonical catalog.

## Dashboard requirements

The dashboard must show:

- Plugin registry and implementation status
- Service health/availability and interface (MCP/HTTP)
- Actual LangGraph stages, edges, active stage, and branch/join outcomes
- Per-run and per-plugin status, duration, retries, and structured errors
- Artifact links for canonical JSON, HTML, SVG, frames, and manifests
- Source/run provenance and whether execution is local or explicitly remote

A generated SVG architecture map may complement the interactive dashboard, but must be derived from canonical registry/graph data.

## Delivery sequence

1. Inventory current code, graph nodes, MCP server, APIs, and generated artifacts.
2. Align the 16-plugin catalog with actual implementation status and existing graph nodes.
3. Define YAML service manifests and versioned JSON contracts.
4. Implement one vertical slice: Python plugin core → MCP adapter → optional OpenAPI endpoint → LangGraph invocation → JSONL events → dashboard.
5. Prove local startup without Docker and verify with synthetic media.
6. Extend the pattern to remaining plugins; add parallelism only where inputs and resource constraints allow it.
7. Document optional container deployment separately, if needed.

## Acceptance checklist

- [ ] Local Python startup and tests work without Docker.
- [ ] Each plugin has an independent, versioned contract and accurate status.
- [ ] MCP calls and HTTP calls share the same core implementation.
- [ ] OpenAPI documents validate for HTTP-enabled services.
- [ ] LangGraph is the sole workflow orchestrator.
- [ ] Dashboard reflects real registry, graph, and JSONL events.
- [ ] Structured errors, timeouts, retries, and partial results are observable.
- [ ] Synthetic end-to-end run produces validated storyboard JSON and reviewable HTML/SVG.
- [ ] No unrequested media upload, cloud fallback, or secrets in logs/artifacts.

## Change control

This policy is a proposal until reviewed and accepted. Make changes through reviewable GitHub commits and keep the design status distinct from implementation status.
